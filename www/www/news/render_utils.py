"""
gathering functions to render pages
"""
from django.shortcuts import render
from .models import ExtPage, WebPage, subWebPage


def render_page(request, page_name, additional_data):
    need_user = False
    need_hidden_access = False
    need_dev_access = False
    if request.user.is_authenticated:
        need_user = True
        if request.user.has_Hidden_Access:
            need_hidden_access = True
        if request.user.has_Developper_Access:
            need_dev_access = True
    print("User infos: " + str(need_user) + str(need_hidden_access) + str(need_dev_access))
    extpages = ExtPage.objects.filter(
        needUser=need_user,
        needDevAccess=need_dev_access,
        needHiddenAccess=need_hidden_access)
    extpages = ExtPage.objects.all()
    pages = WebPage.objects.filter(
        needUser=need_user,
        needDevAccess=need_dev_access,
        needHiddenAccess=need_hidden_access)
    pages = WebPage.objects.all()
    this_page = pages[0]
    for p in pages:
        if p.name == page_name:
            this_page = p
            break
    subpages = subWebPage.objects.filter(
        needUser=need_user,
        needDevAccess=need_dev_access,
        needHiddenAccess=need_hidden_access,
        parent=this_page
    )
    data = this_page.data
    if len(subpages) > 0:
        this_subpage = subpages[0].name
        if "subpage" in additional_data:
            for p in subpages:
                if p.name == additional_data["subpage"]:
                    this_subpage = p.name
                    data.update(p.data)
                    break
    else:
        this_subpage = ""
    data.update(additional_data)
    print("DATA    :" + str(data))
    print("ExtPage :" + str(extpages))
    print("Pages   :" + str(pages))
    print("subpages:" + str(subpages))
    print("Title   :" + str(this_page.title))
    print("Name    :" + str(this_page.name))
    print("Subpage :" + str(this_subpage))
    return render(request, this_page.template, {
        "extpages": extpages,
        "pages": pages,
        "subpages": subpages,
        "page_subtitle": this_page.title,
        "page": this_page.name,
        "subpage": this_subpage,
        "data": data
    })

