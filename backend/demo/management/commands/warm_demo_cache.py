from django.core.management.base import BaseCommand
from demo.fallback import warm_cache


class Command(BaseCommand):
    help = "Pre-warm demo cache for hackathon presentation"

    def handle(self, *args, **options):
        self.stdout.write("Warming demo cache...")
        warm_cache()
        self.stdout.write(self.style.SUCCESS("Demo cache warmed. Ready for presentation."))
