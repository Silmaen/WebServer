"""La page de view.py"""
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import models
from django.http import HttpResponseForbidden, StreamingHttpResponse
from django.shortcuts import render, redirect, get_object_or_404

from common.user_utils import (
    get_user_level, user_is_moderator, user_is_avance, user_is_administrateur,
    USER_LEVEL_CHOICES, ADMINISTRATEUR,
)
from . import settings
from .models import ProjetCategorie, Projet, BricolageArticle, ServiceCategorie, Machine, Serveur
from .render_utils import get_page_data, get_articles, get_article, get_news_articles
from .forms import (
    ArticleCommentForm, ProjetCategorieForm, ProjetForm, BricolageArticleForm,
    ServiceCategorieForm, MachineForm, ServeurForm,
)


def avance_required(view_func):
    """Décorateur : login requis + niveau avancé minimum, sinon 403."""
    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        if not user_is_avance(request.user):
            return HttpResponseForbidden()
        return view_func(request, *args, **kwargs)
    return _wrapped


def admin_required(view_func):
    """Décorateur : login requis + niveau administrateur, sinon 403."""
    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        if not user_is_administrateur(request.user):
            return HttpResponseForbidden()
        return view_func(request, *args, **kwargs)
    return _wrapped


def accueil(request):
    """
    Page d'accueil du site.
     :param request : La requ\u00eate du client.
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


def a_propos_cv(request):
    """
    Sous-page CV.
     :param request : La requête du client.
     :return : La page rendue.
    """
    data = get_page_data(request.user, "a_propos")
    return render(request, "www/a_propos_cv.html", {
        **settings.base_info, **data,
        "subpage": "CV",
    })


def a_propos_publications(request):
    """
    Sous-page Publications.
     :param request : La requête du client.
     :return : La page rendue.
    """
    data = get_page_data(request.user, "a_propos")
    return render(request, "www/a_propos_publications.html", {
        **settings.base_info, **data,
        "subpage": "Publications",
    })


def mes_projets(request):
    """
    Page des projets personnels.
     :param request : La requête du client.
     :return : La page rendue.
    """
    data = get_page_data(request.user, "mes_projets")
    niveau = get_user_level(request.user)
    categories = ProjetCategorie.objects.prefetch_related(
        models.Prefetch("projets", queryset=Projet.objects.filter(
            actif=True, visibilite__lte=niveau))
    )
    return render(request, "www/mes_projets.html", {
        **settings.base_info, **data,
        "categories": categories,
    })


def mes_projets_categorie(request, slug):
    """
    Page des projets d'une catégorie.
     :param request : La requête du client.
     :param slug : Le slug de la catégorie.
     :return : La page rendue.
    """
    categorie = get_object_or_404(ProjetCategorie, slug=slug)
    data = get_page_data(request.user, "mes_projets")
    niveau = get_user_level(request.user)
    projets = categorie.projets.filter(actif=True, visibilite__lte=niveau)
    return render(request, "www/mes_projets_categorie.html", {
        **settings.base_info, **data,
        "subpage": categorie.nom,
        "categorie": categorie,
        "projets": projets,
    })


def mes_projets_detail(request, slug):
    """
    Page détaillée d'un projet.
     :param request : La requête du client.
     :param slug : Le slug du projet.
     :return : La page rendue.
    """
    niveau = get_user_level(request.user)
    projet = get_object_or_404(Projet, slug=slug, actif=True, visibilite__lte=niveau)
    data = get_page_data(request.user, "mes_projets")
    return render(request, "www/mes_projets_detail.html", {
        **settings.base_info, **data,
        "subpage": projet.categorie.nom,
        "projet": projet,
    })


@admin_required
def admin_projets(request):
    """
    Page d'administration des projets.
     :param request : La requête du client.
     :return : La page rendue.
    """
    data = get_page_data(request.user, "administration")
    projets = Projet.objects.select_related("categorie")
    categories = ProjetCategorie.objects.all()
    return render(request, "www/admin_projets.html", {
        **settings.base_info, **data,
        "subpage": "Projets",
        "projets": projets,
        "categories": categories,
    })


@admin_required
def admin_projet_ajouter(request):
    """
    Formulaire d'ajout de projet.
     :param request : La requête du client.
     :return : La page rendue ou redirection.
    """
    data = get_page_data(request.user, "administration")
    if request.method == "POST":
        form = ProjetForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Projet ajouté avec succès.")
            return redirect("admin_projets")
    else:
        form = ProjetForm()
    return render(request, "www/admin_projet_form.html", {
        **settings.base_info, **data,
        "subpage": "Projets",
        "form": form,
        "form_title": "Ajouter un projet",
    })


@admin_required
def admin_projet_modifier(request, projet_id):
    """
    Formulaire de modification de projet.
     :param request : La requête du client.
     :param projet_id : L'identifiant du projet.
     :return : La page rendue ou redirection.
    """
    projet = get_object_or_404(Projet, pk=projet_id)
    data = get_page_data(request.user, "administration")
    if request.method == "POST":
        form = ProjetForm(request.POST, request.FILES, instance=projet)
        if form.is_valid():
            form.save()
            messages.success(request, f"Projet « {projet.titre} » modifié avec succès.")
            return redirect("admin_projets")
    else:
        form = ProjetForm(instance=projet)
    return render(request, "www/admin_projet_form.html", {
        **settings.base_info, **data,
        "subpage": "Projets",
        "form": form,
        "form_title": f"Modifier : {projet.titre}",
    })


@admin_required
def admin_projet_supprimer(request, projet_id):
    """
    Suppression d'un projet (POST uniquement).
     :param request : La requête du client.
     :param projet_id : L'identifiant du projet.
     :return : Redirection vers la liste.
    """
    projet = get_object_or_404(Projet, pk=projet_id)
    if request.method == "POST":
        messages.success(request, f"Projet « {projet.titre} » supprimé.")
        projet.delete()
    return redirect("admin_projets")


@admin_required
def admin_projet_categorie_ajouter(request):
    """
    Formulaire d'ajout de catégorie de projet.
     :param request : La requête du client.
     :return : La page rendue ou redirection.
    """
    data = get_page_data(request.user, "administration")
    if request.method == "POST":
        form = ProjetCategorieForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Catégorie ajoutée avec succès.")
            return redirect("admin_projets")
    else:
        form = ProjetCategorieForm()
    return render(request, "www/admin_projet_categorie_form.html", {
        **settings.base_info, **data,
        "subpage": "Projets",
        "form": form,
        "form_title": "Ajouter une catégorie",
    })


@admin_required
def admin_projet_categorie_modifier(request, categorie_id):
    """
    Formulaire de modification de catégorie de projet.
     :param request : La requête du client.
     :param categorie_id : L'identifiant de la catégorie.
     :return : La page rendue ou redirection.
    """
    categorie = get_object_or_404(ProjetCategorie, pk=categorie_id)
    data = get_page_data(request.user, "administration")
    if request.method == "POST":
        form = ProjetCategorieForm(request.POST, instance=categorie)
        if form.is_valid():
            form.save()
            messages.success(request, f"Catégorie « {categorie.nom} » modifiée avec succès.")
            return redirect("admin_projets")
    else:
        form = ProjetCategorieForm(instance=categorie)
    return render(request, "www/admin_projet_categorie_form.html", {
        **settings.base_info, **data,
        "subpage": "Projets",
        "form": form,
        "form_title": f"Modifier : {categorie.nom}",
    })


@admin_required
def admin_projet_categorie_supprimer(request, categorie_id):
    """
    Suppression d'une catégorie de projet (POST uniquement).
     :param request : La requête du client.
     :param categorie_id : L'identifiant de la catégorie.
     :return : Redirection vers la liste.
    """
    categorie = get_object_or_404(ProjetCategorie, pk=categorie_id)
    if request.method == "POST":
        messages.success(request, f"Catégorie « {categorie.nom} » supprimée.")
        categorie.delete()
    return redirect("admin_projets")


@avance_required
def archives(request):
    """
    Page d'archives principale.
     :param request : La requ\u00eate du client.
     :return : La page rendue.
    """
    data = get_page_data(request.user, "archives")
    return render(request, "www/archives.html", {
        **settings.base_info, **data,
    })


@avance_required
def news(request):
    """
    Page d'archives des news (premi\u00e8re page).
     :param request : La requ\u00eate du client.
     :return : La page rendue.
    """
    return news_page(request, 1)


@avance_required
def news_page(request, n_page):
    """
    D\u00e9finition de la page principale.
     :param request : La requ\u00eate du client.
     :param n_page : Le num\u00e9ro de la page.
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


