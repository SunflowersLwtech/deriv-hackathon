# Manual migration: add unique constraint on users.email for auth lookup.
# behavior/models.py is frozen, so we use RunPython + SeparateDatabaseAndState.
#
# Rollback:  python manage.py migrate behavior 0001
#   - This drops the unique constraint/index on users.email
#   - Safe as long as no duplicate emails exist
#
# Works on both PostgreSQL (production/Supabase) and SQLite (local dev).

from django.db import migrations, models


def add_email_unique_constraint(apps, schema_editor):
    """Add a unique constraint on users.email, database-agnostic."""
    vendor = schema_editor.connection.vendor
    with schema_editor.connection.cursor() as cursor:
        if vendor == "postgresql":
            cursor.execute(
                'DO $$ BEGIN '
                '  ALTER TABLE "users" ADD CONSTRAINT "users_email_unique" UNIQUE ("email"); '
                'EXCEPTION WHEN duplicate_object THEN NULL; '
                'END $$;'
            )
        else:
            # SQLite: use CREATE UNIQUE INDEX (ALTER TABLE ADD CONSTRAINT
            # is not supported)
            cursor.execute(
                'CREATE UNIQUE INDEX IF NOT EXISTS '
                '"users_email_unique" ON "users" ("email");'
            )


def drop_email_unique_constraint(apps, schema_editor):
    """Remove the unique constraint on users.email (rollback)."""
    vendor = schema_editor.connection.vendor
    with schema_editor.connection.cursor() as cursor:
        if vendor == "postgresql":
            cursor.execute(
                'ALTER TABLE "users" '
                'DROP CONSTRAINT IF EXISTS "users_email_unique";'
            )
        else:
            cursor.execute('DROP INDEX IF EXISTS "users_email_unique";')


class Migration(migrations.Migration):

    dependencies = [
        ("behavior", "0001_initial"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(
                    add_email_unique_constraint,
                    reverse_code=drop_email_unique_constraint,
                ),
            ],
            state_operations=[
                migrations.AlterField(
                    model_name="userprofile",
                    name="email",
                    field=models.EmailField(max_length=255, unique=True),
                ),
            ],
        ),
    ]
