from django.core.management import BaseCommand
import os
from users.models import User

from dotenv import load_dotenv
# Загружаем переменные окружения из файла .env
load_dotenv(override=True)


class Command(BaseCommand):
    def handle(self, *args, **options):
        user = User.objects.create(email=os.getenv('USER_EMAIL'))
        user.set_password(os.getenv('USER_PASSWORD'))
        user.is_active = True
        user.is_staff = True
        user.is_superuser = True
        user.save()
