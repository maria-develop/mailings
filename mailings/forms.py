from django.core.exceptions import ValidationError
from django.forms import ModelForm, BooleanField
from django.utils import timezone
from mailings.models import Mailing, Recipient, Parent, MailingAttempt
from django import forms


class StyleFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for fild_name, fild in self.fields.items():
            if isinstance(fild, BooleanField):
                fild.widget.attrs['class'] = 'form-check-input'
            else:
                fild.widget.attrs['class'] = 'form-control'


class RecipientForm(StyleFormMixin, forms.ModelForm):
    class Meta:
        model = Recipient
        fields = '__all__'


class MailingForm(StyleFormMixin, ModelForm):
    forbidden_words_name = ['казино', 'криптовалюта', 'крипта', 'биржа', 'дешево', 'бесплатно', 'обман', 'полиция',
                            'радар']
    forbidden_words_description = ['казино', 'криптовалюта', 'крипта', 'биржа', 'дешево', 'бесплатно', 'обман',
                                   'полиция', 'радар']

    class Meta:
        model = Mailing
        exclude = ('owner',)
        # fields = '__all__'

    def clean_mailing_subject(self):
        name = self.cleaned_data.get('subject').lower()
        for word in self.forbidden_words_name:
            if word in name:
                raise forms.ValidationError("Наименование сообщения содержит запрещенное слово: {}".format(word))
        return name

    def clean_mailing_body(self):
        description = self.cleaned_data.get('body').lower()
        for word in self.forbidden_words_description:
            if word in description:
                raise forms.ValidationError("Текст сообщения содержит запрещенное слово: {}".format(word))
        return description


class MailingManagerForm(ModelForm, StyleFormMixin):
    class Meta:
        model = Mailing
        fields = ('mail_active',)


class MailingAttemptManagerForm(ModelForm, StyleFormMixin):
    class Meta:
        model = MailingAttempt
        fields = ('mailing',)


class ParentForm(StyleFormMixin, ModelForm):
    class Meta:
        model = Parent
        fields = "__all__"
