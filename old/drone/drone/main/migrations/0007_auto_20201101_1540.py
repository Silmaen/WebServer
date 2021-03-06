# Generated by Django 3.1.2 on 2020-11-01 14:40

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('main', '0006_auto_20201101_1523'),
    ]

    operations = [
        migrations.RenameField(
            model_name='articlecomments',
            old_name='Article',
            new_name='article',
        ),
        migrations.AlterField(
            model_name='article',
            name='auteur',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name="Auteur de l'article"),
        ),
    ]
