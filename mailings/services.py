from django.core.cache import cache

from config import settings
from config.settings import CACHE_ENABLED
from mailings.models import Mailing, Recipient

from django.core.mail import send_mail
from .models import MailingAttempt
import logging

logger = logging.getLogger(__name__)


def get_mailings_from_cache():
    """Получает данные из кеша о рассылках, если кеш пуст, получает данные из бд"""
    if not CACHE_ENABLED:
        return Mailing.objects.all()
    key = 'mailing_list'
    mailing = cache.get(key)
    if mailing is not None:
        return mailing
    mailing = Mailing.objects.all()
    cache.set(key, mailing)
    return mailing


def get_recipient_from_cache():
    """Получает данные из кеша о клиентах, если кеш пуст, получает данные из бд"""
    if not CACHE_ENABLED:
        return Recipient.objects.all()
    key = 'recipient_list'
    recipient = cache.get(key)
    if recipient is not None:
        return recipient
    recipient = Recipient.objects.all()
    cache.set(key, recipient)
    return recipient


def send_mailing_messages(mailing):
    """Отправляет сообщения получателям рассылки."""
    from_email = mailing.from_email  # Используем адрес из модели Mailing
    recipients = mailing.recipients.all()

    for recipient in recipients:
        try:
            send_mail(
                subject=mailing.message.subject,
                message=mailing.message.body,
                from_email=from_email,
                recipient_list=[recipient.email],
            )
            MailingAttempt.objects.create(
                mailing=mailing,
                status='Успешно',
                server_response='Сообщение отправлено успешно'
            )
        except Exception as e:
            MailingAttempt.objects.create(
                mailing=mailing,
                status='Не успешно',
                server_response=str(e)
            )
