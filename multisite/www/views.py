"""La page de view.py"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from common.user_utils import user_is_moderator
from . import settings
from .render_utils import get_page_data, get_articles, get_article, get_news_articles
from .forms import ArticleCommentForm


def accueil(request):
    """
    Page d'accueil du site.
     :param request : La requête du client.
     :return : La page rendue.
    """
    data = get_page_data(request.user, "accueil")
    return render(request, "www/accueil.html", {
        **settings.base_info, **data,
    })


def a_propos(request):
    """
    Page à propos.
     :param request : La requête du client.
     :return : La page rendue.
    """
    data = get_page_data(request.user, "a_propos")
    return render(request, "www/a_propos.html", {
        **settings.base_info, **data,
    })


def mes_projets(request):
    """
    Page des projets personnels.
     :param request : La requête du client.
     :return : La page rendue.
    """
    data = get_page_data(request.user, "mes_projets")
    return render(request, "www/mes_projets.html", {
        **settings.base_info, **data,
    })


@login_required
def archives(request):
    """
    Page d'archives principale.
     :param request : La requête du client.
     :return : La page rendue.
    """
    data = get_page_data(request.user, "archives")
    return render(request, "www/archives.html", {
        **settings.base_info, **data,
    })


@login_required
def news(request):
    """
    Page d'archives des news (première page).
     :param request : La requête du client.
     :return : La page rendue.
    """
    return news_page(request, 1)


@login_required
def news_page(request, n_page):
    """
    Définition de la page principale.
     :param request : La requête du client.
     :param n_page : Le numéro de la page.
     :return : La page rendue.
    """
    data = get_page_data(request.user, "archives")
    articles, n_pages = get_news_articles(request.user, n_page)
    return render(request, "www/baseWithArticles.html", {
        **settings.base_info, **data,
        'subpage': 'News',
        'derniers_articles': articles,
        'news_page': n_page,
        'news_pages': n_pages,
    })


@login_required
def detailed_news(request, article_id):
    """
    :param request:
    :param article_id:
    :return:
    """
    article = get_article(request.user, article_id)
    if not article:
        return redirect("archives_news")
    data = get_page_data(request.user, "archives")
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
        'subpage': 'News',
        'article'     : article,
        "new_comment" : new_comment,
        "comment_form": comment_form
    })


@login_required
def bricolage(request):
    """
    Page bricolage (en construction).
     :param request : La requête du client.
     :return : La page rendue.
    """
    data = get_page_data(request.user, "bricolage")
    return render(request, "www/bricolage.html", {
        **settings.base_info, **data,
    })


@login_required
def administration(request):
    """
    Page administration (en construction).
     :param request : La requête du client.
     :return : La page rendue.
    """
    data = get_page_data(request.user, "administration")
    return render(request, "www/administration.html", {
        **settings.base_info, **data,
    })


@login_required
def research(request):
    """
    Page de recherche.
     :param request : La requête du client.
     :return : La page rendue.
    """
    data = get_page_data(request.user, "archives")
    articles = get_articles(request.user, 2)
    return render(request, "www/baseWithArticles.html", {
        **settings.base_info, **data,
        'subpage': 'Recherche',
        'derniers_articles': articles
    })
