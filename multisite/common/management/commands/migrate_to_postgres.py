"""Exporte les données de la base courante pour un chargement dans PostgreSQL."""
import os
import subprocess
import sys

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Exporte la base courante via `dumpdata`, puis affiche la suite à faire."""

    help = "Exporte les données pour migration vers PostgreSQL"

    def add_arguments(self, parser):
        """Ajoute les arguments de la commande."""
        parser.add_argument(
            "-o", "--output",
            default="dump.json",
            help="Chemin du fichier de sortie (défaut : dump.json)",
        )

    def handle(self, *args, **options):
        """Exécute l'export des données."""
        output = options["output"]

        self.stdout.write("Export des données de la base actuelle...")
        cmd = [
            sys.executable, "manage.py", "dumpdata",
            "--natural-foreign", "--natural-primary",
            "--exclude", "contenttypes",
            "--exclude", "auth.permission",
            "--indent", "2",
            "-o", output,
        ]

        result = subprocess.run(
            cmd,
            cwd=os.path.dirname(os.path.abspath("manage.py")),
        )

        if result.returncode != 0:
            self.stderr.write(self.style.ERROR("Erreur lors de l'export."))
            return

        self.stdout.write(self.style.SUCCESS(f"Données exportées dans {output}"))
        self.stdout.write("")
        self.stdout.write("Étapes suivantes :")
        self.stdout.write("  1. Configurer les variables PostgreSQL dans .env")
        self.stdout.write("  2. Lancer les migrations :")
        self.stdout.write("       python manage.py migrate")
        self.stdout.write("  3. Charger les données :")
        self.stdout.write(f"       python manage.py loaddata {output}")
