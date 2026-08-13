"""Distingue une stack cassée d'une stack qui n'est plus déployée.

Ce que ce champ rend possible : faire taire une alerte qui n'avait pas de fin. Une
stack déplacée ou supprimée cesse d'être rapportée par `homelab-probe`, mais sa ligne
restait figée sur le dernier état vu -- souvent `compose: missing`, puisque c'est
l'instant où le répertoire venait de bouger. La page annonçait donc pour toujours une
stack sans fichier compose exploitable, et il n'existait aucun geste pour la corriger :
la seule machine capable de la mettre à jour ne la connaissait plus.

`default=True` pour les lignes existantes : à cet instant on ne sait pas lesquelles ont
disparu, et supposer le contraire ferait disparaître d'un coup des alertes légitimes.
Le premier rapport de chaque machine tranche -- il porte la liste complète de ses
stacks -- donc l'état se corrige de lui-même en moins d'une heure.
"""

from django.db import migrations, models


class Migration(migrations.Migration):
    """Ajoute Stack.present."""

    dependencies = [
        ("fleet", "0004_machine_action_requested"),
    ]

    operations = [
        migrations.AddField(
            model_name="stack",
            name="present",
            field=models.BooleanField(
                default=True,
                help_text="présente dans le dernier rapport de la machine",
            ),
        ),
    ]
