"""Formulaires de l'application réseau."""

from django import forms

from .models import GatewayCredential


class GatewayCredentialForm(forms.ModelForm):
    """Identifiants de passerelle, avec un mot de passe jamais réaffiché."""

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        help_text="Mot de passe de l'utilisateur rpcd sur le routeur.",
    )

    class Meta:
        """Meta informations"""
        model = GatewayCredential
        fields = ["name", "username", "password", "use_https", "verify_ssl"]

    def __init__(self, *args, **kwargs):
        """En modification, le mot de passe devient facultatif."""
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["password"].required = False
            self.fields["password"].help_text = "Laisser vide pour ne pas changer."

    def clean_password(self):
        """Conserve le mot de passe enregistré quand le champ est laissé vide."""
        password = self.cleaned_data.get("password")
        if not password and self.instance.pk:
            return self.instance.password
        return password
