from django.db import models
from django import forms
import uuid

from users.models import User


class Recipient(models.Model):
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    comment = models.TextField(blank=True, null=True)
    owner = models.ForeignKey(
        User,
        verbose_name='Владелец',
        help_text='Укажите владельца рассылки',
        blank=True, null=True,
        on_delete=models.SET_NULL,
    )

    def __str__(self):
        return f"{self.full_name} {self.email}"

    class Meta:
        verbose_name = "клиент"
        verbose_name_plural = "клиенты"
        ordering = [
            "email",
            "full_name",
            "comment",
            "owner",
        ]


class Message(models.Model):
    subject = models.CharField(max_length=255)
    body = models.TextField()

    owner = models.ForeignKey(
        User,
        verbose_name='Владелец',
        help_text='Укажите владельца рассылки',
        blank=True, null=True,
        on_delete=models.SET_NULL,
    )

    # recipient = models.ForeignKey(
    #     Recipient, on_delete=models.SET_NULL,
    #     related_name="message",
    #     null=True, blank=True,
    #     related_query_name='messages',
    # )

    def __str__(self):
        return self.subject

    class Meta:
        verbose_name = "письмо"
        verbose_name_plural = "письма"
        ordering = [
            "subject",
            "owner",
        ]
    permissions = [
        ('manager_view_message', 'Can manager view message'),  # просмотр сообщений
    ]


class Mailing(models.Model):
    STATUS_CHOICES = [
        ('Создана', 'Создана'),
        ('Запущена', 'Запущена'),
        ('Завершена', 'Завершена'),
    ]
    start_time = models.DateTimeField(verbose_name='Начало отправки рассылки')
    end_time = models.DateTimeField(verbose_name='Последняя дата отправки рассылки', null=True, blank=True)
    # status = models.CharField(max_length=50, default='Создана')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Создана')
    mail_active = models.BooleanField(verbose_name='Активность рассылки', default=True)

    message = models.ForeignKey(
        Message, on_delete=models.SET_NULL,
        related_name="message",
        null=True, blank=True,
        related_query_name='messages',
    )
    recipients = models.ManyToManyField(Recipient, verbose_name='Клиент', related_name='client')

    views_count = models.PositiveIntegerField(
        verbose_name="Количество рассылок",
        help_text="Укажите количество рассылок",
        default=0,
    )

    owner = models.ForeignKey(
        User,
        verbose_name='Владелец',
        help_text='Укажите владельца рассылки',
        blank=True, null=True,
        on_delete=models.SET_NULL,
    )

    def __str__(self):
        return f"Рассылка {self.start_time} {self.recipients} - {self.status}"

    class Meta:
        verbose_name = "рассылка"
        verbose_name_plural = "рассылки"
        ordering = [
            # "id",
            "start_time",
            "status",
            "views_count",
            "owner",
        ]
        permissions = [
            ('disabling_mailing', 'Can disable mailing'),  # отключение рассылок
            ('viewing_statistics', 'Can viewing statistics'),  # просмотр статистики по своим рассылкам
        ]


class MailingAttempt(models.Model):
    STATUS_CHOICES = [
        ('created', 'Создана'),
        ('started', 'Запущена'),
        ('completed', 'Завершена'),
    ]
    attempt_time = models.DateTimeField(auto_now_add=True)
    # status = models.CharField(max_length=50)  # 'Успешно' или 'Не успешно'
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='created')
    server_response = models.TextField(null=True, blank=True)  # Ответ сервера, если ошибка
    # mailing = models.ForeignKey(Mailing, on_delete=models.CASCADE)
    mailing = models.ForeignKey(
        Mailing, on_delete=models.SET_NULL,
        related_name="attempts",
        null=True, blank=True,
        related_query_name='attempts',
    )
    from_email = models.EmailField(
        verbose_name="Адрес отправителя",
        default="default-email@example.com",
        help_text="Укажите адрес электронной почты отправителя."
    )
    # recipients = forms.ModelMultipleChoiceField(
    #     queryset=Recipient.objects.all(),
    #     widget=forms.CheckboxSelectMultiple,
    #     label="Выберите получателей"
    # )

    def __str__(self):
        return f"Попытка {self.status}"

    class Meta:
        verbose_name = "попытка"
        verbose_name_plural = "попытки"
        ordering = [
            "attempt_time",
            "status",
            "server_response",
        ]


class Parent(models.Model):
    mailing = models.ForeignKey(
        Mailing,
        related_name='parents',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Сообщение',
    )

    subject = models.CharField(
        max_length=100,
        verbose_name="Наименование сообщения",
        help_text="Введите наименование сообщения",
        null=True, blank=True,
    )

    body = models.TextField(
        verbose_name="Текст сообщения",
        help_text="Введите текст сообщения",
        null=True, blank=True,
    )

    status = models.CharField(max_length=50)  # 'Успешно' или 'Не успешно'

    class Meta:
        verbose_name = "Родительский сообщение"
        verbose_name_plural = "Родительские сообщения"
        ordering = [
            "mailing",
            "subject",
            "body",
            "status",
        ]

    def __str__(self):
        return f"Наименование рассылки: {self.mailing}"


# class MessageForm(forms.ModelForm):
#     """Форма для создания и редактирования сообщений"""
#     subject = models.CharField(max_length=255)
#     body = models.TextField()
#     recipients = models.ForeignKey(
#         Recipient, on_delete=models.SET_NULL,
#         related_name="recipient",
#         null=True, blank=True,
#         related_query_name='recipients',
#     )
#
#     class Meta:
#         verbose_name = "сообщение"
#         verbose_name_plural = "сообщения"
#         ordering = [
#             "subject",
#             "body",
#             "recipients",
#         ]
#
#
# class MailingForm(forms.ModelForm):
#     """Форма для создания и редактирования рассылок"""
#     start_time = models.DateTimeField()
#     end_time = models.DateTimeField()
#     status = models.CharField(max_length=50,
#                               choices=[('Создана', 'Создана'), ('Запущена', 'Запущена'), ('Завершена', 'Завершена')])
#     message = models.ForeignKey(
#         Message, on_delete=models.SET_NULL,
#         related_name="message",
#         null=True, blank=True,
#         related_query_name='messages',
#     )
#     recipients = models.ForeignKey(
#         Recipient, on_delete=models.SET_NULL,
#         related_name="recipient",
#         null=True, blank=True,
#         related_query_name='recipients',
#     )

    # class Meta:
    #     verbose_name = "рассылка"
    #     verbose_name_plural = "рассылки"
    #     ordering = [
    #         "recipients",
    #         "status",
    #         "start_time",
    #     ]
