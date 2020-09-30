"""news.views"""
from .models import Article
from .render_utils import render_page


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
    return render_page(request, "News", {'derniers_articles': articles})


def research(request):
    """
    Research page
    :param request: the page request
    :return: the rendered page
    """
    articles = Article.objects.filter(categorie=2).order_by('-date')[:15]
    return render_page(request, "Research", {'derniers_articles': articles})


def projects(request):
    """
    Project page
    :param request: the page request
    :return: the rendered page
    """
    articles = Article.objects.filter(categorie=3).order_by('-date')[:15]
    return render_page(request, "Projets", {'derniers_articles': articles})


def links(request):
    """
    Links page
    :param request: the page request
    :return: the rendered page
    """
    articles = Article.objects.filter(categorie=4).order_by('-date')[:15]
    return render_page(request, "Links", {'derniers_articles': articles})
