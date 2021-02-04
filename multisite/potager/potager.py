"""
Fichier rassemblant les fonctions associées au potager
"""
from typing import Dict, Any
from django.utils import timezone
from potager.models import Plantation


class casePotager:
    """
    Informations d'affichage du potager
    """
    css_class = "terre"
    content_icon = ""
    X = 0
    Y = 0

    def __init__(self, x: int = 0, y: int = 0):
        self.X = x
        self.Y = y


nb_ligne = 32
nb_col = 23


def get_base_frame():
    contenu = []
    for i in range(nb_ligne):
        ligne = []
        for j in range(nb_col):
            ligne.append(casePotager(j, i))
        contenu.append(ligne)
    # les sentiers
    for i in [3, 4, 15, 16, 27, 28]:
        for j in range(3, 20):
            contenu[i][j].css_class = "senti"
    for j in [3, 4, 11, 18, 19]:
        for i in range(3, 29):
            contenu[i][j].css_class = "senti"
    for j in range(3):
        for i in range(13, 17):
            contenu[i][j].css_class = "senti"
    return contenu


def get_potager_detail(row: int, col: int) -> Dict[str, Any]:
    current_time = timezone.now()
    data = Plantation.objects.exclude(
            Harvested__lt=current_time)
    for d in data:
        if d.is_at_coord(row, col):
            return d
    # retourne le truc par défaut: la case est vide
    return {
        "name": "Oignon rouge de florence",
        "icon": "oignon",
        "CoordX"   : col,
        "CoordY"   : row,
    }


def get_potager_map():
    contenu = get_base_frame()
    current_time = timezone.now()
    data = Plantation.objects.exclude(
            Harvested__lt=current_time)
    for d in data:
        if not d.display_in_potager():
            continue
        coords = d.get_coord_list()
        for cc in coords:
            contenu[cc[1]][cc[0]].content_icon = d.graine.icon
    return contenu
