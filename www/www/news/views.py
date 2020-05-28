"""news.views"""
from django.shortcuts import render
from .models import Article
from .models import SysadminSubpages


def index(request):
    """
    Main page
    :param request: the page request
    :return: the rendered page
    """
    if not request.user.is_authenticated:
        articles = Article.objects.filter(categorie=1, needuser=False, ishidden=False).order_by('-date')[:15]
    else:
        if not request.user.has_Hidden_Access:
            articles = Article.objects.filter(categorie=1, ishidden=False).order_by('-date')[:15]
        else:
            articles = Article.objects.filter(categorie=1).order_by('-date')[:15]
    return render(request, "News.html", {"page": "News", 'derniers_articles': articles})


def research(request):
    """
    Research page
    :param request: the page request
    :return: the rendered page
    """
    articles = Article.objects.filter(categorie=2).order_by('-date')[:15]
    return render(request, "Research.html", {"page": "Search", 'derniers_articles': articles})


def projects(request):
    """
    Project page
    :param request: the page request
    :return: the rendered page
    """
    articles = Article.objects.filter(categorie=3).order_by('-date')[:15]
    return render(request, "Projects.html", {"page": "Project", 'derniers_articles': articles})


def links(request):
    """
    Links page
    :param request: the page request
    :return: the rendered page
    """
    articles = Article.objects.filter(categorie=4).order_by('-date')[:15]
    return render(request, "Links.html", {"page": "Links", 'derniers_articles': articles})


def sysadmin(request, name):
    """
    sysadmin page
    :param request: the page request
    :param name: the subpage name
    :return: the rendered page
    """
    try:
        subpages = SysadminSubpages.objects.all()
    except:
        subpages = []
    ok = False
    for page in subpages:
        if page.Url == name:
            ok = True
            name = page.Name
    if not ok:
        name = "General"
    return render(request, "Sysadmin.html", {"page": "Sysadmin", "name": name, "SysadminSubpage": subpages})


def sysadmin_base(request):
    """
    sysadmin main page
    :param request: the page request
    :return: the rendered page
    """
    return sysadmin(request, index)
