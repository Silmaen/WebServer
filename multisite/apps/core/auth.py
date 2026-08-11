"""Backend d'authentification OIDC pour authentik.

Fait correspondre les groupes authentik aux groupes Django et au niveau du site :
`OIDC_ADMIN_GROUP` → groupe "admins" + niveau Administrateur,
`OIDC_VIEWER_GROUP` → groupe "viewers" + niveau Autorisé.
"""

import logging

from django.conf import settings
from django.contrib.auth.models import Group
from mozilla_django_oidc.auth import OIDCAuthenticationBackend

logger = logging.getLogger("apps")


class OIDCAuthBackend(OIDCAuthenticationBackend):
    """Backend OIDC authentik, avec report des groupes sur le site."""

    def get_username(self, claims):
        """Un nom lisible, et non l'empreinte base64 du `sub`.

        mozilla-django-oidc renvoie par défaut un hachage du sujet, illisible dans
        l'en-tête du site. authentik envoie `preferred_username` ; à défaut on prend
        la partie locale de l'adresse.
        """
        for claim in ("preferred_username", "nickname"):
            value = (claims.get(claim) or "").strip()
            if value:
                return value
        email = (claims.get("email") or "").strip()
        if email:
            return email.split("@", 1)[0]
        return super().get_username(claims)

    def create_user(self, claims):
        """Crée l'utilisateur puis reporte les claims sur son profil."""
        user = super().create_user(claims)
        self._update_user_from_claims(user, claims)
        return user

    def update_user(self, user, claims):
        """Met à jour l'utilisateur existant depuis les claims."""
        self._update_user_from_claims(user, claims)
        return user

    def _update_user_from_claims(self, user, claims):
        """Synchronise le profil et les groupes depuis les claims OIDC."""
        user.first_name = claims.get("given_name", "")
        user.last_name = claims.get("family_name", "")
        user.email = claims.get("email", user.email)

        oidc_groups = claims.get("groups", [])
        admin_group_name = getattr(settings, "OIDC_ADMIN_GROUP", "network-monitor-admins")
        viewer_group_name = getattr(settings, "OIDC_VIEWER_GROUP", "network-monitor-viewers")

        is_admin = admin_group_name in oidc_groups
        is_viewer = viewer_group_name in oidc_groups

        admins_group, _ = Group.objects.get_or_create(name="admins")
        viewers_group, _ = Group.objects.get_or_create(name="viewers")

        # Toujours actif : c'est l'appartenance au groupe qui décide de l'accès.
        user.is_active = True

        # `is_staff` n'est délibérément pas posé ici : le site le dérive de
        # `userprofile.user_level` dans `UserProfile.save()`, donc l'écrire ici serait
        # écrasé juste après. Un seul levier, un seul propriétaire.
        if is_admin:
            user.groups.add(admins_group)
            user.groups.remove(viewers_group)
        elif is_viewer:
            user.groups.add(viewers_group)
            user.groups.remove(admins_group)
        else:
            user.groups.remove(admins_group, viewers_group)
            logger.warning(
                "utilisateur OIDC %s refusé : aucun groupe autorisé (groupes=%s)",
                user.username, oidc_groups,
            )

        user.save()
        self._sync_site_level(user, is_admin, is_viewer)

        logger.info(
            "utilisateur OIDC %s synchronisé : admin=%s, viewer=%s, "
            "groupes OIDC=%s, groupes Django=%s",
            user.username, is_admin, is_viewer,
            oidc_groups, list(user.groups.values_list("name", flat=True)),
        )

    @staticmethod
    def _sync_site_level(user, is_admin, is_viewer):
        """Reporte le groupe authentik sur le niveau d'accès du site.

        La console vérifie les groupes Django, le site vérifie
        `userprofile.user_level` : ne poser que le groupe laissait un administrateur
        authentik au niveau Enregistré, donc en 403 sur les pages visées. Un
        utilisateur d'aucun des deux groupes est laissé où il est, car il peut être
        un membre ordinaire du site public.
        """
        # Importés ici : `common` et `connector` ne sont pas chargés au moment où ce
        # module l'est.
        from common.user_utils import ADMINISTRATEUR, AUTORISE
        from connector.models import UserProfile

        # Créé pour *tout* utilisateur OIDC avant de décider d'un niveau : le context
        # processor de navigation lit le profil de tout utilisateur authentifié, donc
        # un utilisateur sans profil est une erreur 500 sur chaque page.
        profile, _ = UserProfile.objects.get_or_create(user=user)

        if is_admin:
            level = ADMINISTRATEUR
        elif is_viewer:
            level = AUTORISE
        else:
            return

        if profile.user_level != level:
            profile.user_level = level
            profile.save(update_fields=["user_level"])
            logger.info("niveau site de %s porté à %s (groupes authentik)", user.username, level)

    def filter_users_by_claims(self, claims):
        """Retrouve l'utilisateur par son adresse : authentik peut changer le nom."""
        email = claims.get("email")
        if email:
            return self.UserModel.objects.filter(email=email)
        return self.UserModel.objects.none()
