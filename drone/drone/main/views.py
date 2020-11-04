"""main.views"""
from django.contrib.auth.views import PasswordResetView
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.urls import reverse
from .forms import *
from django.core import mail

def index(request):
    """
    Main Page
    :param request: the page request
    :return: the rendered page
    """
    mail.get_connection()
    if request.user.is_authenticated:
        articles = Article.objects.order_by('-date')[:15]
        return render(request, "BaseArticles.html", {"page": "news", "articles": articles})
    else:
        return render(request, "BaseArticles.html", {"page": "news", "articles": []})


def detailed_article(request, article_id):
    """
    page for one article with details
    :param request: the page request
    :param article_id: the id of the article to find
    :return: the rendered page
    """
    if not request.user.is_authenticated:
        return redirect("/")
    article = get_object_or_404(Article, pk=article_id)
    new_comment = None
    # comment posted
    if request.method == "POST":
        comment_form = ArticleCommentForm(data=request.POST)
        if comment_form.is_valid():
            # create an object but don't save to database yet
            new_comment = comment_form.save(commit=False)
            # assign the comment to the current Article
            new_comment.article = article
            # assign the current user to the comment
            new_comment.user = request.user
            # mark it as active if the user is in Moderateurs group
            if request.user.groups.filter(name__in=["Moderateurs"]).exists():
                new_comment.active = True
            # save it to database
            new_comment.save()
    else:
        comment_form = ArticleCommentForm()
    return render(request, "DetailedArticle.html", {
        "page": "news",
        "article": article,
        "new_comment": new_comment,
        "comment_form": comment_form
    })


def vols(request):
    """
    Main Page
    :param request: the page request
    :return: the rendered page
    """
    if not request.user.is_authenticated:
        return redirect("/")
    df = DroneFlight.objects.order_by("-date")
    return render(request, "BaseFlight.html", {"page": "vols", "vols": df})


def detailed_vol(request, vol_id):
    """
    page for one article with details
    :param request: the page request
    :param vol_id: the id of the flight to find
    :return: the rendered page
    """
    if not request.user.is_authenticated:
        return redirect("/")
    vol = get_object_or_404(DroneFlight, pk=vol_id)
    new_comment = None
    # comment posted
    if request.method == "POST":
        comment_form = DroneFlightCommentForm(data=request.POST)
        if comment_form.is_valid():
            # create an object but don't save to database yet
            new_comment = comment_form.save(commit=False)
            # assign the comment to the current Article
            new_comment.article = vol
            # assign the current user to the comment
            new_comment.user = request.user
            # mark it as active if the user is in Moderateurs group
            if request.user.groups.filter(name__in=["Moderateurs"]).exists():
                new_comment.active = True
            # save it to database
            new_comment.save()
    else:
        comment_form = DroneFlightCommentForm()
    return render(request, "DetailedFlight.html", {
        "page": "vols",
        "vol": vol,
        "new_comment": new_comment,
        "comment_form": comment_form
    })


def configurations(request):
    """
    Main Page
    :param request: the page request
    :return: the rendered page
    """
    if not request.user.is_authenticated:
        return redirect("/")
    dc = DroneConfiguration.objects.order_by('-version_number')
    return render(request, "BaseConfiguration.html", {"page": "confs", "configurations": dc})


def detailed_configuration(request, conf_id):
    """
    page for one article with details
    :param request: the page request
    :param conf_id: the id of the article to find
    :return: the rendered page
    """
    if not request.user.is_authenticated:
        return redirect("/")
    dc = get_object_or_404(DroneConfiguration, pk=conf_id)
    new_comment = None
    # comment posted
    if request.method == "POST":
        comment_form = DroneConfigurationCommentForm(data=request.POST)
        if comment_form.is_valid():
            # create an object but don't save to database yet
            new_comment = comment_form.save(commit=False)
            # assign the comment to the current Article
            new_comment.article = dc
            # assign the current user to the comment
            new_comment.user = request.user
            # mark it as active if the user is in Moderateurs group
            if request.user.groups.filter(name__in=["Moderateurs"]).exists():
                new_comment.active = True
            # save it to database
            new_comment.save()
    else:
        comment_form = DroneConfigurationCommentForm()
    return render(request, "DetailedConfiguration.html", {
        "page": "confs",
        "conf": dc,
        "new_comment": new_comment,
        "comment_form": comment_form
    })


def composants(request):
    """
    Main Page
    :param request: the page request
    :return: the rendered page
    """
    if not request.user.is_authenticated:
        return redirect("/")
    dc = DroneComponent.objects.order_by("name")
    return render(request, "BaseComposants.html", {"page": "comps", "composants": dc})


def detailed_composant(request, comp_id):
    """
    page for one article with details
    :param request: the page request
    :param comp_id: the id of the article to find
    :return: the rendered page
    """
    if not request.user.is_authenticated:
        return redirect("/")
    dc = get_object_or_404(DroneComponent, pk=comp_id)
    new_comment = None
    # comment posted
    if request.method == "POST":
        comment_form = DroneComponentCommentForm(data=request.POST)
        if comment_form.is_valid():
            # create an object but don't save to database yet
            new_comment = comment_form.save(commit=False)
            # assign the comment to the current Article
            new_comment.article = dc
            # assign the current user to the comment
            new_comment.user = request.user
            # mark it as active if the user is in Moderateurs group
            if request.user.groups.filter(name__in=["Moderateurs"]).exists():
                new_comment.active = True
            # save it to database
            new_comment.save()
    else:
        comment_form = DroneComponentCommentForm()
    return render(request, "DetailedComposant.html", {
        "page": "comps",
        "comp": dc,
        "new_comment": new_comment,
        "comment_form": comment_form
    })


def register(request):
    good = True
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect(reverse("news"))
        good = False
    return render(request, "registration/register.html", {"form": CustomUserCreationForm, "isgood": good})


def profile(request):
    return render(request, "registration/profile.html", {"user": request.user})


def profile_edit(request):
    good = True
    if request.method == "POST":
        form = CustomUserChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect(reverse("profile"))
        good = False
    else:
        form = CustomUserChangeForm(instance=request.user)
    return render(request, "registration/profile_change.html", {"form": form, "isgood": good})


class CustomPasswordResetView(PasswordResetView):
    """
    custom class for password reset
    """
    from_email = "webmaster@argawaen.net"
    html_email_template_name = 'registration/password_reset_email.html'

