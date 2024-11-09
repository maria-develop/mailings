from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.views import View
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.forms import inlineformset_factory
from django.contrib import messages
from django.core.mail import send_mail
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect, HttpResponseForbidden
import uuid
from django.db import migrations, models

from users.models import User

from mailings.models import Mailing, Message, Recipient, MailingAttempt, Parent
# from django.db import models
from mailings.forms import MailingForm, ParentForm, MailingAttemptManagerForm, RecipientForm, MessageForm
from mailings.services import get_mailings_from_cache, get_recipient_from_cache, send_mailing_messages

import logging


# Просмотр списка рассылок
class MailingListView(ListView):
    model = Mailing
    form_class = MailingForm
    success_url = reverse_lazy('mailings:mailing_list')

    def get_queryset(self):
        return get_mailings_from_cache()


class MailingCreateView(CreateView, LoginRequiredMixin):
    model = Mailing
    # fields = ['start_time', 'end_time', 'status', 'message', 'recipients']
    form_class = MailingForm
    success_url = reverse_lazy('mailings:mailing_list')

    def form_valid(self, form):
        mailing = form.save()
        user = self.request.user
        mailing.owner = user
        mailing.save()
        return super().form_valid(form)

    # def test_func(self):
        # Проверка, активен ли пользователь
        # return self.request.user.is_active  # Возвращает False для заблокированных пользователей

    # def handle_no_permission(self):
        # Обработка для заблокированных пользователей
        # messages.error(self.request, "Ваш аккаунт заблокирован. Доступ к этой функции ограничен.")
        # return redirect('/')  # Перенаправление на главную страницу


# Редактирование существующей рассылки
class MailingUpdateView(UpdateView):
    model = Mailing
    form_class = MailingForm
    # template_name = 'mailing_form.html'
    # fields = ['start_time', 'end_time', 'status', 'message', 'recipients']
    success_url = reverse_lazy('mailings:mailing_list')

    def get_form_class(self):
        user = self.request.user
        if user == self.object.owner:
            return MailingForm
        elif user.has_perm('mailings:viewing_statistics'):
            return MailingAttemptManagerForm
        raise PermissionDenied

    def get_success_url(self):
        return reverse('mailings:mailing_detail', args=[self.kwargs.get('pk')])

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        MailingFormset = inlineformset_factory(Mailing, Parent, ParentForm, extra=1)
        if self.request.method == 'POST':
            context_data['formset'] = MailingFormset(self.request.POST, instance=self.object)
        else:
            context_data['formset'] = MailingFormset(instance=self.object)
        return context_data

    def form_valid(self, form):
        context_data = self.get_context_data()
        formset = context_data['formset']
        if form.is_valid() and formset.is_valid():
            self.object = form.save()
            formset.instance = self.object
            formset.save()
            return super().form_valid(form)
        else:
            return self.render_to_response(self.get_context_data(form=form, formset=formset))


# Удаление рассылки
class MailingDeleteView(DeleteView):
    model = Mailing
    # template_name = 'mailing_confirm_delete.html'
    success_url = reverse_lazy('mailings:mailing_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Рассылка удалена!')
        return super().delete(request, *args, **kwargs)

    def get_form_class(self):
        user = self.request.user
        if user == self.object.owner:
            return MailingForm
        elif user.has_perm('mailings:viewing_statistics'):
            return MailingAttemptManagerForm
        raise PermissionDenied


# Просмотр конкретной рассылки и ее деталей
class MailingDetailView(DetailView):
    model = Mailing
    context_object_name = 'mailing'
    template_name = 'mailings/mailing_detail.html'
    # success_url = reverse_lazy('mailings:mailing_list')

    def get(self, request, *args, **kwargs):
        # Проверяем, является ли пользователь владельцем или имеет право на просмотр статистики
        mailing = self.get_object()
        if request.user != mailing.owner and not request.user.has_perm('mailings.viewing_statistics'):
            raise PermissionDenied("У вас нет прав для просмотра этой рассылки.")
        return super().get(request, *args, **kwargs)


# Логгирование ошибок почтового сервера
logger = logging.getLogger(__name__)


