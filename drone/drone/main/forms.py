"""main.forms"""
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, PasswordResetForm
from .models import *
from markdownx.forms import forms


class CustomUserCreationForm(UserCreationForm):
    """
    form for user creation
    """
    class Meta(UserCreationForm.Meta):
        """
        Meta informations
        """
        fields = UserCreationForm.Meta.fields + ("first_name", "last_name", "email")

    def save(self, commit=True):
        """
        saving function
        """
        user = super(CustomUserCreationForm, self).save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class CustomUserChangeForm(UserChangeForm):
    """
    form for user profile change
    """
    class Meta(UserChangeForm.Meta):
        """
        Meta informations
        """
        fields = ('email', 'first_name', 'last_name', 'password')


class ArticleCommentForm(forms.ModelForm):
    """
    form for comment creation
    """
    class Meta:
        """
        Meta informations
        """
        model = ArticleComments
        fields = ('contenu',)


class DroneComponentCommentForm(forms.ModelForm):
    """
    form for comment creation
    """
    class Meta:
        """
        Meta informations
        """
        model = DroneComponentComments
        fields = ('contenu',)


class DroneConfigurationCommentForm(forms.ModelForm):
    """
    form for comment creation
    """
    class Meta:
        """
        Meta informations
        """
        model = ConfigurationComments
        fields = ('contenu',)


class DroneFlightCommentForm(forms.ModelForm):
    """
    form for comment creation
    """
    class Meta:
        """
        Meta informations
        """
        model = FlightComments
        fields = ('contenu',)
