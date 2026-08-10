"""Mirror `_common/inventory.conf` into `Machine` rows, from the command line.

The page and the report endpoint both sync on their own, so this exists for the
case where neither has run yet — a fresh deploy, or checking that the mount is
actually there before wondering why the page is empty.
"""

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.fleet import inventory


class Command(BaseCommand):
    help = "Synchronise les machines depuis _common/inventory.conf"

    def add_arguments(self, parser):
        parser.add_argument("--path", default=None, help="chemin de l'inventaire (défaut : FLEET_INVENTORY)")

    def handle(self, *args, **options):
        path = options["path"] or settings.FLEET_INVENTORY
        rows = inventory.parse(path)
        if not rows:
            self.stderr.write(self.style.ERROR(f"aucune machine lue depuis {path}"))
            return
        result = inventory.sync(path)
        self.stdout.write(
            self.style.SUCCESS(
                f"{result['seen']} machines dans {path} : "
                f"{result['created']} créées, {result['updated']} mises à jour, {result['retired']} retirées"
            )
        )
