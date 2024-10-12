from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.views import View
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.urls import reverse
from .models import Mailing, Message, Recipient, MailingAttempt, MailingForm, MessageForm
from django.contrib import messages
from django.core.mail import send_mail
from django.utils import timezone
import logging


# Просмотр списка рассылок
class MailingListView(ListView):
    model = Mailing
    # mailings = Mailing.objects.all()
    # template_name = 'mailing_list.html'
    # context_object_name = 'mailings'


class MailingCreateView(CreateView):
    model = Mailing
    fields = ['start_time', 'end_time', 'status', 'message', 'recipients']
    # form_class = MailingForm
    # template_name = 'mailings/mailing_create.html'
    success_url = reverse_lazy('mailings:mailing_list')

    def form_valid(self, form):
        messages.success(self.request, 'Рассылка создана!')
        return super().form_valid(form)


# Редактирование существующей рассылки
class MailingUpdateView(UpdateView):
    model = Mailing
    # form_class = MailingForm
    # template_name = 'mailing_form.html'
    fields = ['start_time', 'end_time', 'status', 'message', 'recipients']
    success_url = reverse_lazy('mailings:mailing_list')

    def form_valid(self, form):
        messages.success(self.request, 'Рассылка обновлена!')
        return super().form_valid(form)


# Удаление рассылки
class MailingDeleteView(DeleteView):
    model = Mailing
    # template_name = 'mailing_confirm_delete.html'
    success_url = reverse_lazy('mailings:mailing_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Рассылка удалена!')
        return super().delete(request, *args, **kwargs)


# Просмотр конкретной рассылки и ее деталей
class MailingDetailView(DetailView):
    model = Mailing
    # success_url = reverse_lazy('mailings:mailing_list')
    # template_name = 'mailings/mailing_detail.html'
    # context_object_name = 'mailing'


# Логгирование ошибок почтового сервера
logger = logging.getLogger(__name__)


# Отправка рассылки вручную
class MailingSendView(View):
    def get(self, request, pk, *args, **kwargs):
        mailing = get_object_or_404(Mailing, pk=pk)
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
