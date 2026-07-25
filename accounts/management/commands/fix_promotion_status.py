from django.core.management.base import BaseCommand
from accounts.models import StudentResult


class Command(BaseCommand):
    help = "Recalculates status_promotion for all StudentResult records using the new thresholds (0-39 REPEAT, 40-44 PROMOTED ON TRIAL, 45+ PROMOTED)."

    def handle(self, *args, **options):
        results = StudentResult.objects.all()
        total = results.count()
        updated_count = 0
        unchanged_count = 0

        self.stdout.write(f"Found {total} result(s). Recalculating...")

        for result in results:
            old_status = result.status_promotion

            if result.average_score >= 45:
                new_status = "PROMOTED"
            elif result.average_score >= 40:
                new_status = "PROMOTED ON TRIAL"
            else:
                new_status = "REPEAT"

            if old_status != new_status:
                result.status_promotion = new_status
                result.save(update_fields=['status_promotion'])
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"  Updated: {result.student.full_name} "
                        f"({result.term} {result.academic_year}) "
                        f"avg={result.average_score}% : '{old_status}' -> '{new_status}'"
                    )
                )
            else:
                unchanged_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"\nDone. {updated_count} updated, {unchanged_count} already correct, {total} total."
        ))