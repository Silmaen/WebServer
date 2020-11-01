"""main.forms"""
from django.contrib.auth.forms import UserCreationForm
from django import forms
from .models import ArticleComments


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        fields = UserCreationForm.Meta.fields + ("first_name", "last_name", "email")

