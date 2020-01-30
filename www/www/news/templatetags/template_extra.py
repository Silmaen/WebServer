from django import template

register = template.Library()

# @register.filter
# def pageSpecific(text,page):
    # result=text
    # return result

@register.filter
def pageSpecificBtn(text,page):
    if (text == page):
        return "current-page"
    return ""