"""sysadmin.view"""
from news.render_utils import render_page
from .admin_utils import get_ActiveMachine

def index(request):
    return summary(request)


def summary(request):
    return render_page(request, "ServerAdmin", {"subpage": "Etat"})


def mlist(request):
    machines = get_ActiveMachine()
    return render_page(request, "ServerAdmin", {
        "subpage": "Liste Machine",
        "machines": machines
    })

