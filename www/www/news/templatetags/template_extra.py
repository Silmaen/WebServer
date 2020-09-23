"""news.templatetags.template_extra"""
from django import template

register = template.Library()


@register.filter
def pageSpecificBtn(text, page):
    if text == page:
        return "current-page"
    return ""

@register.filter
def subpageSpecificBtn(text, subpage):
    if text == subpage:
        return "current-subpage"
    return ""
