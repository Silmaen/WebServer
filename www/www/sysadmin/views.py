from news.render_utils import render_page

# Create your views here.

subpages = [
    {"url": "summary", "name": "Summary", "icon": "mdi mdi-home"},
    {"url": "mlist", "name": "Machine list", "icon": "mdi mdi-desk"},
]


def index(request):
    return summary(request)


def summary(request):
    return render_page(request, "ServerAdmin", {"subpage": "Etat"})


def mlist(request):
    return render_page(request, "ServerAdmin", {"subpage": "Liste Machine"})

