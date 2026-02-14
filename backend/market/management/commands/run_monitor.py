"""Start the real-time market monitor: python manage.py run_monitor"""
from django.core.management.base import BaseCommand
from market.monitor import start_monitor


class Command(BaseCommand):
    help = "Start the real-time market monitor"

    def handle(self, *args, **options):
        self.stdout.write("Starting market monitor...")
        monitor = start_monitor()
        self.stdout.write(self.style.SUCCESS("Monitor running. Press Ctrl+C to stop."))
        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            monitor.stop()
            self.stdout.write("Monitor stopped.")
