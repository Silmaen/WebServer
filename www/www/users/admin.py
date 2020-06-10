"""users.admin"""
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from .models import AccessPermission, CustomUser
from .forms import CustomUserCreationForm, CustomUserChangeForm


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = ('username', 'email', 'avatar',)
    list_filter = ('username', 'email', 'AccessPermissions',)
    ordering = ('username', 'email', 'AccessPermissions',)
    search_fields = ('username', 'email', 'AccessPermissions',)
    fieldsets = (
        ('General', {
            'fields': ('username', 'email', 'first_name', 'last_name', 'avatar'),
        }),
        ('Accreditations', {
            'fields': ('AccessPermissions', 'is_staff', 'is_active', 'user_permissions')
        }),
    )


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(AccessPermission)
