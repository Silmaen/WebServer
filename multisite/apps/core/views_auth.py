"""Authentication views: login page with SSO + local fallback."""

from django.conf import settings
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import redirect, render
from django.views import View


class LoginView(View):
    """Login page with OIDC SSO button and local login form."""

    def get(self, request):
        if request.user.is_authenticated:
            return redirect(settings.LOGIN_REDIRECT_URL)
        return render(request, "core/login.html", {
            "form": AuthenticationForm(),
            "oidc_enabled": settings.OIDC_ENABLED,
        })

    def post(self, request):
        """Handle local login form submission."""
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user(), backend="django.contrib.auth.backends.ModelBackend")
            next_url = request.GET.get("next", settings.LOGIN_REDIRECT_URL)
            return redirect(next_url)
        return render(request, "core/login.html", {
            "form": form,
            "oidc_enabled": settings.OIDC_ENABLED,
        })


class LogoutView(View):
    """Logout and redirect to login page."""

    def get(self, request):
        logout(request)
        return redirect(settings.LOGOUT_REDIRECT_URL)

    def post(self, request):
        logout(request)
        return redirect(settings.LOGOUT_REDIRECT_URL)
