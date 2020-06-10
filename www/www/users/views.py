"""users.views"""
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView

from .forms import CustomUserCreationForm, CustomUserChangeForm

class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'signup.html'

class UserSettings(CreateView):
    form_class = CustomUserChangeForm
    success_url = reverse_lazy('login')
    template_name = 'userSetting.html'


