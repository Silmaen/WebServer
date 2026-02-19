"""
Commande Django pour importer les données depuis une base MySQL existante
vers la base SQLite locale.

Usage:
    python manage.py import_from_mysql --host=192.168.5.1 --user=www_common \
        --password=xxx --database=Site_Common
"""
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User

from connector.models import UserProfile
from common.models import SiteArticle, SiteArticleComment
from www.models import Category, SubCategory, Article, ArticleComment


class Command(BaseCommand):
    help = "Importe les données depuis une base MySQL vers la base SQLite locale."

    def add_arguments(self, parser):
        parser.add_argument(
            '--host', default='192.168.5.1',
            help="Hôte MySQL (défaut: 192.168.5.1)",
        )
        parser.add_argument(
            '--port', type=int, default=3306,
            help="Port MySQL (défaut: 3306)",
        )
        parser.add_argument(
            '--user', default='www_common',
            help="Utilisateur MySQL (défaut: www_common)",
        )
        parser.add_argument(
            '--password', required=True,
            help="Mot de passe MySQL",
        )
        parser.add_argument(
            '--database', default='Site_Common',
            help="Nom de la base MySQL (défaut: Site_Common)",
        )

    def handle(self, *args, **options):
        try:
            import pymysql
            pymysql.install_as_MySQLdb()
        except ImportError:
            raise CommandError(
                "Le paquet 'pymysql' est requis pour l'import. "
                "Installez-le avec : pip install pymysql"
            )

        self.stdout.write("Connexion à MySQL...")
        try:
            conn = pymysql.connect(
                host=options['host'],
                port=options['port'],
                user=options['user'],
                password=options['password'],
                database=options['database'],
                charset='utf8mb4',
            )
        except pymysql.Error as e:
            raise CommandError(f"Impossible de se connecter à MySQL : {e}")

        cursor = conn.cursor(pymysql.cursors.DictCursor)
        self.stdout.write(self.style.SUCCESS("Connecté à MySQL."))

        try:
            self._import_users(cursor)
            self._import_userprofiles(cursor)
            self._import_categories(cursor)
            self._import_subcategories(cursor)
            self._import_sitearticles(cursor)
            self._import_articles(cursor)
            self._import_sitearticlecomments(cursor)
            self._import_articlecomments(cursor)
        finally:
            cursor.close()
            conn.close()

        self.stdout.write(self.style.SUCCESS("Import terminé avec succès."))

    def _import_users(self, cursor):
        cursor.execute(
            "SELECT id, password, last_login, is_superuser, username, "
            "first_name, last_name, email, is_staff, is_active, date_joined "
            "FROM auth_user ORDER BY id"
        )
        rows = cursor.fetchall()
        count = 0
        for row in rows:
            if User.objects.filter(pk=row['id']).exists():
                continue
            user = User(
                pk=row['id'],
                password=row['password'],
                last_login=row['last_login'],
                is_superuser=row['is_superuser'],
                username=row['username'],
                first_name=row['first_name'],
                last_name=row['last_name'],
                email=row['email'],
                is_staff=row['is_staff'],
                is_active=row['is_active'],
                date_joined=row['date_joined'],
            )
            # save_base pour éviter les signaux (UserProfile auto-créé par signal)
            user.save_base(raw=True)
            count += 1
        self.stdout.write(f"  auth_user : {count} importé(s) ({len(rows)} total)")

    def _import_userprofiles(self, cursor):
        cursor.execute(
            "SELECT user_id, avatar, birthDate "
            "FROM connector_userprofile ORDER BY user_id"
        )
        rows = cursor.fetchall()
        count = 0
        for row in rows:
            profile, created = UserProfile.objects.update_or_create(
                user_id=row['user_id'],
                defaults={
                    'avatar': row['avatar'] or '',
                    'birthDate': row['birthDate'],
                },
            )
            if created:
                count += 1
        self.stdout.write(f"  connector_userprofile : {count} importé(s) ({len(rows)} total)")

    def _import_categories(self, cursor):
        cursor.execute("SELECT id, nom, mdi_icon_name FROM www_category ORDER BY id")
        rows = cursor.fetchall()
        count = 0
        for row in rows:
            _, created = Category.objects.get_or_create(
                pk=row['id'],
                defaults={
                    'nom': row['nom'],
                    'mdi_icon_name': row['mdi_icon_name'] or '',
                },
            )
            if created:
                count += 1
        self.stdout.write(f"  www_category : {count} importé(s) ({len(rows)} total)")

    def _import_subcategories(self, cursor):
        cursor.execute("SELECT id, nom, mdi_icon_name FROM www_subcategory ORDER BY id")
        rows = cursor.fetchall()
        count = 0
        for row in rows:
            _, created = SubCategory.objects.get_or_create(
                pk=row['id'],
                defaults={
                    'nom': row['nom'],
                    'mdi_icon_name': row['mdi_icon_name'] or '',
                },
            )
            if created:
                count += 1
        self.stdout.write(f"  www_subcategory : {count} importé(s) ({len(rows)} total)")

    def _import_sitearticles(self, cursor):
        cursor.execute(
            "SELECT id, titre, slug, auteur_id, contenu, date, "
            "private, superprivate, staff, developper "
            "FROM common_sitearticle ORDER BY id"
        )
        rows = cursor.fetchall()
        count = 0
        for row in rows:
            if SiteArticle.objects.filter(pk=row['id']).exists():
                continue
            obj = SiteArticle(
                pk=row['id'],
                titre=row['titre'],
                slug=row['slug'],
                auteur_id=row['auteur_id'],
                contenu=row['contenu'] or '',
                date=row['date'],
                private=row['private'],
                superprivate=row['superprivate'],
                staff=row['staff'],
                developper=row['developper'],
            )
            obj.save_base(raw=True)
            count += 1
        self.stdout.write(f"  common_sitearticle : {count} importé(s) ({len(rows)} total)")

    def _import_articles(self, cursor):
        cursor.execute(
            "SELECT sitearticle_ptr_id, categorie_id, sous_categorie_id "
            "FROM www_article ORDER BY sitearticle_ptr_id"
        )
        rows = cursor.fetchall()
        count = 0
        for row in rows:
            if Article.objects.filter(pk=row['sitearticle_ptr_id']).exists():
                continue
            obj = Article(
                sitearticle_ptr_id=row['sitearticle_ptr_id'],
                categorie_id=row['categorie_id'],
                sous_categorie_id=row['sous_categorie_id'],
            )
            # Copier les champs du parent déjà importé
            parent = SiteArticle.objects.get(pk=row['sitearticle_ptr_id'])
            obj.titre = parent.titre
            obj.slug = parent.slug
            obj.auteur_id = parent.auteur_id
            obj.contenu = parent.contenu
            obj.date = parent.date
            obj.private = parent.private
            obj.superprivate = parent.superprivate
            obj.staff = parent.staff
            obj.developper = parent.developper
            obj.save_base(raw=True)
            count += 1
        self.stdout.write(f"  www_article : {count} importé(s) ({len(rows)} total)")

    def _import_sitearticlecomments(self, cursor):
        cursor.execute(
            "SELECT id, article_id, auteur_id, contenu, date, active "
            "FROM common_sitearticlecomment ORDER BY id"
        )
        rows = cursor.fetchall()
        count = 0
        for row in rows:
            if SiteArticleComment.objects.filter(pk=row['id']).exists():
                continue
            obj = SiteArticleComment(
                pk=row['id'],
                article_id=row['article_id'],
                auteur_id=row['auteur_id'],
                contenu=row['contenu'] or '',
                date=row['date'],
                active=row['active'],
            )
            obj.save_base(raw=True)
            count += 1
        self.stdout.write(f"  common_sitearticlecomment : {count} importé(s) ({len(rows)} total)")

    def _import_articlecomments(self, cursor):
        cursor.execute(
            "SELECT sitearticlecomment_ptr_id "
            "FROM www_articlecomment ORDER BY sitearticlecomment_ptr_id"
        )
        rows = cursor.fetchall()
        count = 0
        for row in rows:
            ptr_id = row['sitearticlecomment_ptr_id']
            if ArticleComment.objects.filter(pk=ptr_id).exists():
                continue
            parent = SiteArticleComment.objects.get(pk=ptr_id)
            obj = ArticleComment(
                sitearticlecomment_ptr_id=ptr_id,
                article_id=parent.article_id,
                auteur_id=parent.auteur_id,
                contenu=parent.contenu,
                date=parent.date,
                active=parent.active,
            )
            obj.save_base(raw=True)
            count += 1
        self.stdout.write(f"  www_articlecomment : {count} importé(s) ({len(rows)} total)")
