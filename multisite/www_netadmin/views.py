"""sysadmin.view"""
from django.shortcuts import render

from www.render_utils import get_page_data
from .admin_utils import get_active_machine
from www import settings

subpages = [
    {
        "name": "État",
        "url": "etat",
        "icon": "mdi-home",
        "Active"           : True,
        "NeedUser"         : True,
        "NeedStaff"        : True,
        "NeedDev"          : True,
        "NeedValidatedUser": True,
    },
    {
        "name": "Liste Machine",
        "url": "mlist",
        "icon": "mdi-desk",
        "Active"           : True,
        "NeedUser"         : True,
        "NeedStaff"        : True,
        "NeedDev"          : True,
        "NeedValidatedUser": True,
    },
]


def index(request):
    return summary(request)


def summary(request):
    data = get_page_data(request.user, "netadmin")
    return render(request, "www/sysadminSummary.html", {
        **settings.base_info, **data,
        "subpages": subpages,
        "subpage": "Etat"
    })


def mlist(request):
    machines = get_active_machine()
    data = get_page_data(request.user, "netadmin")
    return render(request, "www/sysadminMachineList.html", {
        **settings.base_info, **data,
        "subpages": subpages,
        "subpage": "Liste Machine",
        "data" : {
            "machines": machines
        }
    })

