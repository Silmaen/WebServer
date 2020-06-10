# -*- coding: utf-8 -*-
"""mysite.views"""
from django.shortcuts import render, get_object_or_404
from .models import Article
from .forms import ContactForm


def home(request):
    articles = Article.objects.filter(categorie=1).order_by('-date')[:10]
    return render(request, "home.html", {'page': "Home", 'derniers_articles': articles})


def about(request):
    return render(request, "about.html", {'page': "About"})


def blog(request):
    articles = Article.objects.filter(categorie__lte=2).order_by('-date')
    return render(request, "blog.html", {'page': "Blog", 'blog_articles': articles})


def media(request):
    articles = Article.objects.filter(categorie=3).order_by('-date')
    return render(request, "media.html", {'page': "Media", 'media_articles': articles})


def lire(request, id, slug):
    article = get_object_or_404(Article, id=id, slug=slug)
    return render(request, 'lire.html', {'article': article})


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
    return render(request, 'contact.html', locals())
