from django.apps import AppConfig


class MarketConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "market"
    verbose_name = "Market Analysis"

    def ready(self):
        import os
        if os.environ.get("RUN_MONITOR", "").lower() == "true":
            from market.monitor import start_monitor
            start_monitor()
