"""
Management command to seed AI Personas into the database.
Usage: python manage.py seed_personas
"""
from django.core.management.base import BaseCommand
from content.models import AIPersona
from content.personas import ALL_PERSONAS


class Command(BaseCommand):
    help = "Seed the 3 AI personas (Calm Analyst, Data Nerd, Trading Coach) into the database."

    def handle(self, *args, **options):
        created_count = 0
        updated_count = 0

        for persona_data in ALL_PERSONAS:
            obj, created = AIPersona.objects.update_or_create(
                personality_type=persona_data["personality_type"],
                defaults={
                    "name": persona_data["name"],
                    "system_prompt": persona_data["system_prompt"],
                    "voice_config": persona_data.get("voice_config", {}),
                    "is_primary": persona_data.get("is_primary", False),
                },
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"  Created: {obj.name} ({obj.personality_type})"))
            else:
                updated_count += 1
                self.stdout.write(self.style.WARNING(f"  Updated: {obj.name} ({obj.personality_type})"))

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone! {created_count} created, {updated_count} updated. "
                f"Total personas: {AIPersona.objects.count()}"
            )
        )
