# Generated by Django 3.1.3 on 2021-02-04 15:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('potager', '0003_auto_20210203_1741'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='planttype',
            name='harvest',
        ),
        migrations.RemoveField(
            model_name='planttype',
            name='semis_abris',
        ),
        migrations.RemoveField(
            model_name='planttype',
            name='semis_terre',
        ),
        migrations.AddField(
            model_name='planttype',
            name='specifications',
            field=models.JSONField(default={}, verbose_name='Informations supplémentaires'),
        ),
        migrations.AlterField(
            model_name='plantation',
            name='Coordinates',
            field=models.JSONField(verbose_name='liste des coordonnées'),
        ),
    ]
