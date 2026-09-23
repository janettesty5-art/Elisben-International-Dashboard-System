from django.core.management.base import BaseCommand
from accounts.models import Student, StudentResult, ActivityLog

CLASS_ORDER = ['JSS1', 'JSS2', 'JSS3', 'SS1', 'SS2', 'SS3']


def next_class(current_class_name):
    """Returns the next class name up, or None if this is SS3 (top)
    or a class name that isn't in the recognized sequence at all."""
    upper = current_class_name.strip().upper()
    if upper in CLASS_ORDER:
        idx = CLASS_ORDER.index(upper)
        if idx < len(CLASS_ORDER) - 1:
            return CLASS_ORDER[idx + 1]
    return None


class Command(BaseCommand):
    help = "Promote students to their next class based on their Third Term result for a given academic year."

    def add_arguments(self, parser):
        parser.add_argument('academic_year', type=str, help='e.g. 2025/2026')
        parser.add_argument('--yes', action='store_true', help='Skip interactive confirmation (used when triggered from the web)')

    def handle(self, *args, **options):
        academic_year = options['academic_year'].strip()
        confirmed = options['yes']

        results = StudentResult.objects.filter(
            term='Third Term',
            academic_year=academic_year
        ).select_related('student')
        total = results.count()

        self.stdout.write(f"Found {total} Third Term result(s) for {academic_year}.\n")

        if total == 0:
            self.stdout.write(self.style.WARNING("Nothing to do."))
            return

        if not confirmed:
            confirm = input(f'Type "PROMOTE {academic_year}" to continue: ')
            if confirm != f"PROMOTE {academic_year}":
                self.stdout.write(self.style.ERROR("Cancelled."))
                return

        promoted = 0
        on_trial_promoted = 0
        repeated = 0
        skipped_topclass = 0
        skipped_unmapped = 0
        skipped_already = 0

        for result in results:
            student = result.student
            marker = f"[PROMO:{academic_year}:{student.id}]"

            already_done = ActivityLog.objects.filter(
                action='student_edited',
                description__contains=marker
            ).exists()
            if already_done:
                skipped_already += 1
                self.stdout.write(f"  SKIP (already processed earlier): {student.full_name}")
                continue

            status = result.status_promotion
            current_class = student.class_name

            if status == 'REPEAT':
                repeated += 1
                self.stdout.write(f"  STAY: {student.full_name} ({current_class}) - REPEAT")
                ActivityLog.objects.create(
                    action='student_edited',
                    description=f"{marker} {student.full_name} stayed in {current_class} (REPEAT, avg {result.average_score}%)",
                    performed_by_type='admin',
                    performed_by_name='System (Promotion Run)'
                )
                continue

            if status in ('PROMOTED', 'PROMOTED ON TRIAL'):
                target = next_class(current_class)

                if target is None:
                    if current_class.strip().upper() == 'SS3':
                        skipped_topclass += 1
                        self.stdout.write(f"  SS3 (leave for manual Alumni move): {student.full_name}")
                    else:
                        skipped_unmapped += 1
                        self.stdout.write(self.style.WARNING(
                            f"  UNRECOGNIZED CLASS '{current_class}' for {student.full_name} - left unchanged. "
                            f"Check spelling/case of this class name."
                        ))
                    continue

                old_class = student.class_name

                # Moving from a junior class into SS1 requires a Department,
                # which the student won't have yet - clear it so the admin
                # is prompted to set it via Edit Student.
                if target.upper() in ('SS1', 'SS2', 'SS3') and old_class.strip().upper() not in ('SS1', 'SS2', 'SS3'):
                    student.department = ''

                student.class_name = target
                student.save()

                if status == 'PROMOTED':
                    promoted += 1
                else:
                    on_trial_promoted += 1

                self.stdout.write(self.style.SUCCESS(
                    f"  PROMOTED: {student.full_name}  {old_class} -> {target}  ({status}, avg {result.average_score}%)"
                ))

                ActivityLog.objects.create(
                    action='student_edited',
                    description=f"{marker} {student.full_name} promoted {old_class} -> {target} ({status}, avg {result.average_score}%)",
                    performed_by_type='admin',
                    performed_by_name='System (Promotion Run)'
                )

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS(f"Promoted (PROMOTED): {promoted}"))
        self.stdout.write(self.style.SUCCESS(f"Promoted (ON TRIAL): {on_trial_promoted}"))
        self.stdout.write(f"Stayed in same class (REPEAT): {repeated}")
        self.stdout.write(f"SS3 - left for you to move to Alumni: {skipped_topclass}")
        if skipped_unmapped:
            self.stdout.write(self.style.WARNING(f"Unrecognized class name, left unchanged: {skipped_unmapped}"))
        if skipped_already:
            self.stdout.write(f"Already processed in an earlier run (skipped): {skipped_already}")
        self.stdout.write("=" * 60)