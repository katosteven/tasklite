"""Views - every endpoint is auth-gated and queryset-scoped to the user."""
from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.http import FileResponse, Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView,
)

from .forms import (
    AttachmentForm, NoteForm, ProfileForm, ProjectForm, RegisterForm, TaskForm,
)
from .models import Attachment, Note, Project, Task


# --- Public pages -------------------------------------------------------
def home(request):
    """Public landing page; redirects authenticated users to dashboard."""
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "core/home.html")


def about(request):
    """Static About page describing what the app does."""
    return render(request, "core/about.html")


# --- Mixins -------------------------------------------------------------
class ProjectAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Used on project-scoped CBVs; populates self.project from the URL."""
    project_url_kwarg = "pk"

    def get_project(self) -> Project:
        return get_object_or_404(Project, pk=self.kwargs[self.project_url_kwarg])

    def test_func(self) -> bool:
        return self.get_project().is_accessible_by(self.request.user)


# --- Auth ---------------------------------------------------------------
def register(request):
    """User self-registration. Logs them in on success."""
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created.")
            return redirect("dashboard")
    else:
        form = RegisterForm()
    return render(request, "core/register.html", {"form": form})


# --- Dashboard / search -------------------------------------------------
class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "core/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        u = self.request.user
        my_projects = Project.objects.filter(Q(owner=u) | Q(members=u)).distinct()
        my_tasks = Task.objects.filter(
            Q(assignees=u) | Q(project__owner=u)
        ).distinct()
        today = timezone.localdate()
        ctx["projects"] = my_projects[:5]
        ctx["my_open_tasks"] = (
            Task.objects.filter(assignees=u, completed=False)
            .select_related("project")[:10]
        )
        ctx["project_count"] = my_projects.count()
        ctx["open_task_count"] = my_tasks.filter(completed=False).count()
        ctx["done_task_count"] = my_tasks.filter(completed=True).count()
        ctx["overdue_count"] = my_tasks.filter(
            completed=False, due_date__lt=today
        ).count()
        return ctx


@login_required
def search(request):
    """Search only across projects/tasks the user can already see."""
    q = (request.GET.get("q") or "").strip()
    projects = tasks = []
    if q:
        u = request.user
        accessible = Project.objects.filter(Q(owner=u) | Q(members=u)).distinct()
        projects = accessible.filter(Q(title__icontains=q) | Q(description__icontains=q))
        tasks = Task.objects.filter(project__in=accessible).filter(
            Q(title__icontains=q) | Q(body__icontains=q)
        ).select_related("project")
    return render(request, "core/search.html",
                  {"q": q, "projects": projects, "tasks": tasks})


# --- Profile ------------------------------------------------------------
class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "core/profile.html"


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    form_class = ProfileForm
    template_name = "core/profile_form.html"
    success_url = reverse_lazy("profile")

    def get_object(self, queryset=None):
        return self.request.user.profile


# --- Projects -----------------------------------------------------------
class ProjectListView(LoginRequiredMixin, ListView):
    template_name = "core/project_list.html"
    context_object_name = "projects"
    paginate_by = 20

    def get_queryset(self):
        u = self.request.user
        return Project.objects.filter(Q(owner=u) | Q(members=u)).distinct()


class ProjectCreateView(LoginRequiredMixin, CreateView):
    form_class = ProjectForm
    template_name = "core/project_form.html"

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw["owner"] = self.request.user
        return kw

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class ProjectDetailView(ProjectAccessMixin, DetailView):
    template_name = "core/project_detail.html"

    def get_object(self, queryset=None):
        return self.get_project()


class ProjectUpdateView(ProjectAccessMixin, UpdateView):
    form_class = ProjectForm
    template_name = "core/project_form.html"

    def get_object(self, queryset=None):
        return self.get_project()

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw["owner"] = self.get_project().owner
        return kw


class ProjectDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Only the owner can delete a project."""
    model = Project
    success_url = reverse_lazy("project_list")
    template_name = "core/project_confirm_delete.html"

    def test_func(self) -> bool:
        return self.get_object().owner_id == self.request.user.id


