"""
Management command: python manage.py seed_demo [--quiet]

Creates demo user + a batch of realistic trades for Trading Twin and behavioral
detection demos. Idempotent — safe to run on every deploy.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import uuid

DEMO_USER_ID = "d1000000-0000-0000-0000-000000000001"


class Command(BaseCommand):
    help = "Seed demo user and trades for hackathon demo"

    def add_arguments(self, parser):
        parser.add_argument(
            "--quiet", action="store_true", help="Suppress output"
        )

    def handle(self, *args, **options):
        quiet = options.get("quiet", False)
        from behavior.models import UserProfile, Trade

        # 1. Create demo user
        demo_user, created = UserProfile.objects.get_or_create(
            id=DEMO_USER_ID,
            defaults={
                "email": "alex@tradeiq.demo",
                "name": "Alex Demo",
                "preferences": {"theme": "dark"},
                "watchlist": ["EUR/USD", "BTC/USD", "GBP/JPY"],
            },
        )
        if not quiet:
            self.stdout.write(
                f"Demo user: {demo_user.name} ({'created' if created else 'exists'})"
            )

        # 2. Skip if trades already exist
        existing = Trade.objects.filter(user=demo_user, is_mock=True).count()
        if existing >= 15:
            if not quiet:
                self.stdout.write(f"Already {existing} demo trades, skipping seed.")
            return

        # 3. Clear any partial data and seed fresh
        Trade.objects.filter(user=demo_user, is_mock=True).delete()

        now = timezone.now()
        trades_data = [
            # Day 1-3: Disciplined trading (wins)
            {"mins": -4300, "instrument": "EUR/USD", "dir": "buy",  "entry": 1.0850, "exit": 1.0875, "pnl": 25.0, "dur": 3600},
            {"mins": -4100, "instrument": "EUR/USD", "dir": "sell", "entry": 1.0880, "exit": 1.0860, "pnl": 20.0, "dur": 2400},
            {"mins": -3800, "instrument": "BTC/USD", "dir": "buy",  "entry": 42000, "exit": 42350, "pnl": 35.0, "dur": 5400},
            {"mins": -3500, "instrument": "GBP/JPY", "dir": "buy",  "entry": 188.50, "exit": 188.85, "pnl": 30.0, "dur": 4200},
            # Day 4: Loss triggers revenge trading
            {"mins": -2900, "instrument": "EUR/USD", "dir": "buy",  "entry": 1.0870, "exit": 1.0820, "pnl": -50.0, "dur": 1800},
            {"mins": -2895, "instrument": "EUR/USD", "dir": "sell", "entry": 1.0815, "exit": 1.0830, "pnl": -15.0, "dur": 120},
            {"mins": -2893, "instrument": "EUR/USD", "dir": "buy",  "entry": 1.0835, "exit": 1.0820, "pnl": -15.0, "dur": 90},
            {"mins": -2891, "instrument": "EUR/USD", "dir": "sell", "entry": 1.0818, "exit": 1.0825, "pnl": -7.0,  "dur": 60},
            # Day 5-6: Loss chasing (increasing size after losses)
            {"mins": -2100, "instrument": "BTC/USD", "dir": "buy",  "entry": 41800, "exit": 41600, "pnl": -40.0, "dur": 3600},
            {"mins": -1900, "instrument": "BTC/USD", "dir": "buy",  "entry": 41550, "exit": 41400, "pnl": -60.0, "dur": 2400},
            {"mins": -1700, "instrument": "BTC/USD", "dir": "buy",  "entry": 41350, "exit": 41200, "pnl": -90.0, "dur": 1800},
            # Day 7-8: Recovery (disciplined)
            {"mins": -1200, "instrument": "GBP/JPY", "dir": "sell", "entry": 189.20, "exit": 188.90, "pnl": 28.0, "dur": 5400},
            {"mins": -900,  "instrument": "EUR/USD", "dir": "buy",  "entry": 1.0800, "exit": 1.0835, "pnl": 35.0, "dur": 7200},
            # Day 9: Overtrading burst
            {"mins": -500, "instrument": "EUR/USD", "dir": "buy",  "entry": 1.0840, "exit": 1.0845, "pnl": 5.0,   "dur": 300},
            {"mins": -490, "instrument": "EUR/USD", "dir": "sell", "entry": 1.0843, "exit": 1.0840, "pnl": 3.0,   "dur": 240},
            {"mins": -480, "instrument": "BTC/USD", "dir": "buy",  "entry": 42100, "exit": 42050, "pnl": -5.0,   "dur": 180},
            {"mins": -470, "instrument": "GBP/JPY", "dir": "buy",  "entry": 189.00, "exit": 189.05, "pnl": 4.0,  "dur": 300},
            {"mins": -460, "instrument": "EUR/USD", "dir": "sell", "entry": 1.0838, "exit": 1.0842, "pnl": -4.0,  "dur": 120},
            {"mins": -450, "instrument": "EUR/USD", "dir": "buy",  "entry": 1.0845, "exit": 1.0848, "pnl": 3.0,   "dur": 150},
            # Day 10: Latest trade
            {"mins": -60,  "instrument": "EUR/USD", "dir": "buy",  "entry": 1.0855, "exit": 1.0870, "pnl": 15.0,  "dur": 3600},
        ]

        for td in trades_data:
            opened = now + timedelta(minutes=td["mins"])
            Trade.objects.create(
                user=demo_user,
                instrument=td["instrument"],
                direction=td["dir"],
                entry_price=td["entry"],
                exit_price=td["exit"],
                pnl=td["pnl"],
                duration_seconds=td["dur"],
                opened_at=opened,
                closed_at=opened + timedelta(seconds=td["dur"]),
                is_mock=True,
            )

        if not quiet:
            self.stdout.write(
                self.style.SUCCESS(f"Seeded {len(trades_data)} demo trades for Trading Twin + behavioral detection.")
            )
