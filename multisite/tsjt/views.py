"""La definition des vues"""
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from . import settings
from .forms import ContactForm
from .models import tsjtArticle


def index(request):
    """La toute première page"""
    articles = tsjtArticle.objects.filter(categorie=1).order_by('-date')[:10]
    return render(request, "tsjt/home.html", {
        **settings.base_info,
        'page': "Home",
        'derniers_articles': articles
    })


def about(request):
    return render(request, "tsjt/about.html", {
        **settings.base_info,
        'page': "About"
    })


def blog(request):
    articles = tsjtArticle.objects.filter(categorie__lte=2).order_by('-date')
    return render(request, "tsjt/blog.html", {
        **settings.base_info,
        'page': "Blog",
        'blog_articles': articles
    })


def media(request):
    articles = tsjtArticle.objects.filter(categorie=3).order_by('-date')
    return render(request, "tsjt/media.html", {
        **settings.base_info,
        'page': "Media",
        'media_articles': articles
    })


def lire(request, id, slug):
    article = get_object_or_404(tsjtArticle, id=id, slug=slug)
    return render(request, 'tsjt/lire.html', {
        **settings.base_info,
        'article': article
    })


def list_articles(request, year, month=1):
    """ Liste des articles d'un mois précis. """
    return HttpResponse(
        "Vous avez demandé les articles de {0} {1}.".format(month, year)
    )


def list_articles_by_tag(request, tag):
    """ Liste des articles d'un mois précis. """
    return HttpResponse(
        "Vous avez demandé les articles taggués {0}.".format(tag)
    )


def contact(request):
    # Construire le formulaire, soit avec les données postées,
    # soit vide si l'utilisateur accède pour la première fois
    # à la page.
    form = ContactForm(request.POST or None)
    # Nous vérifions que les données envoyées sont valides
    # Cette méthode renvoie False s'il n'y a pas de données
    # dans le formulaire ou qu'il contient des erreurs.
    if form.is_valid():
        # Ici nous pouvons traiter les données du formulaire
        sujet = form.cleaned_data['sujet']
        message = form.cleaned_data['message']
        envoyeur = form.cleaned_data['envoyeur']
        renvoi = form.cleaned_data['renvoi']

        # Nous pourrions ici envoyer l'e-mail grâce aux données
        # que nous venons de récupérer
        envoi = True

    # Quoiqu'il arrive, on affiche la page du formulaire.
    return render(request, 'tsjt/contact.html', locals())
