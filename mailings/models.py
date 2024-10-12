from django.db import models
from django import forms


class Recipient(models.Model):
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    comment = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.full_name} {self.email}"

    class Meta:
        verbose_name = "клиент"
        verbose_name_plural = "клиенты"
        ordering = [
            "email",
            "full_name",
            "comment",
        ]


class Message(models.Model):
    subject = models.CharField(max_length=255)
    body = models.TextField()

    recipient = models.ForeignKey(
        Recipient, on_delete=models.SET_NULL,
        related_name="message",
        null=True, blank=True,
        related_query_name='messages',
    )

    def __str__(self):
        return self.subject

    class Meta:
        verbose_name = "письмо"
        verbose_name_plural = "письма"
        ordering = [
            "subject",
            "recipient",
        ]


class Mailing(models.Model):
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(max_length=50, default='Создана')
    # status = models.CharField(max_length=50, choices=[('Создана', 'Создана'), ('Запущена', 'Запущена'), ('Завершена', 'Завершена')])
    # message = models.ForeignKey(Message, on_delete=models.CASCADE)
    message = models.ForeignKey(
        Message, on_delete=models.SET_NULL,
        related_name="message",
        null=True, blank=True,
        related_query_name='messages',
    )
    recipients = models.ManyToManyField(Recipient)
    # recipients = models.ForeignKey(
    #     Recipient, on_delete=models.SET_NULL,
    #     related_name="recipient",
    #     null=True, blank=True,
    #     related_query_name='recipients',
    # )

    def __str__(self):
        return f"Рассылка {self.id} {self.recipients} - {self.status}"

    class Meta:
        verbose_name = "рассылка"
        verbose_name_plural = "рассылки"
        ordering = [
            "id",
            "start_time",
            "status",
        ]


class MailingAttempt(models.Model):
    attempt_time = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50)  # 'Успешно' или 'Не успешно'
    # status = models.CharField(max_length=50, choices=[('Успешно', 'Успешно'), ('Не успешно', 'Не успешно')])
    # server_response = models.TextField()
    server_response = models.TextField(null=True, blank=True)  # Ответ сервера, если ошибка
    # mailing = models.ForeignKey(Mailing, on_delete=models.CASCADE)
    mailing = models.ForeignKey(
        Mailing, on_delete=models.SET_NULL,
        related_name="attempts",
        null=True, blank=True,
        related_query_name='attempts',
    )

    def __str__(self):
        return f"Попытка {self.id} - {self.status}"

    class Meta:
        verbose_name = "попытка"
        verbose_name_plural = "попытки"
        ordering = [
            "attempt_time",
            "status",
            "server_response",
        ]


# Форма для создания и редактирования сообщений
class MessageForm(forms.ModelForm):
    subject = models.CharField(max_length=255)
    body = models.TextField()
    recipients = models.ForeignKey(
        Recipient, on_delete=models.SET_NULL,
        related_name="recipient",
        null=True, blank=True,
        related_query_name='recipients',
    )

    class Meta:
        verbose_name = "сообщение"
        verbose_name_plural = "сообщения"
        ordering = [
            "subject",
            "body",
            "recipients",
        ]
        # fields = ['subject', 'body']


# Форма для создания и редактирования рассылок
class MailingForm(forms.ModelForm):
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(max_length=50,
                              choices=[('Создана', 'Создана'), ('Запущена', 'Запущена'), ('Завершена', 'Завершена')])
    # message = models.ForeignKey(Message, on_delete=models.CASCADE)
    message = models.ForeignKey(
        Message, on_delete=models.SET_NULL,
        related_name="message",
        null=True, blank=True,
        related_query_name='messages',
    )
    recipients = models.ForeignKey(
        Recipient, on_delete=models.SET_NULL,
        related_name="recipient",
        null=True, blank=True,
        related_query_name='recipients',
    )

    class Meta:
        verbose_name = "рассылка"
        verbose_name_plural = "рассылки"
        ordering = [
            "recipients",
            "status",
            "start_time",
        ]
