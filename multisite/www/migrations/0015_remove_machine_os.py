"""Suppression des champs OS de Machine."""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("www", "0014_machine_hostname_ip_statique_alerte_ip"),
    ]

    operations = [
        migrations.RemoveField(model_name="machine", name="os_detecte"),
        migrations.RemoveField(model_name="machine", name="os_attendu"),
        migrations.RemoveField(model_name="machine", name="dernier_scan_os"),
    ]
