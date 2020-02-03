from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm

from .forms import CustomUserCreationForm, CustomUserChangeForm

class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'signup.html'

class UserSettings(CreateView):
    form_class = CustomUserChangeForm
    success_url = reverse_lazy('login')
    template_name = 'userSetting.html'


