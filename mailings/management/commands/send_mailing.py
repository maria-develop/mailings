import os

from django.core.management.base import BaseCommand, CommandError
from django.core.mail import send_mail
from mailings.models import Mailing, MailingAttempt
from django.utils import timezone
import logging
from dotenv import load_dotenv

# Загружаем переменные окружения из файла .env
load_dotenv(override=True)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Отправляет рассылку с указанным Идентификатором'

    def add_arguments(self, parser):
        parser.add_argument('start_time', type=str, help="Идентификатор рассылки, которую нужно отправить")

    def handle(self, *args, **kwargs):
        mailing_id = kwargs['start_time']

        try:
            mailing = Mailing.objects.get(id=mailing_id)

            # Проверка статуса рассылки
            if mailing.status != 'Создана':
                self.stdout.write(
                    self.style.WARNING(f"Рассылка с Идентификатором {mailing_id} уже отправлена или не может быть отправлена."))
                return

            recipients = mailing.recipients.all()
            for recipient in recipients:
                try:
                    send_mail(
                        subject=mailing.message.subject,
                        message=mailing.message.body,
                        from_email=os.getenv('EMAIL_HOST_USER'),
                        recipient_list=[recipient.email],
                    )
                    MailingAttempt.objects.create(
                        mailing=mailing,
                        status='Успешно',
                        server_response='Сообщение отправлено успешно',
                        attempt_date=timezone.now()
                    )
                    self.stdout.write(self.style.SUCCESS(f"Успешная отправка для {recipient.email}"))
                except Exception as e:
                    # logger.error(f"Ошибка отправки для {recipient.email}: {e}")
                    MailingAttempt.objects.create(
                        mailing=mailing,
                        status='Не успешно',
                        server_response=str(e),
                        attempt_date=timezone.now()
                    )

            # Обновление статуса рассылки
            mailing.status = 'Запущена'
            mailing.save()
            self.stdout.write(self.style.SUCCESS(f"Рассылка с Идентификатором {mailing_id} была успешно отправлена!"))

        except Mailing.DoesNotExist:
            raise CommandError(f"Рассылка с Идентификатором {mailing_id} не найдена")
