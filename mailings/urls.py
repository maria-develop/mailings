from django.urls import path
from mailings import views
from django.views.decorators.cache import cache_page
from mailings.apps import MailingsConfig
from mailings.views import (MailingListView, MailingCreateView, MailingUpdateView, HomePageView,
                            MailingDeleteView, MailingDetailView, MailingSendView, MailingReportView,
                            RecipientListView, RecipientDetailView, RecipientCreateView, RecipientUpdateView,
                            RecipientDeleteView, DisableMailingView, EnableMailingView, MailingAttemptListView,
                            MessageListView, MessageDetailView, MessageCreateView, MessageUpdateView, MessageDeleteView)

app_name = MailingsConfig.name


urlpatterns = [
    path("list/", MailingListView.as_view(), name="mailing_list"),
    path('create/', MailingCreateView.as_view(), name='mailing_create'),
    path('update/<int:pk>/', MailingUpdateView.as_view(), name='mailing_update'),
    path('delete/<int:pk>/', MailingDeleteView.as_view(), name='mailing_delete'),
    path('detail/<int:pk>/', cache_page(1)(MailingDetailView.as_view()), name='mailing_detail'),
    path('send/<int:pk>/', MailingSendView.as_view(), name='mailing_send'),
    path('report/<int:pk>/', MailingReportView.as_view(), name='mailing_report'),
    path("mailingattempt_list/", MailingAttemptListView.as_view(), name="mailingattempt_list"),
    path('', HomePageView.as_view(), name='home'),

    # path('block_user/<int:pk>/', BlockUserView.as_view(), name='block_user'),
    path('disabling_mailing/<int:start_time>/', DisableMailingView.as_view(), name='disabling_mailing'),
    path('enable_mailing/<int:start_time>/', EnableMailingView.as_view(), name='enable_mailing'),

    path('recipient/', RecipientListView.as_view(), name="recipient_list"),
    path('recipient/<int:pk>/', cache_page(1)(RecipientDetailView.as_view()), name="recipient_detail"),
    path('recipient/create/', RecipientCreateView.as_view(), name="recipient_create"),
    path('recipient/update/<int:pk>/', RecipientUpdateView.as_view(), name='recipient_update'),
    path('recipient/delete/<int:pk>/', RecipientDeleteView.as_view(), name='recipient_delete'),

    path('messages/', MessageListView.as_view(), name='message_list'),
    path('messages/<int:pk>/', MessageDetailView.as_view(), name='message_detail'),
    path('messages/create/', MessageCreateView.as_view(), name='message_create'),
    path('messages/update/<int:pk>/', MessageUpdateView.as_view(), name='message_update'),
    path('messages/delete/<int:pk>/', MessageDeleteView.as_view(), name='message_delete'),
]
