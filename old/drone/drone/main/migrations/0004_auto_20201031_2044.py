# Generated by Django 3.1.2 on 2020-10-31 19:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0003_auto_20201030_1050'),
    ]

    operations = [
        migrations.RenameField(
            model_name='droneconfiguration',
            old_name='comments',
            new_name='description',
        ),
        migrations.RemoveField(
            model_name='droneconfiguration',
            name='specs',
        ),
        migrations.AddField(
            model_name='droneconfiguration',
            name='Composants',
            field=models.ManyToManyField(to='main.DroneComponent'),
        ),
        migrations.AddField(
            model_name='droneconfiguration',
            name='version_logiciel',
            field=models.CharField(max_length=40, null=True, verbose_name='Version du logiciel du contrôleur de vol'),
        ),
    ]