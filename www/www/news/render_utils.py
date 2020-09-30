"""
gathering functions to render pages
"""
from django.shortcuts import render
from .models import ExtPage, WebPage, subWebPage


def filter_by_credential(user, pages):
    """
    apply filter on a list of pages based on user datz
    :param user: the user data (including its credentials
    :param pages: the lis of page to filter
    :return: the filtered list of pages
    """
    is_user = False
    has_hidden_access = False
    has_dev_access = False
    if user.is_authenticated:
        is_user = True
        if user.has_Hidden_Access:
            has_hidden_access = True
        if user.has_Developper_Access:
            has_dev_access = True
    if not is_user:
        pages = pages.filter(needUser=False, needDevAccess=False, needHiddenAccess=False)
    else:
        if not has_hidden_access:
            pages = pages.filter(needHiddenAccess=False)
        if not has_dev_access:
            pages = pages.filter(needDevAccess=False)
    return pages


def render_page(request, page_name, additional_data):
    extpages = filter_by_credential(request.user, ExtPage.objects.filter(isActive=True))
    pages = filter_by_credential(request.user, WebPage.objects.filter(isActive=True))
    this_page = pages[0]
    for p in pages:
        if p.name == page_name:
            this_page = p
            break
    template = this_page.template
    subpages = filter_by_credential(request.user, subWebPage.objects.filter(isActive=True, parent=this_page))
    data = this_page.data
    if len(subpages) > 0:
        this_subpage = subpages[0].name
        if "subpage" in additional_data:
            for p in subpages:
                if p.name == additional_data["subpage"]:
                    this_subpage = p.name
                    data.update(p.data)
                    if p.template not in [None, ""]:
                        template = p.template
                    break
    else:
        this_subpage = ""
    data.update(additional_data)
    return render(request, template, {
        "extpages": extpages,
        "pages": pages,
        "subpages": subpages,
        "page_subtitle": this_page.title,
        "page": this_page.name,
        "subpage": this_subpage,
        "data": data
    })