# Отправка рассылки вручную
class MailingSendView(View):
    def get(self, request, pk, *args, **kwargs):
        mailing = get_object_or_404(Mailing, pk=pk)
        # Ограничение: проверка, что текущий пользователь является владельцем или имеет необходимые права
        if request.user != mailing.owner and not request.user.has_perm('mailings.viewing_statistics'):
            raise PermissionDenied("У вас нет прав для отправки этой рассылки.")

        return render(request, 'mailings/mailing_send.html', {'mailing': mailing})

    def post(self, request, pk, *args, **kwargs):
        mailing = get_object_or_404(Mailing, pk=pk)

        # Проверяем, что статус рассылки "Создана"
        if mailing.status == 'Создана':
            recipients = mailing.recipients.all()

            # Проходим по каждому получателю
            for recipient in recipients:
                try:
                    # Попытка отправки письма
                    send_mail(
                        subject=mailing.message.subject,
                        message=mailing.message.body,
                        from_email='moi066@mail.ru',
                        recipient_list=[recipient.email],
                    )
                    # Если письмо отправлено успешно, создаем запись в попытках
                    MailingAttempt.objects.create(
                        mailing=mailing,
                        status='Успешно',
                        server_response='Сообщение отправлено успешно',
                    )
                except Exception as e:
                    # Логгируем ошибку
                    logger.error(f'Ошибка отправки письма: {e}')

                    MailingAttempt.objects.create(
                        mailing=mailing,
                        status='Не успешно',
                        server_response=str(e),
                    )
            # Обновляем статус рассылки после завершения попыток отправки
            mailing.status = 'Запущена'
            mailing.save()
            messages.success(request, 'Рассылка отправлена!')
        else:
            messages.error(request, 'Эта рассылка уже была отправлена.')

        # return redirect('mailings:mailing_send', pk=pk)
        return redirect('mailings:mailing_report', pk=pk)


class MailingReportView(DetailView):
    model = Mailing
    template_name = 'mailings/mailing_report.html'
    context_object_name = 'mailing'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['successful_attempts'] = self.object.attempts.filter(status='Успешно').count()
        context['failed_attempts'] = self.object.attempts.filter(status='Не успешно').count()
        context['total_attempts'] = self.object.attempts.count()
        return context

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        # Ограничение: проверка, что текущий пользователь является владельцем или имеет нужные права
        if request.user != self.object.owner and not request.user.has_perm('mailings.viewing_statistics'):
            raise PermissionDenied("У вас нет прав для просмотра отчета этой рассылки.")

        return super().get(request, *args, **kwargs)


class RecipientUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование данных клиента"""
    model = Recipient
    form_class = RecipientForm
    success_url = reverse_lazy('mailings:recipient_list')

    def get_form_class(self):
        user = self.request.user
        if user == self.object.owner:
            return RecipientForm
        raise PermissionDenied


class RecipientListView(LoginRequiredMixin, ListView):
    """ Просмотр списка клиентов """
    model = Recipient
    form_class = RecipientForm
    context_object_name = 'object_list_recipient'

    # def get_queryset(self):
    #     user = self.request.user
        # Разрешить менеджерам просматривать всех получателей
        # if user.is_staff or user.has_perm('users.view_all_recipients'):
        #     return get_recipient_from_cache()
        # else:
        #     return Recipient.objects.filter(owner=user)

    def get_form_class(self):
        user = self.request.user
        if user == self.object.owner:
            return RecipientForm
        elif user.has_perm('mailings:view_all_recipients'):
            return RecipientForm
        raise PermissionDenied


class RecipientDetailView(LoginRequiredMixin, DetailView):
    """Просмотр одного клиента"""
    model = Recipient


class RecipientCreateView(LoginRequiredMixin, CreateView):
    """Создание клиента"""
    model = Recipient
    form_class = RecipientForm
    success_url = reverse_lazy('mailings:recipient_list')

    def form_valid(self, form):
        # Устанавливаем текущего пользователя в качестве владельца
        form.instance.owner = self.request.user
        return super().form_valid(form)

    # def form_valid(self, form):
    #     recipient = form.save()
    #     user = self.request.user
    #     recipient.owner = user
    #     recipient.save()
    #     return super().form_valid(form)


class RecipientDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление клиента"""
    model = Recipient
    success_url = reverse_lazy('mailings:recipient_list')

    def get_context_data(self, **kwargs):
        """
        Права доступа владельца.
        """
        context_data = super().get_context_data(**kwargs)
        user = self.request.user
        if user == self.object.owner:
            return context_data
        raise PermissionDenied


class DisableMailingView(PermissionRequiredMixin, View):
    permission_required = 'mailings.disabling_mailing'

    def post(self, request, *args, **kwargs):
        mailing_id = kwargs.get('start_time')
        mailing_to_disable = get_object_or_404(Mailing, pk=mailing_id)

        # Логика отключения рассылки
        mailing_to_disable.mail_active = False
        mailing_to_disable.save()
        messages.success(request, f"Рассылка '{mailing_to_disable.message.subject}' была успешно отключена.")
        return HttpResponseRedirect(reverse('mailings:mailing_list'))


