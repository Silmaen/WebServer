# Generated by Django 3.1.2 on 2020-11-01 16:49

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import markdownx.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('main', '0007_auto_20201101_1540'),
    ]

    operations = [
        migrations.AlterField(
            model_name='articlecomments',
            name='article',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='main.article', verbose_name='Article du commentaire'),
        ),
        migrations.CreateModel(
            name='FlightComments',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('contenu', markdownx.models.MarkdownxField(blank=True, default='', verbose_name="Contenu de l'article au format Markdown")),
                ('date', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Date de parution')),
                ('active', models.BooleanField(default=False)),
                ('article', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='main.droneflight', verbose_name='Article du commentaire')),
                ('user', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Auteur du commentaire')),
            ],
            options={
                'verbose_name': "Commentaire d'article",
                'ordering': ['date'],
            },
        ),
        migrations.CreateModel(
            name='ConfigurationComments',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('contenu', markdownx.models.MarkdownxField(blank=True, default='', verbose_name="Contenu de l'article au format Markdown")),
                ('date', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Date de parution')),
                ('active', models.BooleanField(default=False)),
                ('article', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='main.droneconfiguration', verbose_name='Article du commentaire')),
                ('user', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Auteur du commentaire')),
            ],
            options={
                'verbose_name': "Commentaire d'article",
                'ordering': ['date'],
            },
        ),
    ]