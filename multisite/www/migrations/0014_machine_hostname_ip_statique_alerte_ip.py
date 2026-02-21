"""Ajout ip_statique, alerte_ip sur Machine + adresse_ip nullable."""
from django.db import migrations, models


def copier_ip_vers_statique(apps, schema_editor):
    """Copie adresse_ip vers ip_statique pour les machines existantes."""
    Machine = apps.get_model("www", "Machine")
    for machine in Machine.objects.all():
        if machine.adresse_ip:
            machine.ip_statique = machine.adresse_ip
            machine.save(update_fields=["ip_statique"])


class Migration(migrations.Migration):

    dependencies = [
        ("www", "0013_machine_scan_dates_serveur_hostname_description"),
    ]

    operations = [
        migrations.AddField(
            model_name="machine",
            name="ip_statique",
            field=models.GenericIPAddressField(
                blank=True, null=True, verbose_name="IP statique attendue"
            ),
        ),
        migrations.AddField(
            model_name="machine",
            name="alerte_ip",
            field=models.CharField(
                blank=True, default="", max_length=300, verbose_name="Alerte IP"
            ),
        ),
        migrations.RunPython(copier_ip_vers_statique, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="machine",
            name="adresse_ip",
            field=models.GenericIPAddressField(
                blank=True, null=True, verbose_name="Adresse IP"
            ),
        ),
    ]
