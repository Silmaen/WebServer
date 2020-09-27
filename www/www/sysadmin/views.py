from django.shortcuts import render

# Create your views here.

subpages = [
    {"url": "summary", "name": "Summary", "icon": "mdi mdi-home"},
    {"url": "mlist", "name": "Machine list", "icon": "mdi mdi-desk"},
]


def index(request):
    return summary(request)


def summary(request):
    return render(request, "baseWithSubPages.html",
                  {"page": "Sysadmin",
                   "page_subtitle": "Administration Système",
                   "subpage": "Summary",
                   "subpages": subpages,
                   })


def mlist(request):
    return render(request, "baseWithSubPages.html",
                  {"page": "Sysadmin",
                   "page_subtitle": "Administration Système",
                   "subpage": "Machine list",
                   "subpages": subpages,
                   })
