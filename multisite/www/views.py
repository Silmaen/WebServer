"""Vues du site www : pages publiques, archives, bricolage, monitoring, administration."""
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import models
from django.http import HttpResponseForbidden, StreamingHttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from apps.fleet.enrich import annotate
from common.user_utils import (
    USER_LEVEL_CHOICES, get_user_level, user_is_administrateur,
    user_is_avance, user_is_moderator,
)

from . import settings
from .forms import (
    ArticleCommentForm, BricolageArticleForm, MachineForm, ProjetCategorieForm,
    ProjetForm, ServeurForm, ServiceCategorieForm,
)
from .models import (
    BricolageArticle, Machine, Projet, ProjetCategorie, Serveur, ServiceCategorie,
)
from .render_utils import get_article, get_articles, get_news_articles, get_page_data


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


def _rendre_formulaire(request, form_class, template, *, subpage, titre, retour,
                       instance=None, succes, fichiers=False):
    """Squelette commun aux formulaires d'administration.

    Les six familles de vues d'administration partagent exactement cette
    mécanique : instancier, valider, enregistrer, rediriger.

     :param form_class : Le formulaire à utiliser.
     :param template : Le gabarit du formulaire.
     :param subpage : La sous-page à surligner dans la navigation.
     :param titre : Le titre affiché au-dessus du formulaire.
     :param retour : Le nom d'URL de la liste, où rediriger après succès.
     :param instance : L'objet à modifier, ou None pour un ajout.
     :param succes : Le message de succès.
     :param fichiers : Vrai si le formulaire accepte des fichiers envoyés.
     :return : La page rendue ou une redirection.
    """
    data = get_page_data(request.user, "administration")
    if request.method == "POST":
        args = (request.POST, request.FILES) if fichiers else (request.POST,)
        form = form_class(*args, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, succes)
            return redirect(retour)
    else:
        form = form_class(instance=instance)
    return render(request, template, {
        **settings.base_info, **data,
        "subpage": subpage,
        "form": form,
        "form_title": titre,
    })


def _supprimer(request, objet, retour, succes):
    """Squelette commun aux suppressions : n'agit que sur un POST.

     :param objet : L'objet à supprimer.
     :param retour : Le nom d'URL de la liste, où rediriger.
     :param succes : Le message de succès.
     :return : Une redirection vers la liste.
    """
    if request.method == "POST":
        messages.success(request, succes)
        objet.delete()
    return redirect(retour)


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
    return render(request, "www/admin_projets.html", {
        **settings.base_info, **data,
        "subpage": "Projets",
        "projets": Projet.objects.select_related("categorie"),
        "categories": ProjetCategorie.objects.all(),
    })


@admin_required
def admin_projet_ajouter(request):
    """
    Formulaire d'ajout de projet.
     :param request : La requête du client.
     :return : La page rendue ou redirection.
    """
    return _rendre_formulaire(
        request, ProjetForm, "www/admin_projet_form.html",
        subpage="Projets", titre="Ajouter un projet", retour="admin_projets",
        succes="Projet ajouté avec succès.", fichiers=True,
    )


@admin_required
def admin_projet_modifier(request, projet_id):
    """
    Formulaire de modification de projet.
     :param request : La requête du client.
     :param projet_id : L'identifiant du projet.
     :return : La page rendue ou redirection.
    """
    projet = get_object_or_404(Projet, pk=projet_id)
    return _rendre_formulaire(
        request, ProjetForm, "www/admin_projet_form.html",
        subpage="Projets", titre=f"Modifier : {projet.titre}", retour="admin_projets",
        instance=projet, succes=f"Projet « {projet.titre} » modifié avec succès.",
        fichiers=True,
    )


@admin_required
def admin_projet_supprimer(request, projet_id):
    """
    Suppression d'un projet (POST uniquement).
     :param request : La requête du client.
     :param projet_id : L'identifiant du projet.
     :return : Redirection vers la liste.
    """
    projet = get_object_or_404(Projet, pk=projet_id)
    return _supprimer(request, projet, "admin_projets", f"Projet « {projet.titre} » supprimé.")


