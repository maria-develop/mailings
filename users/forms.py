from mailings.forms import StyleFormMixin
from django.contrib.auth.forms import UserCreationForm
from django import forms

from users.models import User


class UserRegisterForm(StyleFormMixin, UserCreationForm):
    class Meta:
        model = User
        fields = ('email', 'password1', 'password2')


class PasswordResetRequestForm(forms.Form):
    """Форма запрашивает у пользователя email для восстановления пароля"""
    email = forms.EmailField(label="Введите ваш email")


class SetNewPasswordForm(forms.Form):
    """Форма для ввода нового пароля"""
    new_password = forms.CharField(widget=forms.PasswordInput, label="Новый пароль")
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Подтвердите пароль")

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get("new_password")
        confirm_password = cleaned_data.get("confirm_password")

        if new_password != confirm_password:
            raise forms.ValidationError("Пароли не совпадают.")
