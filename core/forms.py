"""ModelForms - all user input enters the system through these."""
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Attachment, Note, Profile, Project, Task


class RegisterForm(UserCreationForm):
    """Adds email to Django's built-in registration form."""
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "password1", "password2")


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ("bio", "avatar")


class ProjectForm(forms.ModelForm):
    due_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}), required=False
    )

    class Meta:
        model = Project
        fields = ("title", "description", "priority", "due_date", "members")
        widgets = {"members": forms.SelectMultiple(attrs={"size": 6})}

    def __init__(self, *args, owner=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Owner is implicit; never let them assign themself as "member".
        if owner is not None:
            self.fields["members"].queryset = User.objects.exclude(pk=owner.pk)


class TaskForm(forms.ModelForm):
    due_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}), required=False
    )

    class Meta:
        model = Task
        fields = ("title", "body", "due_date", "assignees")
        widgets = {"assignees": forms.SelectMultiple(attrs={"size": 6})}

    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Only project members + owner may be assigned to a task.
        if project is not None:
            self.fields["assignees"].queryset = (
                User.objects.filter(pk=project.owner_id)
                | project.members.all()
            ).distinct()


class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ("title", "body")


class AttachmentForm(forms.ModelForm):
    class Meta:
        model = Attachment
        fields = ("file",)
