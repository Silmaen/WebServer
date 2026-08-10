from django import forms

from .models import GatewayCredential


class GatewayCredentialForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        help_text="Mot de passe de l'utilisateur rpcd sur le routeur.",
    )

    class Meta:
        model = GatewayCredential
        fields = ["name", "username", "password", "use_https", "verify_ssl"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            # In edit mode, don't require re-entering the password
            self.fields["password"].required = False
            self.fields["password"].help_text = "Laisser vide pour ne pas changer."

    def clean_password(self):
        password = self.cleaned_data.get("password")
        if not password and self.instance.pk:
            return self.instance.password
        return password
