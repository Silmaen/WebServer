"""Reflète `_common/inventory.conf` dans les lignes `Machine`, en ligne de commande.

La page et l'endpoint de rapport synchronisent d'eux-mêmes : ceci sert au cas où
aucun des deux n'a encore tourné, ou pour vérifier que le montage est bien là avant
de se demander pourquoi la page est vide.
"""

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.fleet import inventory


class Command(BaseCommand):
    """Relit l'inventaire et rapporte ce que la synchronisation a changé."""

    help = "Synchronise les machines depuis _common/inventory.conf"

    def add_arguments(self, parser):
        """Ajoute l'option de chemin de l'inventaire."""
        parser.add_argument(
            "--path", default=None,
            help="chemin de l'inventaire (défaut : FLEET_INVENTORY)",
        )

    def handle(self, *args, **options):
        """Lit l'inventaire puis réconcilie les machines."""
        path = options["path"] or settings.FLEET_INVENTORY
        rows = inventory.parse(path)
        if not rows:
            self.stderr.write(self.style.ERROR(f"aucune machine lue depuis {path}"))
            return
        result = inventory.sync(path)
        self.stdout.write(
            self.style.SUCCESS(
                f"{result['seen']} machines dans {path} : "
                f"{result['created']} créées, {result['updated']} mises à jour, "
                f"{result['retired']} retirées"
            )
        )
