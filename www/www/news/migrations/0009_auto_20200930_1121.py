# Generated by Django 3.1.1 on 2020-09-30 09:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0008_extpage'),
    ]

    operations = [
        migrations.AddField(
            model_name='subwebpage',
            name='template',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AlterField(
            model_name='subwebpage',
            name='data',
            field=models.JSONField(blank=True),
        ),
        migrations.AlterField(
            model_name='webpage',
            name='data',
            field=models.JSONField(blank=True),
        ),
    ]
