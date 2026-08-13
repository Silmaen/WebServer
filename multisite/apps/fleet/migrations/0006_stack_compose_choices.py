"""Déclare les choix de `Stack.compose`, ce qui rend son libellé affichable.

Aucun changement de schéma : `choices` ne pose ni contrainte ni type en base sur
PostgreSQL. Ce que cette migration corrige est ailleurs -- sans `choices`, Django ne
génère pas `get_compose_display()`, le gabarit avale l'attribut manquant en silence, et
la colonne « Compose » de la page Stacks est restée vide depuis le premier jour. Les
valeurs déjà en base sont exactement celles de `Compose`, il n'y a donc rien à réécrire.
"""

from django.db import migrations, models


class Migration(migrations.Migration):
    """Ajoute les choices sur Stack.compose."""

    dependencies = [
        ("fleet", "0005_stack_present"),
    ]

    operations = [
        migrations.AlterField(
            model_name="stack",
            name="compose",
            field=models.CharField(
                max_length=16,
                default="-",
                choices=[
                    ("tracked", "Suivi par git"),
                    ("untracked", "Jamais commité"),
                    ("missing", "Fichier disparu"),
                    ("no-git", "Hors dépôt git"),
                    ("-", "Inconnu"),
                ],
            ),
        ),
    ]
