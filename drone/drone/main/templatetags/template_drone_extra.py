"""news.templatetags.template_extra"""
from django import template

register = template.Library()


@register.simple_tag
def getunit(text):
    if text == "Prix":
        return "€"
    if text in ["Largeur", "Longueur", "Hauteur"]:
        return "mm"
    if text == "Poids":
        return "g"
    return ""
