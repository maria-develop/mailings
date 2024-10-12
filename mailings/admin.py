from django.contrib import admin
from .models import Recipient, Message, Mailing, MailingAttempt


@admin.register(Recipient)
class RecipientAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'full_name', 'comment')
    list_filter = ('full_name',)
    search_fields = ('email', 'full_name', 'comment')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'subject',  'body', 'recipient')
    list_filter = ('subject',)
    search_fields = ('subject', 'recipient',)


@admin.register(Mailing)
# class MailingAdmin(admin.ModelAdmin):
#     list_display = ('id', 'start_time',  'end_time', 'status', 'message', 'recipients')
#     list_filter = ('id', 'status', 'recipients')
#     search_fields = ('start_time', 'status', 'recipient',)
class MailingAdmin(admin.ModelAdmin):
    list_display = ('start_time', 'end_time', 'status', 'message', 'get_recipients')

    def get_recipients(self, obj):
        return ", ".join([recipient.email for recipient in obj.recipients.all()])
    # get_recipients.short_description = 'Получатели'
