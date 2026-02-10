# Path: accounts/management/commands/wipe_all_results.py
# 
# This script DELETES ALL RESULT DATA but keeps students, teachers, CBT intact
# 
# To run: python manage.py wipe_all_results

from django.core.management.base import BaseCommand
from accounts.models import SubjectResult, StudentResult, ResultActivityLog


class Command(BaseCommand):
    help = 'Wipe ALL result records (Subject Results, Student Results, Activity Logs) - FRESH START'

    def handle(self, *args, **kwargs):
        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.WARNING('⚠️  RESULT SYSTEM WIPE - FRESH START'))
        self.stdout.write('='*70 + '\n')
        
        # Count records before deletion
        subject_count = SubjectResult.objects.count()
        student_count = StudentResult.objects.count()
        log_count = ResultActivityLog.objects.count()
        
        self.stdout.write(f'\n📊 Current Records:')
        self.stdout.write(f'   - Subject Results: {subject_count}')
        self.stdout.write(f'   - Student Results: {student_count}')
        self.stdout.write(f'   - Activity Logs: {log_count}')
        self.stdout.write(f'\n   TOTAL TO DELETE: {subject_count + student_count + log_count} records\n')
        
        if subject_count == 0 and student_count == 0 and log_count == 0:
            self.stdout.write(self.style.SUCCESS('✅ No records to delete. System is already clean!\n'))
            return
        
        # Ask for confirmation
        self.stdout.write(self.style.ERROR('\n⚠️  WARNING: This will DELETE ALL result records!'))
        self.stdout.write(self.style.WARNING('   Students, Teachers, CBT data will NOT be affected.\n'))
        
        confirm = input('Type "DELETE ALL RESULTS" to confirm: ')
        
        if confirm != "DELETE ALL RESULTS":
            self.stdout.write(self.style.ERROR('\n❌ Deletion cancelled. No records were deleted.\n'))
            return
        
        self.stdout.write(self.style.WARNING('\n🗑️  Deleting records...\n'))
        
        try:
            # Delete Subject Results
            self.stdout.write('   Deleting Subject Results...')
            SubjectResult.objects.all().delete()
            self.stdout.write(self.style.SUCCESS(f'   ✅ Deleted {subject_count} subject results'))
            
            # Delete Student Results
            self.stdout.write('   Deleting Student Results...')
            StudentResult.objects.all().delete()
            self.stdout.write(self.style.SUCCESS(f'   ✅ Deleted {student_count} student results'))
            
            # Delete Activity Logs
            self.stdout.write('   Deleting Result Activity Logs...')
            ResultActivityLog.objects.all().delete()
            self.stdout.write(self.style.SUCCESS(f'   ✅ Deleted {log_count} activity logs'))
            
            self.stdout.write('\n' + '='*70)
            self.stdout.write(self.style.SUCCESS('✅ COMPLETE! All result records have been deleted.'))
            self.stdout.write(self.style.SUCCESS('✅ Result system is now FRESH and ready to start over.'))
            self.stdout.write('='*70 + '\n')
            
            self.stdout.write(self.style.WARNING('📝 What was NOT deleted:'))
            self.stdout.write('   ✅ Students')
            self.stdout.write('   ✅ Teachers')
            self.stdout.write('   ✅ CBT/Exams')
            self.stdout.write('   ✅ Attendance records')
            self.stdout.write('   ✅ Payment records')
            self.stdout.write('   ✅ Everything else\n')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ ERROR: {str(e)}'))
            self.stdout.write(self.style.ERROR('Some records may have been deleted. Check database.\n'))