@avance_required
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


@avance_required
def bricolage(request):
    """
    Page bricolage : liste des articles actifs.
     :param request : La requête du client.
     :return : La page rendue.
    """
    data = get_page_data(request.user, "bricolage")
    articles = BricolageArticle.objects.all()
    return render(request, "www/bricolage.html", {
        **settings.base_info, **data,
        "articles": articles,
    })


@avance_required
def bricolage_detail(request, slug):
    """
    Page détaillée d'un article de bricolage.
     :param request : La requête du client.
     :param slug : Le slug de l'article.
     :return : La page rendue.
    """
    article = get_object_or_404(BricolageArticle, slug=slug)
    data = get_page_data(request.user, "bricolage")
    return render(request, "www/bricolage_detail.html", {
        **settings.base_info, **data,
        "article": article,
    })


@admin_required
def administration(request):
    """
    Page administration.
     :param request : La requ\u00eate du client.
     :return : La page rendue.
    """
    data = get_page_data(request.user, "administration")
    return render(request, "www/administration.html", {
        **settings.base_info, **data,
    })


@admin_required
def admin_users(request):
    """
    Page de gestion des utilisateurs.
     :param request : La requ\u00eate du client.
     :return : La page rendue.
    """
    if request.method == "POST":
        user_id = request.POST.get("user_id")
        new_level = request.POST.get("user_level")
        if user_id and new_level is not None:
            target = User.objects.get(pk=user_id)
            if not target.is_superuser:
                target.userprofile.user_level = int(new_level)
                target.userprofile.save()
        return redirect("admin_users")

    users = User.objects.select_related("userprofile").order_by("username")
    data = get_page_data(request.user, "administration")
    return render(request, "www/admin_users.html", {
        **settings.base_info, **data,
        "subpage": "Utilisateurs",
        "users": users,
        "level_choices": USER_LEVEL_CHOICES,
    })


