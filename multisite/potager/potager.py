"""
Fichier rassemblant les fonctions associées au potager
"""
from typing import Dict, Any


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
    for i in [3, 4, 16, 17, 27, 28]:
        for j in range(3, 20):
            contenu[i][j].css_class = "senti"
    for j in [3, 4, 11, 18, 19]:
        for i in range(3, 29):
            contenu[i][j].css_class = "senti"
    for j in range(3):
        for i in range(14, 18):
            contenu[i][j].css_class = "senti"
    return contenu


def get_potager_detail(row: int, col: int) -> Dict[str, Any]:
    return {
        "Name": "Oignon rouge de florence",
        "Icon": "oignon",
        "X"   : col,
        "Y"   : row,
    }


# helpers pour le potager


def get_potager_data():
    contenu = get_base_frame()
    # tests de plantation
    # # oignons
    for j in range(8):
        for i in range(3):
            contenu[i][j].content_icon = "oignon"
    return contenu
