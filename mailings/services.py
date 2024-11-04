from django.core.cache import cache

from config.settings import CACHE_ENABLED
from mailings.models import Mailing, Recipient


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
