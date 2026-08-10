from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("devices", "0005_alter_device_category"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="device",
            name="snmp_credential",
        ),
        migrations.DeleteModel(
            name="DevicePort",
        ),
        migrations.DeleteModel(
            name="SNMPCredential",
        ),
    ]
