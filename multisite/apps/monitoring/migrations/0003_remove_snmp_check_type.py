from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("monitoring", "0002_alter_checkresult_status_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="monitoringcheck",
            name="check_type",
            field=models.CharField(
                choices=[
                    ("icmp", "Ping (ICMP)"),
                    ("tcp", "Port TCP"),
                    ("http", "HTTP(S)"),
                    ("dns", "DNS"),
                ],
                max_length=10,
            ),
        ),
    ]