@admin_required
def admin_bricolages(request):
    """
    Page d'administration des articles de bricolage.
     :param request : La requête du client.
     :return : La page rendue.
    """
    data = get_page_data(request.user, "administration")
    articles = BricolageArticle.objects.all()
    return render(request, "www/admin_bricolages.html", {
        **settings.base_info, **data,
        "subpage": "Bricolages",
        "articles": articles,
    })


@admin_required
def admin_bricolage_ajouter(request):
    """
    Formulaire d'ajout d'article de bricolage.
     :param request : La requête du client.
     :return : La page rendue ou redirection.
    """
    data = get_page_data(request.user, "administration")
    if request.method == "POST":
        form = BricolageArticleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Article de bricolage ajouté avec succès.")
            return redirect("admin_bricolages")
    else:
        form = BricolageArticleForm()
    return render(request, "www/admin_bricolage_form.html", {
        **settings.base_info, **data,
        "subpage": "Bricolages",
        "form": form,
        "form_title": "Ajouter un article de bricolage",
    })


@admin_required
def admin_bricolage_modifier(request, article_id):
    """
    Formulaire de modification d'article de bricolage.
     :param request : La requête du client.
     :param article_id : L'identifiant de l'article.
     :return : La page rendue ou redirection.
    """
    article = get_object_or_404(BricolageArticle, pk=article_id)
    data = get_page_data(request.user, "administration")
    if request.method == "POST":
        form = BricolageArticleForm(request.POST, instance=article)
        if form.is_valid():
            form.save()
            messages.success(request, f"Article « {article.titre} » modifié avec succès.")
            return redirect("admin_bricolages")
    else:
        form = BricolageArticleForm(instance=article)
    return render(request, "www/admin_bricolage_form.html", {
        **settings.base_info, **data,
        "subpage": "Bricolages",
        "form": form,
        "form_title": f"Modifier : {article.titre}",
    })


@admin_required
def admin_bricolage_supprimer(request, article_id):
    """
    Suppression d'un article de bricolage (POST uniquement).
     :param request : La requête du client.
     :param article_id : L'identifiant de l'article.
     :return : Redirection vers la liste.
    """
    article = get_object_or_404(BricolageArticle, pk=article_id)
    if request.method == "POST":
        messages.success(request, f"Article « {article.titre} » supprimé.")
        article.delete()
    return redirect("admin_bricolages")


@admin_required
def monitoring(request):
    """
    Page de monitoring des machines et serveurs.
     :param request : La requête du client.
     :return : La page rendue.
    """
    data = get_page_data(request.user, "monitoring")
    categories = ServiceCategorie.objects.prefetch_related("machines", "serveurs")
    return render(request, "www/monitoring.html", {
        **settings.base_info, **data,
        "categories": categories,
    })


