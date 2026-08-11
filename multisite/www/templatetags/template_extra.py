"""Filtres de gabarit propres au site www."""
from django import template

register = template.Library()


@register.filter
def pageSpecificBtn(text, page):
    """Rend "current" quand l'entrée de navigation est celle de la page affichée."""
    return "current" if text == page else ""