class EnableMailingView(PermissionRequiredMixin, View):
    permission_required = 'mailings.disabling_mailing'

    def post(self, request, *args, **kwargs):
        mailing_id = kwargs.get('start_time')
        mailing_to_enable = get_object_or_404(Mailing, pk=mailing_id)

        # Логика включения рассылки
        mailing_to_enable.mail_active = True
        mailing_to_enable.save()

        # Отправить сообщение об успехе
        messages.success(request, f"Рассылка '{mailing_to_enable.message.subject}' была успешно включена.")
        return redirect('mailings:mailing_list')  # или  redirect('mailings:mailing_detail', pk=mailing_id)


class MailingAttemptListView(ListView):
    model = MailingAttempt
    success_url = reverse_lazy('mailings:mailing_list')

    def get_queryset(self):
        user = self.request.user

        # Проверка на суперпользователя или наличие специального разрешения
        if user.is_staff or user.has_perm('users.view_all_recipients'):
            # Возвращаем все попытки рассылок для пользователей с правами
            return MailingAttempt.objects.all()
        else:
            # Получаем рассылки, принадлежащие текущему пользователю
            user_mailings = Mailing.objects.filter(owner=user)
            # Возвращаем только попытки рассылок, относящиеся к этим рассылкам
            return MailingAttempt.objects.filter(mailing__in=user_mailings)
    # form = MailingForm
    # if form.is_valid():
    #     selected_recipients = form.cleaned_data['recipients']  # Получаем список объектов
    #     for recipient in selected_recipients:
    #         print(recipient.email)  # Получаем email из каждого объекта Recipient

    def post(self, request, *args, **kwargs):
        mailing_id = kwargs.get('pk')
        mailing = get_object_or_404(Mailing, pk=mailing_id)

        # Инициация отправки рассылки
        send_mailing_messages(mailing)

        # Отображаем сообщение об успешной отправке
        messages.success(request, f"Рассылка '{mailing.message.subject}' была успешно отправлена.")
        return redirect('mailings:mailing_list')


class HomePageView(TemplateView):
    template_name = 'mailings/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Количество всех рассылок
        context['total_mailings'] = Mailing.objects.count()

        # Количество активных рассылок (со статусом 'Запущена')
        context['active_mailings'] = Mailing.objects.filter(status='Запущена').count()

        # Количество уникальных получателей
        context['unique_recipients'] = Recipient.objects.distinct().count()

        return context


class MessageListView(LoginRequiredMixin, ListView):
    model = Message
    template_name = 'mailings/message_list.html'
    context_object_name = 'messages'

    def get_form_class(self):
        user = self.request.user
        if user == self.object.owner:
            return MessageForm
        elif user.has_perm('mailings:view_message'):
            return MessageForm
        raise PermissionDenied


class MessageDetailView(PermissionRequiredMixin, DetailView):
    model = Message
    template_name = 'mailings/message_detail.html'
    context_object_name = 'message'
    permission_required = 'mailings.view_message'

    def get_form_class(self):
        user = self.request.user
        if user == self.object.owner:
            return MessageForm
        elif user.has_perm('mailings:view_message'):
            return MessageForm
        raise PermissionDenied


class MessageCreateView(PermissionRequiredMixin, CreateView):
    model = Message
    template_name = 'mailings/message_form.html'
    fields = ['subject', 'body']
    permission_required = 'mailings.add_message'
    success_url = reverse_lazy('mailings:message_list')

    # def form_valid(self, form):
    #     message = form.save()
    #     user = self.request.user
    #     message.owner = user
    #     message.save()
    #     return super().form_valid(form)

    def form_valid(self, form):
        # Устанавливаем текущего пользователя в качестве владельца
        form.instance.owner = self.request.user
        return super().form_valid(form)


class MessageUpdateView(PermissionRequiredMixin, UpdateView):
    model = Message
    template_name = 'mailings/message_form.html'
    fields = ['subject', 'body']
    permission_required = 'mailings.view_message'
    success_url = reverse_lazy('mailings:message_list')

    def has_permission(self):
        # Проверяем, что пользователь либо имеет право на изменение, либо является владельцем
        return super().has_permission() or self.get_object().owner == self.request.user

    def get_form_class(self):
        user = self.request.user
        if self.get_object().owner == user or user.has_perm('mailings.change_message'):
            return MessageForm
        raise PermissionDenied

    # def get_form_class(self):
    #     user = self.request.user
    #     if user == self.object.owner:
    #         return MessageForm
    #     elif user.has_perm('mailings:view_message'):
    #         return PermissionDenied
    #     raise PermissionDenied


class MessageDeleteView(PermissionRequiredMixin, DeleteView):
    model = Message
    template_name = 'mailings/message_confirm_delete.html'
    permission_required = 'mailings.view_message'
    success_url = reverse_lazy('mailings:message_list')

    def has_permission(self):
        # Проверяем, что пользователь либо имеет право на удаление, либо является владельцем
        return super().has_permission() or self.get_object().owner == self.request.user
