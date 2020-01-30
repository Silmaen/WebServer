from django import template

register = template.Library()

@register.filter
def pageSpecific(text,page):
    result=text
    if text=="background":
        if page=="Home":
            result="background"
        elif page=="About":
            result="about_background"
        elif page=="Blog":
            result="blog_background"
        elif page=="Media":
            result="media_background"
    if text=="showcase":
        if page in ["About","Media"]:
            result="showcase_about"
    return result