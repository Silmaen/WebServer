"""Permet d'acquitter l'alerte compose d'une stack — « je sais ».

Ce que ce champ rend possible : éteindre une alerte que la console ne peut pas réparer.
Une stack qui tourne, dont le dépôt est propre et à jour, et dont `homelab-probe` ne
reconnaît pas le fichier compose, se corrige dans `home-server-stacks` ; ici il n'y avait
qu'un encart rouge permanent, sans le moindre geste. Une alerte qu'on ne peut pas
éteindre finit par ne plus être lue du tout, y compris les jours où elle a raison.

Il retient l'**état acquitté** plutôt qu'un booléen : comparé à `compose`, il se réarme
seul dès que la sonde rapporte autre chose, sans rien à remettre à zéro à l'ingestion.
Vide par défaut, donc aucune alerte existante n'est tue par cette migration.
"""

from django.db import migrations, models


class Migration(migrations.Migration):
    """Ajoute Stack.alert_ack."""

    dependencies = [
        ("fleet", "0006_stack_compose_choices"),
    ]

    operations = [
        migrations.AddField(
            model_name="stack",
            name="alert_ack",
            field=models.CharField(
                max_length=16,
                blank=True,
                help_text="état compose dont l'alerte a été acquittée",
            ),
        ),
    ]
