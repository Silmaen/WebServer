"""news.templatetags.template_extra"""
from django import template

register = template.Library()


@register.filter
def pageSpecificBtn(text, page):
    if text == page:
        return "current"
    return ""
