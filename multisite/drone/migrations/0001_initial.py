# Generated by Django 3.1.3 on 2020-11-17 14:38

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('common', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DroneArticle',
            fields=[
                ('sitearticle_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='common.sitearticle')),
            ],
            options={
                'verbose_name': 'Article du site de drone',
                'ordering': ['-date'],
            },
            bases=('common.sitearticle',),
        ),
        migrations.CreateModel(
            name='DroneArticleComment',
            fields=[
                ('sitearticlecomment_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='common.sitearticlecomment')),
            ],
            options={
                'verbose_name': "Commentaire d'article de drone",
                'ordering': ['-date'],
            },
            bases=('common.sitearticlecomment',),
        ),
        migrations.CreateModel(
            name='DroneComponent',
            fields=[
                ('sitearticle_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='common.sitearticle')),
                ('specs', models.JSONField(blank=True, default=dict, verbose_name='Caractéristiques')),
                ('datasheet', models.URLField(blank=True, null=True, verbose_name='Liens vers la datasheet')),
                ('photo', models.ImageField(blank=True, null=True, upload_to='compimg', verbose_name='Photo du composant')),
            ],
            options={
                'verbose_name': 'Composant de Drone',
                'ordering': ['category', 'titre'],
            },
            bases=('common.sitearticle',),
        ),
        migrations.CreateModel(
            name='DroneComponentCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=40, verbose_name='Nom de la catégorie')),
                ('onBoard', models.BooleanField(verbose_name='Composant volant ou restant au sol')),
            ],
        ),
        migrations.CreateModel(
            name='DroneComponentComment',
            fields=[
                ('sitearticlecomment_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='common.sitearticlecomment')),
            ],
            options={
                'verbose_name': 'Commentaire de composant de drone',
                'ordering': ['-date'],
            },
            bases=('common.sitearticlecomment',),
        ),
        migrations.CreateModel(
            name='DroneConfiguration',
            fields=[
                ('sitearticle_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='common.sitearticle')),
                ('version_number', models.CharField(max_length=10, verbose_name='Numéro de version')),
                ('version_logiciel', models.CharField(blank=True, default='', max_length=40, verbose_name='Version du logiciel du contrôleur de vol')),
                ('photo', models.ImageField(blank=True, null=True, upload_to='confimg', verbose_name='Photo de la configuration')),
                ('Composants', models.ManyToManyField(to='drone.DroneComponent', verbose_name='Composants du drone')),
            ],
            options={
                'verbose_name': 'Configuration Drone',
                'ordering': ['-date'],
            },
            bases=('common.sitearticle',),
        ),
        migrations.CreateModel(
            name='DroneConfigurationComment',
            fields=[
                ('sitearticlecomment_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='common.sitearticlecomment')),
            ],
            options={
                'verbose_name': 'Commentaire de configuration de drone',
                'ordering': ['-date'],
            },
            bases=('common.sitearticlecomment',),
        ),
        migrations.CreateModel(
            name='DroneFlightComment',
            fields=[
                ('sitearticlecomment_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='common.sitearticlecomment')),
            ],
            options={
                'verbose_name': 'Commentaire de vol de drone',
                'ordering': ['-date'],
            },
            bases=('common.sitearticlecomment',),
        ),
        migrations.CreateModel(
            name='DroneFlight',
            fields=[
                ('sitearticle_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='common.sitearticle')),
                ('meteo', models.JSONField(blank=True, default=dict, verbose_name='Definition Météo')),
                ('datalog', models.FileField(blank=True, upload_to='datalog', verbose_name='lien vers le log du vol')),
                ('video', models.FileField(blank=True, upload_to='videoflight', verbose_name='Vidéo du vol')),
                ('drone_configuration', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='drone.droneconfiguration', verbose_name='la configuration de drone utilise')),
            ],
            options={
                'verbose_name': 'Vol de  Drone',
                'ordering': ['-date'],
            },
            bases=('common.sitearticle',),
        ),
        migrations.AddField(
            model_name='dronecomponent',
            name='category',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='drone.dronecomponentcategory', verbose_name='Catégorie'),
        ),
    ]
