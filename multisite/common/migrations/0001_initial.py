# Generated by Django 3.1.3 on 2020-11-17 14:38

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import markdownx.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SiteArticle',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titre', models.CharField(max_length=100, verbose_name="Titre de l'article")),
                ('slug', models.SlugField(max_length=100, verbose_name="slug de l'article")),
                ('contenu', markdownx.models.MarkdownxField(blank=True, default='', verbose_name="Contenu de l'article au format Markdown")),
                ('date', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Date de parution')),
                ('private', models.BooleanField(default=False, verbose_name='Nécessite un utilisateur pour être vu')),
                ('superprivate', models.BooleanField(default=False, verbose_name="Nécessite un utilisateur validé ou l'auteur pour être vu")),
                ('staff', models.BooleanField(default=False, verbose_name="Nécessite un utilisateur du staff ou l'auteur pour être vu")),
                ('developper', models.BooleanField(default=False, verbose_name="Nécessite un utilisateur 'développeur' pour être vu")),
                ('auteur', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name="Auteur de l'article")),
            ],
            options={
                'verbose_name': 'article',
                'ordering': ['-date'],
            },
        ),
        migrations.CreateModel(
            name='SiteArticleComment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('contenu', markdownx.models.MarkdownxField(blank=True, default='', verbose_name='Contenu du commentaire au format Markdown')),
                ('date', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Date de parution')),
                ('active', models.BooleanField(default=False)),
                ('article', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='common.sitearticle', verbose_name='Article lié')),
                ('auteur', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Auteur du commentaire')),
            ],
            options={
                'verbose_name': "Commentaire d'article",
                'ordering': ['-date'],
            },
        ),
    ]
