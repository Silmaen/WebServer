"""Routes transverses de la console : administration et tâches."""

from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("admin-panel/", views.AdminDashboardView.as_view(), name='admin-panel'),
    path("tasks/", views.TaskListView.as_view(), name='task-list'),
    path("tasks/<uuid:pk>/", views.TaskDetailView.as_view(), name='task-detail'),
    path("tasks/<uuid:pk>/revoke/", views.TaskRevokeView.as_view(), name='task-revoke'),
]
