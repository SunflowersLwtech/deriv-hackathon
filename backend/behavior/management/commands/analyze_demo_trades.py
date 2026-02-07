# behavior/management/commands/analyze_demo_trades.py
# Management command to analyze demo trading scenarios

from django.core.management.base import BaseCommand
from django.utils import timezone
from behavior.models import UserProfile, Trade
from behavior.tools import analyze_trade_patterns, generate_behavioral_nudge_with_ai
from behavior.websocket_utils import send_behavioral_nudge
import json


class Command(BaseCommand):
    help = 'Analyze demo trading scenarios and generate nudges'

    def add_arguments(self, parser):
        parser.add_argument(
            '--scenario',
            type=str,
            default='all',
            help='Scenario to analyze: revenge_trading, overtrading, loss_chasing, healthy, or all'
        )
        parser.add_argument(
            '--user-email',
            type=str,
            default='demo@tradeiq.com',
            help='Email of user to analyze'
        )
        parser.add_argument(
            '--hours',
            type=int,
            default=24,
            help='Hours of trade history to analyze'
        )
        parser.add_argument(
            '--send-nudge',
            action='store_true',
            help='Send nudge via WebSocket'
        )

    def handle(self, *args, **options):
        scenario = options['scenario']
        user_email = options['user_email']
        hours = options['hours']
        send_nudge = options['send_nudge']

        try:
            user = UserProfile.objects.get(email=user_email)
        except UserProfile.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User {user_email} not found'))
            return

        self.stdout.write(self.style.SUCCESS(f'Analyzing trades for {user.email}'))
        self.stdout.write(f'Scenario: {scenario}')
        self.stdout.write(f'Time window: {hours} hours')
        self.stdout.write('-' * 60)

        # Run analysis
        analysis = analyze_trade_patterns(str(user.id), hours=hours)

        # Display results
        self.stdout.write(f'\n📊 ANALYSIS RESULTS:')
        self.stdout.write(f'Trade count: {analysis["trade_count"]}')
        self.stdout.write(f'Summary: {analysis["summary"]}')
        self.stdout.write(f'Needs nudge: {analysis["needs_nudge"]}')

        # Pattern details
        patterns = analysis.get('patterns', {})
        
        self.stdout.write(f'\n🔍 DETECTED PATTERNS:')
        
        if patterns.get('revenge_trading', {}).get('detected'):
            rt = patterns['revenge_trading']
            self.stdout.write(self.style.WARNING(
                f'  ⚠️  REVENGE TRADING ({rt["severity"]}): {rt["details"]}'
            ))
        
        if patterns.get('overtrading', {}).get('detected'):
            ot = patterns['overtrading']
            self.stdout.write(self.style.WARNING(
                f'  ⚠️  OVERTRADING ({ot["severity"]}): {ot["details"]}'
            ))
        
        if patterns.get('loss_chasing', {}).get('detected'):
            lc = patterns['loss_chasing']
            self.stdout.write(self.style.WARNING(
                f'  ⚠️  LOSS CHASING ({lc["severity"]}): {lc["details"]}'
            ))
        
        if patterns.get('time_patterns', {}).get('detected'):
            tp = patterns['time_patterns']
            self.stdout.write(self.style.WARNING(
                f'  ⚠️  TIME PATTERNS ({tp.get("severity", "low")}): {tp["details"]}'
            ))

        if not patterns.get('has_any_pattern'):
            self.stdout.write(self.style.SUCCESS('  ✅ No concerning patterns detected'))

        # Generate nudge if needed
        if analysis['needs_nudge']:
            self.stdout.write(f'\n💬 GENERATING NUDGE...')
            nudge = generate_behavioral_nudge_with_ai(str(user.id), analysis)
            
            self.stdout.write(f'  Type: {nudge["nudge_type"]}')
            self.stdout.write(f'  Severity: {nudge["severity"]}')
            self.stdout.write(f'  Message: {nudge["message"]}')
            self.stdout.write(f'  Action: {nudge["suggested_action"]}')

            # Send via WebSocket if requested
            if send_nudge:
                success = send_behavioral_nudge(str(user.id), nudge)
                if success:
                    self.stdout.write(self.style.SUCCESS('\n✅ Nudge sent via WebSocket'))
                else:
                    self.stdout.write(self.style.ERROR('\n❌ Failed to send nudge'))
        else:
            self.stdout.write(self.style.SUCCESS('\n✅ No nudge needed - trading looks healthy!'))

        self.stdout.write('-' * 60)
