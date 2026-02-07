# behavior/apps.py
from django.apps import AppConfig


class BehaviorConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "behavior"
    verbose_name = "Behavioral Coaching"
    
    def ready(self):
        """Import signals when app is ready."""
        import behavior.signals  # noqa