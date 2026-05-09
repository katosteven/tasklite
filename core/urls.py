"""Routes for the `core` app."""
from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("register/", views.register, name="register"),
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path("search/", views.search, name="search"),

    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("profile/edit/", views.ProfileUpdateView.as_view(), name="profile_edit"),

    path("projects/", views.ProjectListView.as_view(), name="project_list"),
    path("projects/new/", views.ProjectCreateView.as_view(), name="project_create"),
    path("projects/<int:pk>/", views.ProjectDetailView.as_view(), name="project_detail"),
    path("projects/<int:pk>/edit/", views.ProjectUpdateView.as_view(), name="project_edit"),
    path("projects/<int:pk>/delete/", views.ProjectDeleteView.as_view(), name="project_delete"),
    path("projects/<int:pk>/tasks/new/", views.TaskCreateView.as_view(), name="task_create"),
    path("projects/<int:pk>/upload/", views.AttachmentCreateView.as_view(), name="attachment_create"),

    path("tasks/<int:pk>/", views.TaskDetailView.as_view(), name="task_detail"),
    path("tasks/<int:pk>/edit/", views.TaskUpdateView.as_view(), name="task_edit"),
    path("tasks/<int:pk>/delete/", views.TaskDeleteView.as_view(), name="task_delete"),
    path("tasks/<int:pk>/toggle/", views.task_toggle_complete, name="task_toggle"),
    path("tasks/<int:task_pk>/notes/new/", views.NoteCreateView.as_view(), name="note_create"),

    path("notes/<int:pk>/edit/", views.NoteUpdateView.as_view(), name="note_edit"),
    path("notes/<int:pk>/delete/", views.NoteDeleteView.as_view(), name="note_delete"),

    path("attachments/<int:pk>/", views.attachment_download, name="attachment_download"),
    path("attachments/<int:pk>/delete/", views.AttachmentDeleteView.as_view(), name="attachment_delete"),
]
