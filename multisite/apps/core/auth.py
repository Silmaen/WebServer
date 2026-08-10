"""Custom OIDC authentication backend for Authentik integration.

Maps Authentik groups to Django groups and staff/active status:
- OIDC_ADMIN_GROUP  → Django group "admins", is_staff=True, is_active=True
- OIDC_VIEWER_GROUP → Django group "viewers", is_staff=False, is_active=True
- Neither group     → is_active=False (access denied)
"""

import logging

from django.conf import settings
from django.contrib.auth.models import Group
from mozilla_django_oidc.auth import OIDCAuthenticationBackend

logger = logging.getLogger("apps")


class OIDCAuthBackend(OIDCAuthenticationBackend):
    """Authentik OIDC backend with group mapping."""

    def create_user(self, claims):
        user = super().create_user(claims)
        self._update_user_from_claims(user, claims)
        return user

    def update_user(self, user, claims):
        self._update_user_from_claims(user, claims)
        return user

    def _update_user_from_claims(self, user, claims):
        """Sync user profile and group memberships from OIDC claims."""
        user.first_name = claims.get("given_name", "")
        user.last_name = claims.get("family_name", "")
        user.email = claims.get("email", user.email)

        # Get groups from Authentik claims
        oidc_groups = claims.get("groups", [])
        admin_group_name = getattr(settings, "OIDC_ADMIN_GROUP", "network-monitor-admins")
        viewer_group_name = getattr(settings, "OIDC_VIEWER_GROUP", "network-monitor-viewers")

        is_admin = admin_group_name in oidc_groups
        is_viewer = viewer_group_name in oidc_groups

        admins_group, _ = Group.objects.get_or_create(name="admins")
        viewers_group, _ = Group.objects.get_or_create(name="viewers")

        # Always keep OIDC users active (group check handled by middleware)
        user.is_active = True

        if is_admin:
            user.is_staff = True
            user.groups.add(admins_group)
            user.groups.remove(viewers_group)
        elif is_viewer:
            user.is_staff = False
            user.groups.add(viewers_group)
            user.groups.remove(admins_group)
        else:
            # No authorized group — keep active but no group (middleware will block)
            user.is_staff = False
            user.groups.remove(admins_group, viewers_group)
            logger.warning("OIDC user %s denied: not in any authorized group (groups=%s)", user.username, oidc_groups)

        user.save()
        self._sync_site_level(user, is_admin, is_viewer)

        logger.info(
            "OIDC user %s synced: admin=%s, viewer=%s, expected_admin_group=%s, expected_viewer_group=%s, oidc_groups=%s, django_groups=%s",
            user.username, is_admin, is_viewer,
            admin_group_name, viewer_group_name,
            oidc_groups, list(user.groups.values_list("name", flat=True)),
        )

    @staticmethod
    def _sync_site_level(user, is_admin, is_viewer):
        """Carry the authentik group over to the site's own access level.

        This is the join between two authorisation models that had no reason to know
        about each other until the console moved into the site.

        Django groups and `is_staff` are what the console checks. The site is older
        and checks `userprofile.user_level` (Enregistré / Autorisé / Avancé /
        Administrateur), which is what `@admin_required` on its monitoring page and on
        every one of its admin views tests. Setting only the group left an authentik
        administrator at level *Enregistré*: logged in, in the `admins` group, and 403
        on the very pages they were given the group for.

        So `admin domain` -> Administrateur, `user home` -> Autorisé. A user in
        neither is left where they are: they may well be an ordinary member of the
        public site who also happens to exist in authentik, and demoting them here
        would take away access this backend was never asked to manage.
        """
        from common.user_utils import ADMINISTRATEUR, AUTORISE
        from connector.models import UserProfile

        if is_admin:
            level = ADMINISTRATEUR
        elif is_viewer:
            level = AUTORISE
        else:
            return

        profile, _ = UserProfile.objects.get_or_create(user=user)
        if profile.user_level != level:
            profile.user_level = level
            profile.save(update_fields=["user_level"])
            logger.info("niveau site de %s porté à %s (groupes authentik)", user.username, level)

    def filter_users_by_claims(self, claims):
        """Match existing users by email (Authentik may change usernames)."""
        email = claims.get("email")
        if email:
            return self.UserModel.objects.filter(email=email)
        return self.UserModel.objects.none()