@admin_required
def monitoring_machine_detail(request, machine_id):
    """
    Page de détail d'une machine avec scan à la demande.
     :param request : La requête du client.
     :param machine_id : L'identifiant de la machine.
     :return : La page rendue.
    """
    machine = get_object_or_404(Machine, pk=machine_id)
    data = get_page_data(request.user, "monitoring")
    return render(request, "www/machine_detail.html", {
        **settings.base_info, **data,
        "subpage": machine.nom,
        "machine": machine,
    })


def _sse_response(generateur):
    """Crée une StreamingHttpResponse SSE à partir d'un générateur."""
    response = StreamingHttpResponse(
        generateur, content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response


@admin_required
def machine_ping_sse(request, machine_id):
    """
    Endpoint SSE : vérifie la connectivité d'une machine.
     :param request : La requête du client.
     :param machine_id : L'identifiant de la machine.
     :return : Réponse SSE streaming.
    """
    from .tasks import scanner_ping
    get_object_or_404(Machine, pk=machine_id)
    return _sse_response(scanner_ping(machine_id))


@admin_required
def machine_ports_sse(request, machine_id):
    """
    Endpoint SSE : scanne les ports ouverts d'une machine.
     :param request : La requête du client.
     :param machine_id : L'identifiant de la machine.
     :return : Réponse SSE streaming.
    """
    from .tasks import scanner_ports
    get_object_or_404(Machine, pk=machine_id)
    return _sse_response(scanner_ports(machine_id))



@admin_required
def monitoring_serveur_detail(request, serveur_id):
    """
    Page de détail d'un serveur avec vérification à la demande.
     :param request : La requête du client.
     :param serveur_id : L'identifiant du serveur.
     :return : La page rendue.
    """
    serveur = get_object_or_404(Serveur, pk=serveur_id)
    data = get_page_data(request.user, "monitoring")
    return render(request, "www/serveur_detail.html", {
        **settings.base_info, **data,
        "subpage": serveur.titre,
        "serveur": serveur,
    })


@admin_required
def serveur_check_sse(request, serveur_id):
    """
    Endpoint SSE : vérifie l'état d'un serveur.
     :param request : La requête du client.
     :param serveur_id : L'identifiant du serveur.
     :return : Réponse SSE streaming.
    """
    from .tasks import scanner_serveur
    get_object_or_404(Serveur, pk=serveur_id)
    return _sse_response(scanner_serveur(serveur_id))


@admin_required
def admin_services(request):
    """
    Page d'administration des machines, serveurs et catégories.
     :param request : La requête du client.
     :return : La page rendue.
    """
    data = get_page_data(request.user, "administration")
    machines = Machine.objects.select_related("categorie")
    serveurs = Serveur.objects.select_related("categorie")
    categories = ServiceCategorie.objects.all()
    return render(request, "www/admin_services.html", {
        **settings.base_info, **data,
        "subpage": "Services",
        "machines": machines,
        "serveurs": serveurs,
        "categories": categories,
    })


@admin_required
def admin_machine_ajouter(request):
    """
    Formulaire d'ajout de machine.
     :param request : La requête du client.
     :return : La page rendue ou redirection.
    """
    data = get_page_data(request.user, "administration")
    if request.method == "POST":
        form = MachineForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Machine ajoutée avec succès.")
            return redirect("admin_services")
    else:
        form = MachineForm()
    return render(request, "www/admin_machine_form.html", {
        **settings.base_info, **data,
        "subpage": "Services",
        "form": form,
        "form_title": "Ajouter une machine",
    })


@admin_required
def admin_machine_modifier(request, machine_id):
    """
    Formulaire de modification de machine.
     :param request : La requête du client.
     :param machine_id : L'identifiant de la machine.
     :return : La page rendue ou redirection.
    """
    machine = get_object_or_404(Machine, pk=machine_id)
    data = get_page_data(request.user, "administration")
    if request.method == "POST":
        form = MachineForm(request.POST, instance=machine)
        if form.is_valid():
            form.save()
            messages.success(request, f"Machine « {machine.nom} » modifiée avec succès.")
            return redirect("admin_services")
    else:
        form = MachineForm(instance=machine)
    return render(request, "www/admin_machine_form.html", {
        **settings.base_info, **data,
        "subpage": "Services",
        "form": form,
        "form_title": f"Modifier : {machine.nom}",
    })


@admin_required
def admin_machine_supprimer(request, machine_id):
    """
    Suppression d'une machine (POST uniquement).
     :param request : La requête du client.
     :param machine_id : L'identifiant de la machine.
     :return : Redirection vers la liste.
    """
    machine = get_object_or_404(Machine, pk=machine_id)
    if request.method == "POST":
        messages.success(request, f"Machine « {machine.nom} » supprimée.")
        machine.delete()
    return redirect("admin_services")


@admin_required
def admin_serveur_ajouter(request):
    """
    Formulaire d'ajout de serveur.
     :param request : La requête du client.
     :return : La page rendue ou redirection.
    """
    data = get_page_data(request.user, "administration")
    if request.method == "POST":
        form = ServeurForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Serveur ajouté avec succès.")
            return redirect("admin_services")
    else:
        form = ServeurForm()
    return render(request, "www/admin_service_form.html", {
        **settings.base_info, **data,
        "subpage": "Services",
        "form": form,
        "form_title": "Ajouter un serveur",
    })


@admin_required
def admin_serveur_modifier(request, serveur_id):
    """
    Formulaire de modification de serveur.
     :param request : La requête du client.
     :param serveur_id : L'identifiant du serveur.
     :return : La page rendue ou redirection.
    """
    serveur = get_object_or_404(Serveur, pk=serveur_id)
    data = get_page_data(request.user, "administration")
    if request.method == "POST":
        form = ServeurForm(request.POST, request.FILES, instance=serveur)
        if form.is_valid():
            form.save()
            messages.success(request, f"Serveur « {serveur.titre} » modifié avec succès.")
            return redirect("admin_services")
    else:
        form = ServeurForm(instance=serveur)
    return render(request, "www/admin_service_form.html", {
        **settings.base_info, **data,
        "subpage": "Services",
        "form": form,
        "form_title": f"Modifier : {serveur.titre}",
    })


@admin_required
def admin_serveur_supprimer(request, serveur_id):
    """
    Suppression d'un serveur (POST uniquement).
     :param request : La requête du client.
     :param serveur_id : L'identifiant du serveur.
     :return : Redirection vers la liste.
    """
    serveur = get_object_or_404(Serveur, pk=serveur_id)
    if request.method == "POST":
        messages.success(request, f"Serveur « {serveur.titre} » supprimé.")
        serveur.delete()
    return redirect("admin_services")


@admin_required
def admin_service_categorie_ajouter(request):
    """
    Formulaire d'ajout de catégorie de service.
     :param request : La requête du client.
     :return : La page rendue ou redirection.
    """
    data = get_page_data(request.user, "administration")
    if request.method == "POST":
        form = ServiceCategorieForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Catégorie ajoutée avec succès.")
            return redirect("admin_services")
    else:
        form = ServiceCategorieForm()
    return render(request, "www/admin_service_categorie_form.html", {
        **settings.base_info, **data,
        "subpage": "Services",
        "form": form,
        "form_title": "Ajouter une catégorie",
    })


@admin_required
def admin_service_categorie_modifier(request, categorie_id):
    """
    Formulaire de modification de catégorie de service.
     :param request : La requête du client.
     :param categorie_id : L'identifiant de la catégorie.
     :return : La page rendue ou redirection.
    """
    categorie = get_object_or_404(ServiceCategorie, pk=categorie_id)
    data = get_page_data(request.user, "administration")
    if request.method == "POST":
        form = ServiceCategorieForm(request.POST, instance=categorie)
        if form.is_valid():
            form.save()
            messages.success(request, f"Catégorie « {categorie.nom} » modifiée avec succès.")
            return redirect("admin_services")
    else:
        form = ServiceCategorieForm(instance=categorie)
    return render(request, "www/admin_service_categorie_form.html", {
        **settings.base_info, **data,
        "subpage": "Services",
        "form": form,
        "form_title": f"Modifier : {categorie.nom}",
    })


@admin_required
def admin_service_categorie_supprimer(request, categorie_id):
    """
    Suppression d'une catégorie de service (POST uniquement).
     :param request : La requête du client.
     :param categorie_id : L'identifiant de la catégorie.
     :return : Redirection vers la liste.
    """
    categorie = get_object_or_404(ServiceCategorie, pk=categorie_id)
    if request.method == "POST":
        messages.success(request, f"Catégorie « {categorie.nom} » supprimée.")
        categorie.delete()
    return redirect("admin_services")


@avance_required
def research(request):
    """
    Page de recherche.
     :param request : La requ\u00eate du client.
     :return : La page rendue.
    """
    data = get_page_data(request.user, "archives")
    articles = get_articles(request.user, 2)
    return render(request, "www/baseWithArticles.html", {
        **settings.base_info, **data,
        'subpage': 'Recherche',
        'derniers_articles': articles
    })
