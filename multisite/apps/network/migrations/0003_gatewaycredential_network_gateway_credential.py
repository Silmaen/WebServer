import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("network", "0002_network_last_scan"),
    ]

    operations = [
        migrations.CreateModel(
            name="GatewayCredential",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=100)),
                ("username", models.CharField(default="monitor", max_length=100)),
                ("password", models.CharField(max_length=200)),
                ("use_https", models.BooleanField(default=False)),
                ("verify_ssl", models.BooleanField(default=False, help_text="Verify SSL certificate (disable for self-signed)")),
            ],
            options={
                "ordering": ["name"],
            },
        ),
        migrations.AddField(
            model_name="network",
            name="gateway_credential",
            field=models.ForeignKey(
                blank=True, null=True,
                help_text="SSH credentials for the gateway (OpenWrt)",
                on_delete=django.db.models.deletion.SET_NULL,
                to="network.gatewaycredential",
            ),
        ),
    ]