@admin_required
def admin_projet_categorie_ajouter(request):
    """
    Formulaire d'ajout de catégorie de projet.
     :param request : La requête du client.
     :return : La page rendue ou redirection.
    """
    return _rendre_formulaire(
        request, ProjetCategorieForm, "www/admin_projet_categorie_form.html",
        subpage="Projets", titre="Ajouter une catégorie", retour="admin_projets",
        succes="Catégorie ajoutée avec succès.",
    )


@admin_required
def admin_projet_categorie_modifier(request, categorie_id):
    """
    Formulaire de modification de catégorie de projet.
     :param request : La requête du client.
     :param categorie_id : L'identifiant de la catégorie.
     :return : La page rendue ou redirection.
    """
    categorie = get_object_or_404(ProjetCategorie, pk=categorie_id)
    return _rendre_formulaire(
        request, ProjetCategorieForm, "www/admin_projet_categorie_form.html",
        subpage="Projets", titre=f"Modifier : {categorie.nom}", retour="admin_projets",
        instance=categorie, succes=f"Catégorie « {categorie.nom} » modifiée avec succès.",
    )


@admin_required
def admin_projet_categorie_supprimer(request, categorie_id):
    """
    Suppression d'une catégorie de projet (POST uniquement).
     :param request : La requête du client.
     :param categorie_id : L'identifiant de la catégorie.
     :return : Redirection vers la liste.
    """
    categorie = get_object_or_404(ProjetCategorie, pk=categorie_id)
    return _supprimer(
        request, categorie, "admin_projets", f"Catégorie « {categorie.nom} » supprimée.",
    )


@avance_required
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


@avance_required
def news(request):
    """
    Page d'archives des news (première page).
     :param request : La requête du client.
     :return : La page rendue.
    """
    return news_page(request, 1)


@avance_required
def news_page(request, n_page):
    """
    Une page de la liste des news.
     :param request : La requête du client.
     :param n_page : Le numéro de la page.
     :return : La page rendue.
    """
    data = get_page_data(request.user, "archives")
    articles, n_pages = get_news_articles(request.user, n_page)
    return render(request, "www/baseWithArticles.html", {
        **settings.base_info, **data,
        "subpage": "News",
        "derniers_articles": articles,
        "news_page": n_page,
        "news_pages": n_pages,
    })


@avance_required
def detailed_news(request, article_id):
    """
    Page détaillée d'un article, avec son formulaire de commentaire.
     :param request : La requête du client.
     :param article_id : L'identifiant de l'article.
     :return : La page rendue ou une redirection si l'article n'est pas visible.
    """
    article = get_article(request.user, article_id)
    if not article:
        return redirect("archives_news")
    data = get_page_data(request.user, "archives")
    new_comment = None
    if request.method == "POST":
        comment_form = ArticleCommentForm(data=request.POST)
        if comment_form.is_valid():
            new_comment = comment_form.save(commit=False)
            new_comment.article = article
            new_comment.auteur = request.user
            # Un modérateur publie sans passer par la file de modération.
            if user_is_moderator(request.user):
                new_comment.active = True
            new_comment.save()
    else:
        comment_form = ArticleCommentForm()
    return render(request, "www/DetailedArticles.html", {
        **settings.base_info, **data,
        "subpage": "News",
        "article": article,
        "new_comment": new_comment,
        "comment_form": comment_form,
    })


