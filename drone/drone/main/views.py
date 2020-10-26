"""main.views"""
from django.shortcuts import render


def index(request):
    """
    Main Page
    :param request: the page request
    :return: the redered page
    """
    return render(request)
