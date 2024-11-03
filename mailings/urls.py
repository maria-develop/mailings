from django.urls import path
from mailings.apps import MailingsConfig
from mailings.views import (MailingListView, MailingCreateView, MailingUpdateView, HomePageView,
                            MailingDeleteView, MailingDetailView, MailingSendView, MailingReportView,
                            RecipientListView, RecipientDetailView, RecipientCreateView, RecipientUpdateView,
                            RecipientDeleteView)

app_name = MailingsConfig.name


urlpatterns = [
    path("list/", MailingListView.as_view(), name="mailing_list"),
    path('create/', MailingCreateView.as_view(), name='mailing_create'),
    path('update/<int:pk>/', MailingUpdateView.as_view(), name='mailing_update'),
    path('delete/<int:pk>/', MailingDeleteView.as_view(), name='mailing_delete'),
    path('detail/<int:pk>/', MailingDetailView.as_view(), name='mailing_detail'),
    path('send/<int:pk>/', MailingSendView.as_view(), name='mailing_send'),
    path('report/<int:pk>/', MailingReportView.as_view(), name='mailing_report'),
    path('', HomePageView.as_view(), name='home'),

    path('recipient/', RecipientListView.as_view(), name="recipient_list"),
    path('recipient/<int:pk>/', RecipientDetailView.as_view(), name="recipient_detail"),
    path('recipient/create/', RecipientCreateView.as_view(), name="recipient_create"),
    path('recipient/update/<int:pk>/', RecipientUpdateView.as_view(), name='recipient_update'),
    path('recipient/delete/<int:pk>/', RecipientDeleteView.as_view(), name='recipient_delete'),
]
