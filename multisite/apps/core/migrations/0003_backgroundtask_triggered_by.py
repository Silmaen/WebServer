import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("core", "0002_backgroundtask_log"),
    ]

    operations = [
        migrations.AddField(
            model_name="backgroundtask",
            name="triggered_by",
            field=models.ForeignKey(
                blank=True,
                help_text="User who triggered this task (null = automatic)",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="background_tasks",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
