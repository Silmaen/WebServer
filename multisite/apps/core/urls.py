from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("admin-panel/", views.AdminDashboardView.as_view(), name="admin-panel"),
    path("admin-panel/tasks/", views.AdminTasksPartialView.as_view(), name="admin-tasks-partial"),
    path("admin-panel/credentials/", views.AdminCredentialsPartialView.as_view(), name="admin-credentials-partial"),
    path("tasks/", views.TaskListView.as_view(), name="task-list"),
    path("tasks/indicator/", views.TaskIndicatorView.as_view(), name="task-indicator"),
    path("tasks/<uuid:pk>/", views.TaskDetailView.as_view(), name="task-detail"),
    path("tasks/<uuid:pk>/revoke/", views.TaskRevokeView.as_view(), name="task-revoke"),
]
