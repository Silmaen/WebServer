"""Horodate la demande de mise à jour d'une stack.

Ce que ce champ rend possible : dire « déploiement en cours » entre le clic et le
rapport qui suit. Avant, la page publiait la demande et réaffichait l'état d'avant,
donc pendant une minute et demie rien ne distinguait « en cours » de « rien fait ».

Nullable et sans valeur par défaut : une ligne existante n'a jamais été demandée, et
`null` dit exactement ça. Aucune donnée à réécrire, donc rien à dérouler en sens
inverse -- la migration inverse retire simplement la colonne.
"""

from django.db import migrations, models


class Migration(migrations.Migration):
    """Ajoute Stack.deploy_requested_at."""

    dependencies = [
        ("fleet", "0002_stack_deploy_script"),
    ]

    operations = [
        migrations.AddField(
            model_name="stack",
            name="deploy_requested_at",
            field=models.DateTimeField(
                blank=True,
                null=True,
                help_text="dernière demande de mise à jour publiée par la console",
            ),
        ),
    ]
