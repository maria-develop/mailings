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

from users.models import User

from mailings.models import Mailing, Message, Recipient, MailingAttempt, MailingForm, MessageForm, Parent
# from django.db import models
from mailings.forms import MailingForm, ParentForm, MailingManagerForm, MailingAttemptManagerForm, RecipientForm
from mailings.services import get_mailings_from_cache, get_recipient_from_cache

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
        # return redirect('/')  # Перенаправление на главную страницу или другую нужную страницу


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
    # success_url = reverse_lazy('mailings:mailing_list')
    # template_name = 'mailings/mailing_detail.html'
    # context_object_name = 'mailing'

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

    def get_queryset(self):
        user = self.request.user
        # Разрешить менеджерам просматривать всех получателей
        if user.is_staff or user.has_perm('users.view_all_recipients'):
            return get_recipient_from_cache()
        else:
            return Recipient.objects.filter(owner=user)


class RecipientDetailView(LoginRequiredMixin, DetailView):
    """Просмотр одного клиента"""
    model = Recipient


class RecipientCreateView(LoginRequiredMixin, CreateView):
    """Создание клиента"""
    model = Recipient
    form_class = RecipientForm
    success_url = reverse_lazy('mailings:recipient_list')

    def form_valid(self, form):
        recipient = form.save()
        user = self.request.user
        recipient.owner = user
        recipient.save()
        return super().form_valid(form)


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
        mailing_id = kwargs.get('mailing_id')
        mailing_to_disable = get_object_or_404(Mailing, pk=mailing_id)

        # Логика отключения рассылки
        mailing_to_disable.is_active = False
        mailing_to_disable.save()
        messages.success(request, f"Рассылка '{mailing_to_disable.message.subject}' была успешно отключена.")
        return HttpResponseRedirect(reverse('mailings:mailing_list'))


class BlockUserView(LoginRequiredMixin, View):
    def post(self, request, pk):
        user_to_block = get_object_or_404(User, id=pk)

        if not request.user.has_perm('mailings.blocking_users'):
            return HttpResponseForbidden("У вас нет прав для блокировки пользователя.")

        # Логика блокировки пользователя
        user_to_block.is_active = False
        user_to_block.save()

        return redirect('users:user_list')


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
