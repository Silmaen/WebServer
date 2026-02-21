"""Suppression de la colonne hostname orpheline sur Machine."""
from django.db import migrations


def supprimer_hostname_orphelin(apps, schema_editor):
    """Supprime la colonne hostname de www_machine si elle existe.

    Cette colonne a été ajoutée par une version antérieure de la migration 0014,
    puis retirée du modèle sans migration correspondante.
    """
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("PRAGMA table_info(www_machine)")
        colonnes = [row[1] for row in cursor.fetchall()]
    if "hostname" in colonnes:
        schema_editor.execute("ALTER TABLE www_machine DROP COLUMN hostname")


class Migration(migrations.Migration):

    dependencies = [
        ("www", "0015_remove_machine_os"),
    ]

    operations = [
        migrations.RunPython(supprimer_hostname_orphelin, migrations.RunPython.noop),
    ]
