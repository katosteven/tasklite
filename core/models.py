"""Domain models. Object-level access is enforced in views via members M2M."""
from __future__ import annotations

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone


class Profile(models.Model):
    """Per-user profile. Created automatically by a post_save signal."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    bio = models.TextField(blank=True, max_length=2000)
    avatar = models.ImageField(upload_to="avatars/%Y/%m/", blank=True, null=True)

    def __str__(self) -> str:
        return f"Profile<{self.user.username}>"


class Project(models.Model):
    class Priority(models.IntegerChoices):
        LOW = 1, "Low"
        MEDIUM = 2, "Medium"
        HIGH = 3, "High"

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, max_length=5000)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_projects",
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="projects", blank=True
    )
    priority = models.IntegerField(choices=Priority.choices, default=Priority.MEDIUM)
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title

    def get_absolute_url(self) -> str:
        return reverse("project_detail", args=[self.pk])

    # Convenience helpers used in templates ------------------------------
    def is_overdue(self) -> bool:
        return bool(self.due_date and self.due_date < timezone.localdate())

    def percent_complete(self) -> int:
        total = self.tasks.count()
        if not total:
            return 0
        done = self.tasks.filter(completed=True).count()
        return int(done * 100 / total)

    def is_accessible_by(self, user) -> bool:
        """True for owner OR member; the only access check we ever need."""
        return self.owner_id == user.id or self.members.filter(pk=user.pk).exists()


class Task(models.Model):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="tasks"
    )
    title = models.CharField(max_length=200)
    body = models.TextField(blank=True, max_length=5000)
    completed = models.BooleanField(default=False)
    assignees = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="tasks", blank=True
    )
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["completed", "due_date", "-created_at"]

    def __str__(self) -> str:
        return self.title

    def get_absolute_url(self) -> str:
        return reverse("task_detail", args=[self.pk])

    def is_overdue(self) -> bool:
        return bool(
            not self.completed
            and self.due_date
            and self.due_date < timezone.localdate()
        )


class Note(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="notes")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notes"
    )
    title = models.CharField(max_length=200)
    body = models.TextField(max_length=5000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title


class Attachment(models.Model):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="attachments"
    )
    file = models.FileField(upload_to="attachments/%Y/%m/")
    original_name = models.CharField(max_length=255)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="uploaded_files",
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self) -> str:
        return self.original_name
