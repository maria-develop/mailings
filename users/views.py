import secrets
from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView, ListView, UpdateView
from django.core.mail import send_mail
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.conf import settings
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.http import HttpResponseForbidden
from django.views import View


from users.forms import (UserRegisterForm, PasswordResetRequestForm, SetNewPasswordForm,
                         UserProfileForm, UserManagerProfileForm)
from users.models import User
from config.settings import EMAIL_HOST_USER


class UserCreateView(CreateView):
    model = User
    form_class = UserRegisterForm
    success_url = reverse_lazy('users:login')

    def form_valid(self, form):
        user = form.save()
        user.is_active = False
        token = secrets.token_hex(16)
        user.token = token
        user.save()
        host = self.request.get_host()
        url = f'http://{host}/users/email-confirm/{token}/'
        send_mail(
            subject='Подтверждение почты',
            message=f'Перейдите по ссылке для подтверждения почты {url}',
            from_email=EMAIL_HOST_USER,
            recipient_list=[user.email],
        )

        return super().form_valid(form)


class UsersListView(PermissionRequiredMixin, ListView):
    """Просмотр списка пользователей"""
    model = User
    template_name = 'users/user_list.html'
    context_object_name = 'object_list_users'
    permission_required = "users.view_all_users"


class ProfileView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserProfileForm
    template_name = 'users/user_edit_form.html'
    success_url = reverse_lazy('newsletter:homepage')

    def get_object(self, queryset=None):
        return self.request.user

    def get_form_class(self):
        user = self.request.user
        if user.has_perm('users.blocking_users'):
            return UserManagerProfileForm
        return UserProfileForm


def email_verification(request, token):
    user = get_object_or_404(User, token=token)
    user.is_active = True
    user.save()
    return redirect(reverse('users:login'))


class BlockUserView(LoginRequiredMixin, View):
    def post(self, request, pk):
        user_to_block = get_object_or_404(User, id=pk)

        if not request.user.has_perm('mailings.blocking_users'):
            return HttpResponseForbidden("У вас нет прав для блокировки пользователя.")

        # Логика блокировки пользователя
        user_to_block.is_active = False
        user_to_block.save()

        return redirect('users:block_user')


User = get_user_model()


class UnblockUserView(LoginRequiredMixin, View):
    def post(self, request, pk):
        user_to_unblock = get_object_or_404(User, id=pk)

        if not request.user.has_perm('mailings.unblocking_users'):
            return HttpResponseForbidden("У вас нет прав для разблокировки пользователя.")

        # Логика разблокировки пользователя
        user_to_unblock.is_active = True
        user_to_unblock.save()

        return redirect('users:list_view')


def password_reset_request(request):
    if request.method == "POST":
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            user = get_object_or_404(User, email=email)
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(str(user.pk).encode())
            reset_url = request.build_absolute_uri(
                reverse("users:password_reset_confirm", kwargs={"uidb64": uid, "token": token})
            )
            send_mail(
                "Восстановление пароля",
                f"Перейдите по ссылке, чтобы сбросить пароль: {reset_url}",
                settings.EMAIL_HOST_USER,
                [email],
            )
            return redirect("users:password_reset_done")
    else:
        form = PasswordResetRequestForm()
    return render(request, "users/password_reset_form.html", {"form": form})


def password_reset_confirm(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == "POST":
            form = SetNewPasswordForm(request.POST)
            if form.is_valid():
                user.set_password(form.cleaned_data["new_password"])
                user.save()
                return redirect("users:password_reset_complete")
        else:
            form = SetNewPasswordForm()
        return render(request, "users/password_reset_confirm.html", {"form": form})
    else:
        return redirect("users:password_reset_invalid")


def password_reset_done(request):
    return render(request, "users/password_reset_done.html")


def password_reset_complete(request):
    return render(request, "users/password_reset_complete.html")


def password_reset_invalid(request):
    return render(request, "users/password_reset_invalid.html")
