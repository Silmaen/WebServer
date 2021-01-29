"""La page de view.py"""
from django.shortcuts import render, redirect

from common.user_utils import user_is_moderator
from . import settings
from .render_utils import get_page_data, get_articles, get_article, get_potager_data
from .forms import ArticleCommentForm


def index(request):
    """
    Définition de la page principale.
     :param request : La requête du client.
     :return : La page rendue.
    """
    data = get_page_data(request.user, "news")
    articles = get_articles(request.user, 1)
    return render(request, "www/baseWithArticles.html", {
        **settings.base_info, **data,
        'derniers_articles': articles
    })


def detailed_news(request, article_id):
    """
    :param request:
    :param article_id:
    :return:
    """
    article = get_article(request.user, article_id)
    if not article:
        return redirect("/")
    data = get_page_data(request.user, "news")
    new_comment = None
    # comment posted
    if request.method == "POST":
        comment_form = ArticleCommentForm(data=request.POST)
        if comment_form.is_valid():
            # create an object but don't save to database yet
            new_comment = comment_form.save(commit=False)
            # assign the comment to the current Article
            new_comment.article = article
            # assign the current user to the comment
            new_comment.auteur = request.user
            # mark it as active if the user is in Moderateurs group
            if user_is_moderator(request.user):
                new_comment.active = True
            # save it to database
            new_comment.save()
    else:
        comment_form = ArticleCommentForm()
    return render(request, "www/DetailedArticles.html", {
        **settings.base_info, **data,
        'article': article,
        "new_comment": new_comment,
        "comment_form": comment_form
    })


def research(request):
    """
    Page de recherche.
     :param request : La requête du client.
     :return : La page rendue.
    """
    data = get_page_data(request.user, "research")
    articles = get_articles(request.user, 2)
    return render(request, "www/baseWithArticles.html", {
        **settings.base_info, **data,
        'derniers_articles': articles
    })


def projects(request):
    """
    Page des projets.
     :param request : La requête du client.
     :return : La page rendue.
    """
    data = get_page_data(request.user, "projects")
    articles = get_articles(request.user, 3)
    return render(request, "www/baseWithArticles.html", {
        **settings.base_info, **data,
        'derniers_articles': articles
    })


def links(request):
    """
    Page des liens
     :param request : La requête du client.
     :return : La page rendue.
    """
    data = get_page_data(request.user, "links")
    articles = get_articles(request.user, 4)
    return render(request, "www/baseWithArticles.html", {
        **settings.base_info, **data,
        'derniers_articles': articles
    })


def potager(request):
    """
    Page du potager
     :param request : La requête du client.
     :return : La page rendue.
    """
    data = get_page_data(request.user, "Potager")
    contenu = get_potager_data()
    print(data)
    return render(request, "www/baseWithPotager.html", {
        **settings.base_info, **data,
        "map": contenu
    })