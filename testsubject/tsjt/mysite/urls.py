from django.urls import path
from django.conf.urls import url,include
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('article/<int:id>-<slug:slug>', views.lire, name='lire'),
    path('about',views.about),
    path('blog',views.blog),
    path('media',views.media),
    
#    path('articles/<str:tag>', views.list_articles_by_tag),
#    path('articles/<int:year>/', views.list_articles),
#    path('articles/<int:year>/<int:month>', views.list_articles),  
]