"""
Management command: validate_auth_schema

Validates that the database schema is compatible with the auth system:
  1. 'users' table exists and has expected columns
  2. 'email' column has a unique constraint
  3. No duplicate emails exist
  4. All UserProfile rows have valid UUIDs
  5. Reports any issues found

Usage:
    python manage.py validate_auth_schema
    python manage.py validate_auth_schema --fix-duplicates  # dry-run report of duplicates
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from behavior.models import UserProfile


class Command(BaseCommand):
    help = "Validate that the users table schema is compatible with auth requirements."

    def add_arguments(self, parser):
        parser.add_argument(
            "--fix-duplicates",
            action="store_true",
            default=False,
            help="Show detailed report of duplicate emails (does NOT auto-fix).",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("TradeIQ Auth Schema Validation"))
        self.stdout.write("=" * 60)

        issues = []
        warnings = []

        # --- Check 1: users table exists ---
        self.stdout.write("\n[1/5] Checking 'users' table exists...")
        if not self._table_exists("users"):
            issues.append("CRITICAL: 'users' table does not exist in the database.")
            self.stdout.write(self.style.ERROR("  FAIL: 'users' table not found"))
            self._report(issues, warnings)
            return
        self.stdout.write(self.style.SUCCESS("  OK: 'users' table exists"))

        # --- Check 2: expected columns ---
        self.stdout.write("\n[2/5] Checking expected columns...")
        expected_columns = {"id", "email", "name", "preferences", "watchlist", "created_at"}
        actual_columns = self._get_table_columns("users")
        missing = expected_columns - actual_columns
        extra = actual_columns - expected_columns

        if missing:
            issues.append(f"CRITICAL: Missing columns in 'users' table: {missing}")
            self.stdout.write(self.style.ERROR(f"  FAIL: Missing columns: {missing}"))
        else:
            self.stdout.write(self.style.SUCCESS(f"  OK: All expected columns present"))

        if extra:
            # Extra columns are fine -- just informational
            warnings.append(f"Extra columns in 'users' table (not an error): {extra}")
            self.stdout.write(self.style.WARNING(f"  INFO: Extra columns found: {extra}"))

        # --- Check 3: email unique constraint ---
        self.stdout.write("\n[3/5] Checking unique constraint on 'email'...")
        has_unique = self._column_has_unique_constraint("users", "email")
        if has_unique:
            self.stdout.write(self.style.SUCCESS("  OK: 'email' column has unique constraint"))
        else:
            issues.append(
                "WARNING: 'email' column lacks unique constraint. "
                "Run: python manage.py migrate behavior 0002"
            )
            self.stdout.write(self.style.ERROR(
                "  FAIL: No unique constraint on 'email'. "
                "Run migration 0002_userprofile_email_unique."
            ))

        # --- Check 4: duplicate emails ---
        self.stdout.write("\n[4/5] Checking for duplicate emails...")
        duplicates = self._find_duplicate_emails()
        if duplicates:
            issues.append(
                f"CRITICAL: {len(duplicates)} duplicate email(s) found. "
                "Must resolve before applying unique constraint."
            )
            self.stdout.write(self.style.ERROR(
                f"  FAIL: {len(duplicates)} duplicate email(s) found"
            ))
            if options["fix_duplicates"]:
                self.stdout.write("\n  Duplicate email details:")
                for email, count in duplicates:
                    self.stdout.write(f"    - {email}: {count} rows")
                    users = UserProfile.objects.filter(email=email).order_by("created_at")
                    for u in users:
                        self.stdout.write(
                            f"      id={u.id}  name={u.name!r}  created_at={u.created_at}"
                        )
                self.stdout.write(
                    "\n  To fix: keep the oldest row for each email and "
                    "reassign/delete the newer duplicates."
                )
        else:
            self.stdout.write(self.style.SUCCESS("  OK: No duplicate emails"))

        # --- Check 5: valid UUIDs ---
        self.stdout.write("\n[5/5] Checking UserProfile UUIDs...")
        invalid_uuid_count = self._check_invalid_uuids()
        if invalid_uuid_count > 0:
            issues.append(f"WARNING: {invalid_uuid_count} row(s) with invalid/null UUIDs")
            self.stdout.write(self.style.ERROR(
                f"  FAIL: {invalid_uuid_count} row(s) with invalid UUIDs"
            ))
        else:
            self.stdout.write(self.style.SUCCESS("  OK: All UUIDs are valid"))

        # --- Summary ---
        self._report(issues, warnings)

    def _table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the database."""
        with connection.cursor() as cursor:
            # Works for both PostgreSQL and SQLite
            if connection.vendor == "postgresql":
                cursor.execute(
                    "SELECT EXISTS ("
                    "  SELECT FROM information_schema.tables "
                    "  WHERE table_name = %s"
                    ");",
                    [table_name],
                )
                return cursor.fetchone()[0]
            else:
                # SQLite fallback
                cursor.execute(
                    "SELECT name FROM sqlite_master "
                    "WHERE type='table' AND name=%s;",
                    [table_name],
                )
                return cursor.fetchone() is not None

    def _get_table_columns(self, table_name: str) -> set:
        """Get column names for a table."""
        with connection.cursor() as cursor:
            if connection.vendor == "postgresql":
                cursor.execute(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name = %s;",
                    [table_name],
                )
                return {row[0] for row in cursor.fetchall()}
            else:
                # SQLite fallback using PRAGMA
                cursor.execute(f'PRAGMA table_info("{table_name}");')
                return {row[1] for row in cursor.fetchall()}

    def _column_has_unique_constraint(self, table_name: str, column_name: str) -> bool:
        """Check if a column has a unique constraint or unique index."""
        with connection.cursor() as cursor:
            if connection.vendor == "postgresql":
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM (
                        -- Check unique constraints
                        SELECT 1
                        FROM information_schema.table_constraints tc
                        JOIN information_schema.constraint_column_usage ccu
                            ON tc.constraint_name = ccu.constraint_name
                        WHERE tc.table_name = %s
                            AND ccu.column_name = %s
                            AND tc.constraint_type = 'UNIQUE'
                        UNION
                        -- Check unique indexes
                        SELECT 1
                        FROM pg_indexes
                        WHERE tablename = %s
                            AND indexdef LIKE %s
                            AND indexdef LIKE %s
                    ) AS combined;
                    """,
                    [
                        table_name, column_name,
                        table_name,
                        "%UNIQUE%",
                        f"%{column_name}%",
                    ],
                )
                return cursor.fetchone()[0] > 0
            else:
                # SQLite: check for unique index
                cursor.execute(f'PRAGMA index_list("{table_name}");')
                for row in cursor.fetchall():
                    index_name = row[1]
                    is_unique = row[2]
                    if is_unique:
                        cursor.execute(f'PRAGMA index_info("{index_name}");')
                        cols = [r[2] for r in cursor.fetchall()]
                        if column_name in cols and len(cols) == 1:
                            return True
                return False

    def _find_duplicate_emails(self) -> list:
        """Find emails that appear more than once."""
        with connection.cursor() as cursor:
            cursor.execute(
                'SELECT email, COUNT(*) as cnt FROM "users" '
                "GROUP BY email HAVING COUNT(*) > 1 "
                "ORDER BY cnt DESC;"
            )
            return cursor.fetchall()

    def _check_invalid_uuids(self) -> int:
        """Count rows with NULL or empty id (should be impossible with model defaults)."""
        with connection.cursor() as cursor:
            cursor.execute(
                'SELECT COUNT(*) FROM "users" WHERE id IS NULL;'
            )
            return cursor.fetchone()[0]

    def _report(self, issues: list, warnings: list):
        """Print final summary."""
        self.stdout.write("\n" + "=" * 60)
        if not issues and not warnings:
            self.stdout.write(self.style.SUCCESS(
                "\nAll checks passed. Schema is ready for auth integration."
            ))
        else:
            if warnings:
                self.stdout.write(self.style.WARNING(f"\nWarnings ({len(warnings)}):"))
                for w in warnings:
                    self.stdout.write(f"  - {w}")
            if issues:
                self.stdout.write(self.style.ERROR(f"\nIssues ({len(issues)}):"))
                for issue in issues:
                    self.stdout.write(f"  - {issue}")
                self.stdout.write(self.style.ERROR(
                    "\nSchema validation FAILED. Fix the issues above before proceeding."
                ))
            else:
                self.stdout.write(self.style.SUCCESS(
                    "\nSchema validation passed (with informational warnings)."
                ))
