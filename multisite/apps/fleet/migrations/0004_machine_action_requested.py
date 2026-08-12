"""Horodate l'approbation publiée pour une machine, et retient son verbe.

Pourquoi, alors que `Stack.deploy_requested_at` venait d'être ajouté : parce que les
actions par machine sont les plus longues du lot. Un `upgrade` sur hecate a pris
quatorze minutes — `pacman -Syu` à lui seul — pendant lesquelles la page ne montrait
rien, et le rechargement automatique, borné à trois tours de vingt secondes, avait
renoncé quinze minutes trop tôt. Ces deux colonnes permettent au serveur de dire
« il reste quelque chose à attendre », au lieu de laisser le navigateur le deviner.

Nullable et vide par défaut : une machine existante n'a jamais reçu de demande.
"""

from django.db import migrations, models


class Migration(migrations.Migration):
    """Ajoute Machine.action_requested_at et Machine.action_requested_verb."""

    dependencies = [
        ("fleet", "0003_stack_deploy_requested_at"),
    ]

    operations = [
        migrations.AddField(
            model_name="machine",
            name="action_requested_at",
            field=models.DateTimeField(
                blank=True,
                null=True,
                help_text="dernière approbation publiée par la console",
            ),
        ),
        migrations.AddField(
            model_name="machine",
            name="action_requested_verb",
            field=models.CharField(
                blank=True,
                max_length=20,
                help_text="verbe de cette approbation, pour l'afficher",
            ),
        ),
    ]