@avance_required
def bricolage(request):
    """
    Page bricolage : liste des articles actifs.
     :param request : La requête du client.
     :return : La page rendue.
    """
    data = get_page_data(request.user, "bricolage")
    return render(request, "www/bricolage.html", {
        **settings.base_info, **data,
        "articles": BricolageArticle.objects.all(),
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
     :param request : La requête du client.
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
     :param request : La requête du client.
     :return : La page rendue ou une redirection après changement de niveau.
    """
    if request.method == "POST":
        user_id = request.POST.get("user_id")
        new_level = request.POST.get("user_level")
        if user_id and new_level is not None:
            target = User.objects.get(pk=user_id)
            # Un superutilisateur ne peut pas être rétrogradé depuis cette page.
            if not target.is_superuser:
                target.userprofile.user_level = int(new_level)
                target.userprofile.save()
        return redirect("admin_users")

    data = get_page_data(request.user, "administration")
    return render(request, "www/admin_users.html", {
        **settings.base_info, **data,
        "subpage": "Utilisateurs",
        "users": User.objects.select_related("userprofile").order_by("username"),
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
    return render(request, "www/admin_bricolages.html", {
        **settings.base_info, **data,
        "subpage": "Bricolages",
        "articles": BricolageArticle.objects.all(),
    })


@admin_required
def admin_bricolage_ajouter(request):
    """
    Formulaire d'ajout d'article de bricolage.
     :param request : La requête du client.
     :return : La page rendue ou redirection.
    """
    return _rendre_formulaire(
        request, BricolageArticleForm, "www/admin_bricolage_form.html",
        subpage="Bricolages", titre="Ajouter un article de bricolage",
        retour="admin_bricolages", succes="Article de bricolage ajouté avec succès.",
    )


@admin_required
def admin_bricolage_modifier(request, article_id):
    """
    Formulaire de modification d'article de bricolage.
     :param request : La requête du client.
     :param article_id : L'identifiant de l'article.
     :return : La page rendue ou redirection.
    """
    article = get_object_or_404(BricolageArticle, pk=article_id)
    return _rendre_formulaire(
        request, BricolageArticleForm, "www/admin_bricolage_form.html",
        subpage="Bricolages", titre=f"Modifier : {article.titre}",
        retour="admin_bricolages", instance=article,
        succes=f"Article « {article.titre} » modifié avec succès.",
    )


@admin_required
def admin_bricolage_supprimer(request, article_id):
    """
    Suppression d'un article de bricolage (POST uniquement).
     :param request : La requête du client.
     :param article_id : L'identifiant de l'article.
     :return : Redirection vers la liste.
    """
    article = get_object_or_404(BricolageArticle, pk=article_id)
    return _supprimer(
        request, article, "admin_bricolages", f"Article « {article.titre} » supprimé.",
    )


@admin_required
def monitoring(request):
    """
    Page de monitoring des machines.
     :param request : La requête du client.
     :return : La page rendue.
    """
    data = get_page_data(request.user, "monitoring")
    categories = ServiceCategorie.objects.prefetch_related("machines")
    # Chaque machine gagne un attribut `.flotte` : ce qu'elle rapporte d'elle-même
    # (uptime, MAJ, dérive, images, stacks), assemblé par apps.fleet.
    categories = annotate(list(categories))
    return render(request, "www/monitoring.html", {
        **settings.base_info, **data,
        "subpage": "Machines",
        "categories": categories,
    })


@admin_required
def monitoring_services(request):
    """
    Page de monitoring des services web.
     :param request : La requête du client.
     :return : La page rendue.
    """
    data = get_page_data(request.user, "monitoring")
    return render(request, "www/monitoring_services.html", {
        **settings.base_info, **data,
        "subpage": "Services",
        "categories": ServiceCategorie.objects.prefetch_related("serveurs"),
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
        "subpage": "Machines",
        "machine": machine,
    })


def _sse_response(generateur):
    """Crée une StreamingHttpResponse SSE à partir d'un générateur."""
    response = StreamingHttpResponse(generateur, content_type="text/event-stream")
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
    # Importé ici : www.tasks charge nmap, absent hors de l'image Docker.
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
        "subpage": "Services",
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
    return render(request, "www/admin_services.html", {
        **settings.base_info, **data,
        "subpage": "Services",
        "machines": Machine.objects.select_related("categorie"),
        "serveurs": Serveur.objects.select_related("categorie"),
        "categories": ServiceCategorie.objects.all(),
    })


@admin_required
def admin_machine_ajouter(request):
    """
    Formulaire d'ajout de machine.
     :param request : La requête du client.
     :return : La page rendue ou redirection.
    """
    return _rendre_formulaire(
        request, MachineForm, "www/admin_machine_form.html",
        subpage="Services", titre="Ajouter une machine", retour="admin_services",
        succes="Machine ajoutée avec succès.",
    )


@admin_required
def admin_machine_modifier(request, machine_id):
    """
    Formulaire de modification de machine.
     :param request : La requête du client.
     :param machine_id : L'identifiant de la machine.
     :return : La page rendue ou redirection.
    """
    machine = get_object_or_404(Machine, pk=machine_id)
    return _rendre_formulaire(
        request, MachineForm, "www/admin_machine_form.html",
        subpage="Services", titre=f"Modifier : {machine.nom}", retour="admin_services",
        instance=machine, succes=f"Machine « {machine.nom} » modifiée avec succès.",
    )


@admin_required
def admin_machine_supprimer(request, machine_id):
    """
    Suppression d'une machine (POST uniquement).
     :param request : La requête du client.
     :param machine_id : L'identifiant de la machine.
     :return : Redirection vers la liste.
    """
    machine = get_object_or_404(Machine, pk=machine_id)
    return _supprimer(
        request, machine, "admin_services", f"Machine « {machine.nom} » supprimée.",
    )


@admin_required
def admin_serveur_ajouter(request):
    """
    Formulaire d'ajout de serveur.
     :param request : La requête du client.
     :return : La page rendue ou redirection.
    """
    return _rendre_formulaire(
        request, ServeurForm, "www/admin_service_form.html",
        subpage="Services", titre="Ajouter un serveur", retour="admin_services",
        succes="Serveur ajouté avec succès.", fichiers=True,
    )


@admin_required
def admin_serveur_modifier(request, serveur_id):
    """
    Formulaire de modification de serveur.
     :param request : La requête du client.
     :param serveur_id : L'identifiant du serveur.
     :return : La page rendue ou redirection.
    """
    serveur = get_object_or_404(Serveur, pk=serveur_id)
    return _rendre_formulaire(
        request, ServeurForm, "www/admin_service_form.html",
        subpage="Services", titre=f"Modifier : {serveur.titre}", retour="admin_services",
        instance=serveur, succes=f"Serveur « {serveur.titre} » modifié avec succès.",
        fichiers=True,
    )


@admin_required
def admin_serveur_supprimer(request, serveur_id):
    """
    Suppression d'un serveur (POST uniquement).
     :param request : La requête du client.
     :param serveur_id : L'identifiant du serveur.
     :return : Redirection vers la liste.
    """
    serveur = get_object_or_404(Serveur, pk=serveur_id)
    return _supprimer(
        request, serveur, "admin_services", f"Serveur « {serveur.titre} » supprimé.",
    )


@admin_required
def admin_service_categorie_ajouter(request):
    """
    Formulaire d'ajout de catégorie de service.
     :param request : La requête du client.
     :return : La page rendue ou redirection.
    """
    return _rendre_formulaire(
        request, ServiceCategorieForm, "www/admin_service_categorie_form.html",
        subpage="Services", titre="Ajouter une catégorie", retour="admin_services",
        succes="Catégorie ajoutée avec succès.",
    )


@admin_required
def admin_service_categorie_modifier(request, categorie_id):
    """
    Formulaire de modification de catégorie de service.
     :param request : La requête du client.
     :param categorie_id : L'identifiant de la catégorie.
     :return : La page rendue ou redirection.
    """
    categorie = get_object_or_404(ServiceCategorie, pk=categorie_id)
    return _rendre_formulaire(
        request, ServiceCategorieForm, "www/admin_service_categorie_form.html",
        subpage="Services", titre=f"Modifier : {categorie.nom}", retour="admin_services",
        instance=categorie, succes=f"Catégorie « {categorie.nom} » modifiée avec succès.",
    )


@admin_required
def admin_service_categorie_supprimer(request, categorie_id):
    """
    Suppression d'une catégorie de service (POST uniquement).
     :param request : La requête du client.
     :param categorie_id : L'identifiant de la catégorie.
     :return : Redirection vers la liste.
    """
    categorie = get_object_or_404(ServiceCategorie, pk=categorie_id)
    return _supprimer(
        request, categorie, "admin_services", f"Catégorie « {categorie.nom} » supprimée.",
    )


def _deplacer_ordre(model_class, pk, direction):
    """
    Échange l'ordre d'un objet avec son voisin.
     :param model_class : Le modèle (doit avoir un champ 'ordre').
     :param pk : L'identifiant de l'objet à déplacer.
     :param direction : 'monter' ou 'descendre'.
    """
    objet = get_object_or_404(model_class, pk=pk)
    if direction == "monter":
        voisin = model_class.objects.filter(ordre__lt=objet.ordre).order_by("-ordre").first()
    else:
        voisin = model_class.objects.filter(ordre__gt=objet.ordre).order_by("ordre").first()
    if voisin:
        objet.ordre, voisin.ordre = voisin.ordre, objet.ordre
        objet.save()
        voisin.save()


@admin_required
def admin_projet_monter(request, projet_id):
    """
    Monte un projet d'un cran dans l'ordre (POST uniquement).
     :param request : La requête du client.
     :param projet_id : L'identifiant du projet.
     :return : Redirection vers la liste.
    """
    if request.method == "POST":
        _deplacer_ordre(Projet, projet_id, "monter")
    return redirect("admin_projets")


@admin_required
def admin_projet_descendre(request, projet_id):
    """
    Descend un projet d'un cran dans l'ordre (POST uniquement).
     :param request : La requête du client.
     :param projet_id : L'identifiant du projet.
     :return : Redirection vers la liste.
    """
    if request.method == "POST":
        _deplacer_ordre(Projet, projet_id, "descendre")
    return redirect("admin_projets")


@admin_required
def admin_projet_categorie_monter(request, categorie_id):
    """
    Monte une catégorie de projet d'un cran dans l'ordre (POST uniquement).
     :param request : La requête du client.
     :param categorie_id : L'identifiant de la catégorie.
     :return : Redirection vers la liste.
    """
    if request.method == "POST":
        _deplacer_ordre(ProjetCategorie, categorie_id, "monter")
    return redirect("admin_projets")


@admin_required
def admin_projet_categorie_descendre(request, categorie_id):
    """
    Descend une catégorie de projet d'un cran dans l'ordre (POST uniquement).
     :param request : La requête du client.
     :param categorie_id : L'identifiant de la catégorie.
     :return : Redirection vers la liste.
    """
    if request.method == "POST":
        _deplacer_ordre(ProjetCategorie, categorie_id, "descendre")
    return redirect("admin_projets")


@admin_required
def admin_service_categorie_monter(request, categorie_id):
    """
    Monte une catégorie de service d'un cran dans l'ordre (POST uniquement).
     :param request : La requête du client.
     :param categorie_id : L'identifiant de la catégorie.
     :return : Redirection vers la liste.
    """
    if request.method == "POST":
        _deplacer_ordre(ServiceCategorie, categorie_id, "monter")
    return redirect("admin_services")


@admin_required
def admin_service_categorie_descendre(request, categorie_id):
    """
    Descend une catégorie de service d'un cran dans l'ordre (POST uniquement).
     :param request : La requête du client.
     :param categorie_id : L'identifiant de la catégorie.
     :return : Redirection vers la liste.
    """
    if request.method == "POST":
        _deplacer_ordre(ServiceCategorie, categorie_id, "descendre")
    return redirect("admin_services")


@avance_required
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
        "subpage": "Recherche",
        "derniers_articles": articles,
    })
