from django.shortcuts import render
from news.models import Article
from django.views.generic import TemplateView, CreateView
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy

def index(request):
    articles = Article.objects.filter(categorie=1).order_by('-date')[:15]
    return render(request,"News.html",{"page":"News",'derniers_articles':articles})

def resarch(request):
    articles = Article.objects.filter(categorie=2).order_by('-date')[:15]
    return render(request,"Research.html",{"page":"Search",'derniers_articles':articles})

def projects(request):
    articles = Article.objects.filter(categorie=3).order_by('-date')[:15]
    return render(request,"Projects.html",{"page":"Project",'derniers_articles':articles})

def links(request):
    articles = Article.objects.filter(categorie=4).order_by('-date')[:15]
    return render(request,"Links.html",{"page":"Links",'derniers_articles':articles})

class SignUpView(CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'signup.html'