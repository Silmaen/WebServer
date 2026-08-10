"""multisite URL Configuration"""
from django.contrib import admin
from django.urls import path, include

from www.urls import urlpatterns as www_patterns

# The console lives under /console/, so the public site keeps every URL it had --
# argawaen.net is a CV and some projects first, and the lab's operational surface is
# something you reach only after logging in. See _ops/docs/console-merge.md in
# home-server-stacks.
console_patterns = [
    path('', include('apps.dashboard.urls')),
    path('fleet/', include('apps.fleet.urls')),
    path('devices/', include('apps.devices.urls')),
    path('networks/', include('apps.network.urls')),
    path('monitoring/', include('apps.monitoring.urls')),
    path('', include('apps.core.urls')),
]

urlpatterns = www_patterns + [
    path('profile/', include('connector.urls')),
    path('console/', include(console_patterns)),
    # Bearer-token endpoints the machines POST to. Deliberately outside the DRF
    # defaults above, whose permission demands a logged-in viewer: a shell script on
    # a systemd timer cannot follow an SSO redirect.
    path('api/fleet/', include('apps.fleet.api_urls')),
    path('api/', include('apps.api.urls')),
    path('oidc/', include('mozilla_django_oidc.urls')),
    path('admin/', admin.site.urls),
    path('markdownx/', include('markdownx.urls')),
]
