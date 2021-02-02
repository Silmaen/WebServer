from django.shortcuts import render, redirect, get_object_or_404

# Create your views here.
from common.user_utils import user_is_moderator
from potager.potager import get_potager_data, get_potager_detail
from . import settings
from .forms import PlantTypeCommentForm
from .models import PlantType


def potager(request):
    """
    Page du potager
     :param request : La requête du client.
     :return : La page rendue.
    """
    contenu = get_potager_data()
    return render(request, "potager/baseWithPlan.html", {
        **settings.base_info,
        "page": "plan",
        "map": contenu
    })


def potager_detail(request, row: int, col: int):
    """
    Page du potager
     :param request : La requête du client.
     :return : La page rendue.
    """
    if not request.user.is_authenticated:
        return redirect("/")
    contenu = get_potager_data()
    details = get_potager_detail(row, col)
    return render(request, "potager/baseWithPlan.html", {
        **settings.base_info,
        "page": "plan",
        "map"   : contenu,
        "detail": details
    })


def potager_plants(request):
    if request.user.is_authenticated:
        plants = PlantType.objects.order_by('name')
        return render(request, "potager/baseWithPlants.html", {
            **settings.base_info,
            "page": "semence",
            "plants": plants
        })
    else:
        return render(request, "potager/baseWithPlants.html", {
            **settings.base_info,
            "page": "semence", "plants": []
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
