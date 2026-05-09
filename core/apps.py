from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = "core"
    default_auto_field = "django.db.models.AutoField"

    def ready(self) -> None:
        # Wire the post-save signal that creates a Profile row per User.
        from . import signals  # noqa: F401
