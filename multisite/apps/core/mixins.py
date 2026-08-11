"""Mixins de contrôle d'accès et d'intégration des pages de la console.

Deux niveaux d'accès : `ViewerRequiredMixin` (groupe "viewers" ou "admins") et
`StaffRequiredMixin` (staff uniquement).
"""

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


class ViewerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Réserve la vue aux utilisateurs autorisés (viewers ou admins)."""

    def test_func(self):
        """Vrai si l'utilisateur est staff ou membre d'un groupe de la console."""
        user = self.request.user
        if user.is_superuser or user.is_staff:
            return True
        return user.groups.filter(name__in=["viewers", "admins"]).exists()


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Réserve la vue au staff (admins)."""

    def test_func(self):
        """Vrai si l'utilisateur est staff ou superuser."""
        user = self.request.user
        return user.is_superuser or user.is_staff


class ConsolePageMixin:
    """Branche une page de la console sur le gabarit du site.

    Fournit les mêmes clés de contexte que `www.render_utils.get_page_data` :
    le titre affiché dans le bandeau, l'entrée de navigation à surligner et la
    sous-navigation en ligne. Sans elle, les pages de la console affichaient
    « Console » en titre et aucune entrée de menu active.
    """

    page_title = ""
    # Nom d'URL de l'entrée de navigation à surligner (ex. "fleet:index").
    nav_page = ""
    # Nom de la sous-page active, à faire correspondre au "name" d'une sous-page.
    subpage_title = ""
    subpages = ()

    def get_page_title(self):
        """Titre affiché ; à surcharger quand il dépend de l'objet de la page."""
        return self.page_title

    def get_context_data(self, **kwargs):
        """Ajoute le titre et les repères de navigation au contexte."""
        ctx = super().get_context_data(**kwargs)
        ctx.setdefault("page_subtitle", self.get_page_title())
        ctx.setdefault("page", self.nav_page)
        ctx.setdefault("subpage", self.subpage_title)
        ctx.setdefault("subpages", list(self.subpages))
        return ctx
