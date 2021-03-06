from django.db.models import Q, QuerySet
from django.shortcuts import render, redirect, get_object_or_404

# Create your views here.
from common.user_utils import user_is_moderator
from potager.potager import get_potager_map, get_potager_detail
from . import settings
from .forms import PlantTypeCommentForm, PlantationCommentForm, PlantsFilterForm
from .models import PlantType, Plantation
from django.utils import timezone


def potager(request):
    """
    Page du potager
     :param request : La requête du client.
     :return : La page rendue.
    """
    if request.user.is_authenticated:
        contenu = get_potager_map()
        return render(request, "potager/baseWithPlan.html", {
            **settings.base_info,
            "page": "plan",
            "map": contenu
        })
    else:
        return render(request, "potager/baseWithPlants.html", {
            **settings.base_info,
            "page": "plan", "plants": []
        })


def potager_detail(request, row: int, col: int):
    """
    Page du potager
     :param request : La requête du client.
     :return : La page rendue.
    """
    if not request.user.is_authenticated:
        return redirect("/")
    contenu_map = get_potager_map()
    plantation = get_potager_detail(row, col)
    now = timezone.now().date()
    new_comment = None
    # comment posted
    if request.method == "POST":
        comment_form = PlantationCommentForm(data=request.POST)
        if comment_form.is_valid():
            # create an object but don't save to database yet
            new_comment = comment_form.save(commit=False)
            # assign the comment to the current Article
            new_comment.plantation = plantation
            # assign the current user to the comment
            new_comment.auteur = request.user
            # mark it as active if the user is in Moderateurs group
            if user_is_moderator(request.user):
                new_comment.active = True
            # save it to database
            new_comment.save()
    else:
        comment_form = PlantationCommentForm()

    return render(request, "potager/baseWithPlan.html", {
        **settings.base_info,
        "page": "plan",
        "now": now,
        "map"   : contenu_map,
        "plantation": plantation,
        "new_comment": new_comment,
        "comment_form": comment_form
    })


def semis(request):
    if not request.user.is_authenticated:
        return redirect("/")
    semis = Plantation.objects.exclude(
            semis_status=Plantation.READY
    ).exclude(
            semis_status=Plantation.RECOLTE
    )
    return render(request, "potager/baseWithSemis.html", {
        **settings.base_info,
        "page": "semis",
        "semis": semis
    })


def semis_detail(request, id):
    if not request.user.is_authenticated:
        return redirect("/")
    semi = get_object_or_404(Plantation, pk=id)

    new_comment = None
    # comment posted
    if request.method == "POST":
        comment_form = PlantationCommentForm(data=request.POST)
        if comment_form.is_valid():
            # create an object but don't save to database yet
            new_comment = comment_form.save(commit=False)
            # assign the comment to the current Article
            new_comment.plantation = semi
            # assign the current user to the comment
            new_comment.auteur = request.user
            # mark it as active if the user is in Moderateurs group
            if user_is_moderator(request.user):
                new_comment.active = True
            # save it to database
            new_comment.save()
    else:
        comment_form = PlantationCommentForm()

    return render(request, "potager/detailedWithSemis.html", {
        **settings.base_info,
        "page": "semis",
        "new_comment": new_comment,
        "comment_form": comment_form,
        "semi": semi
    })


def potager_plants(request):
    """
    Vue de la liste des semences
    :param request:
    :return:
    """
    if not request.user.is_authenticated:
        return redirect("/")
    plants = PlantType.objects.order_by('name')
    if request.method == "POST":
        search_form = PlantsFilterForm(data=request.POST)
        if search_form.is_valid():
            nom = search_form.cleaned_data['nom']
            if nom != "":
                plants = plants.filter(name__icontains=nom)
            mois_semi = search_form.cleaned_data['mois_semi']
            if mois_semi != 0:
                plant_list = []
                for plant in plants:
                    if plant.is_code_in_list(int(mois_semi), "semis"):
                        plant_list.append(plant)
                plants = plant_list
    else:
        search_form = PlantsFilterForm()
    return render(request, "potager/baseWithPlants.html", {
        **settings.base_info,
        "page": "semence",
        "plants": plants,
        "search_form": search_form,
    })


def potager_plants_details(request, id):
    if not request.user.is_authenticated:
        return redirect("/")
    plant = get_object_or_404(PlantType, pk=id)
    new_comment = None
    # comment posted
    if request.method == "POST":
        comment_form = PlantTypeCommentForm(data=request.POST)
        if comment_form.is_valid():
            # create an object but don't save to database yet
            new_comment = comment_form.save(commit=False)
            # assign the comment to the current Article
            new_comment.type_plant = plant
            # assign the current user to the comment
            new_comment.auteur = request.user
            # mark it as active if the user is in Moderateurs group
            if user_is_moderator(request.user):
                new_comment.active = True
            # save it to database
            new_comment.save()
    else:
        comment_form = PlantTypeCommentForm()
    return render(request, "potager/detailedWithPlants.html", {
        **settings.base_info,
        "page": "semence",
        "plant": plant,
        "new_comment": new_comment,
        "comment_form": comment_form
    })
