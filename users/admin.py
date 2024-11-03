from django.contrib import admin

from users.models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'phone', 'country',)
    list_filter = ('email',)
    search_fields = ('email', 'phone', 'country',)
