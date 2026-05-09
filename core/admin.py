from django.contrib import admin

from .models import Attachment, Note, Profile, Project, Task


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user",)
    search_fields = ("user__username",)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "priority", "due_date", "created_at")
    list_filter = ("priority",)
    search_fields = ("title", "description")
    filter_horizontal = ("members",)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "project", "completed", "due_date")
    list_filter = ("completed",)
    search_fields = ("title", "body")
    filter_horizontal = ("assignees",)


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ("title", "task", "author", "created_at")
    search_fields = ("title", "body")


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ("original_name", "project", "uploaded_by", "uploaded_at")
    search_fields = ("original_name",)