# --- Tasks --------------------------------------------------------------
class TaskCreateView(ProjectAccessMixin, CreateView):
    form_class = TaskForm
    template_name = "core/task_form.html"

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw["project"] = self.get_project()
        return kw

    def form_valid(self, form):
        form.instance.project = self.get_project()
        return super().form_valid(form)


class _TaskAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Like ProjectAccessMixin but for views with a Task pk."""

    def get_task(self) -> Task:
        return get_object_or_404(Task, pk=self.kwargs["pk"])

    def test_func(self) -> bool:
        return self.get_task().project.is_accessible_by(self.request.user)


class TaskDetailView(_TaskAccessMixin, DetailView):
    model = Task
    template_name = "core/task_detail.html"


class TaskUpdateView(_TaskAccessMixin, UpdateView):
    model = Task
    form_class = TaskForm
    template_name = "core/task_form.html"

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw["project"] = self.get_object().project
        return kw


class TaskDeleteView(_TaskAccessMixin, DeleteView):
    model = Task
    template_name = "core/task_confirm_delete.html"

    def get_success_url(self):
        return reverse("project_detail", args=[self.object.project_id])


@require_POST
@login_required
def task_toggle_complete(request, pk: int):
    """Flip a task's completed flag. POST-only to defeat CSRF & GET side-effects."""
    task = get_object_or_404(Task, pk=pk)
    if not task.project.is_accessible_by(request.user):
        raise Http404
    task.completed = not task.completed
    task.save(update_fields=["completed"])
    return HttpResponseRedirect(reverse("task_detail", args=[task.pk]))


class NoteCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    form_class = NoteForm
    template_name = "core/note_form.html"

    def get_task(self) -> Task:
        return get_object_or_404(Task, pk=self.kwargs["task_pk"])

    def test_func(self) -> bool:
        return self.get_task().project.is_accessible_by(self.request.user)

    def form_valid(self, form):
        form.instance.task = self.get_task()
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("task_detail", args=[self.kwargs["task_pk"]])


class NoteUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Only the author may edit their note."""
    model = Note
    form_class = NoteForm
    template_name = "core/note_form.html"

    def test_func(self) -> bool:
        return self.get_object().author_id == self.request.user.id

    def get_success_url(self):
        return reverse("task_detail", args=[self.object.task_id])


class NoteDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Note
    template_name = "core/note_confirm_delete.html"

    def test_func(self) -> bool:
        n = self.get_object()
        # Author OR project owner can delete.
        return (n.author_id == self.request.user.id
                or n.task.project.owner_id == self.request.user.id)

    def get_success_url(self):
        return reverse("task_detail", args=[self.object.task_id])


class AttachmentCreateView(ProjectAccessMixin, CreateView):
    form_class = AttachmentForm
    template_name = "core/attachment_form.html"

    def form_valid(self, form):
        f = form.cleaned_data["file"]
        # Django sanitises filenames in the storage layer, but we keep the
        # user-facing original separate so we never reflect raw input.
        form.instance.project = self.get_project()
        form.instance.uploaded_by = self.request.user
        form.instance.original_name = f.name[:255]
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("project_detail", args=[self.kwargs["pk"]])


@login_required
def attachment_download(request, pk: int):
    """Stream the file only if the user has project access."""
    a = get_object_or_404(Attachment, pk=pk)
    if not a.project.is_accessible_by(request.user):
        raise Http404
    return FileResponse(a.file.open("rb"), as_attachment=True, filename=a.original_name)


class AttachmentDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Attachment
    template_name = "core/project_confirm_delete.html"  # generic confirm

    def test_func(self) -> bool:
        a = self.get_object()
        return (a.uploaded_by_id == self.request.user.id
                or a.project.owner_id == self.request.user.id)

    def get_success_url(self):
        return reverse("project_detail", args=[self.object.project_id])
