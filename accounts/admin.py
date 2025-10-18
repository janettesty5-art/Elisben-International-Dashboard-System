from django.contrib import admin
from .models import (
    Admin, Principal, Bursar, Teacher, Student, Alumni, Exam, Question, 
    ExamSubmission, StudentAnswer, Attendance, Book, BorrowRecord, 
    FeeRecord, ActivityLog, AcademicSession, Term, SubjectGrade, ResultSummary,
    SchoolSettings
)

@admin.register(Admin)
class AdminModelAdmin(admin.ModelAdmin):
    list_display = ['admin_id', 'full_name', 'user', 'created_at']
    search_fields = ['admin_id', 'full_name']
    readonly_fields = ['admin_id', 'created_at']

@admin.register(Principal)
class PrincipalAdmin(admin.ModelAdmin):
    list_display = ['principal_id', 'full_name', 'user', 'created_at']
    search_fields = ['principal_id', 'full_name']
    readonly_fields = ['principal_id', 'created_at']

@admin.register(Bursar)
class BursarAdmin(admin.ModelAdmin):
    list_display = ['bursar_id', 'full_name', 'user', 'created_at']
    search_fields = ['bursar_id', 'full_name']
    readonly_fields = ['bursar_id', 'created_at']

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ['teacher_id', 'full_name', 'subject', 'email', 'phone', 'created_at']
    search_fields = ['teacher_id', 'full_name', 'email', 'subject']
    list_filter = ['subject', 'created_at']
    readonly_fields = ['teacher_id', 'created_at']

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['student_id', 'full_name', 'class_name', 'email', 'phone', 'created_at']
    search_fields = ['student_id', 'full_name', 'email', 'class_name']
    list_filter = ['class_name', 'created_at']
    readonly_fields = ['student_id', 'created_at']

@admin.register(Alumni)
class AlumniAdmin(admin.ModelAdmin):
    list_display = ['student_id', 'full_name', 'last_class', 'reason', 'year_left', 'moved_on']
    search_fields = ['student_id', 'full_name', 'last_class']
    list_filter = ['reason', 'year_left', 'moved_on']
    readonly_fields = ['student_id', 'original_registration_date', 'moved_on', 'created_at']

@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ['exam_id', 'title', 'subject', 'class_name', 'created_by', 'is_active', 'shuffle_questions', 'created_at']
    search_fields = ['exam_id', 'title', 'subject']
    list_filter = ['class_name', 'subject', 'is_active', 'created_at']
    readonly_fields = ['exam_id', 'created_at']

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['exam', 'question_number', 'correct_answer']
    list_filter = ['exam']
    search_fields = ['question_text']

@admin.register(ExamSubmission)
class ExamSubmissionAdmin(admin.ModelAdmin):
    list_display = ['student', 'exam', 'score', 'correct_answers', 'total_questions', 'submitted_at']
    list_filter = ['exam', 'submitted_at']
    search_fields = ['student__full_name', 'exam__title']
    readonly_fields = ['submitted_at']

@admin.register(StudentAnswer)
class StudentAnswerAdmin(admin.ModelAdmin):
    list_display = ['submission', 'question', 'selected_answer', 'is_correct']
    list_filter = ['is_correct']

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'date', 'status', 'class_name', 'marked_by', 'created_at']
    list_filter = ['status', 'date', 'class_name']
    search_fields = ['student__full_name']
    readonly_fields = ['created_at']

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'isbn', 'quantity', 'available', 'added_by', 'created_at']
    search_fields = ['title', 'author', 'isbn']
    list_filter = ['created_at']
    readonly_fields = ['created_at']

@admin.register(BorrowRecord)
class BorrowRecordAdmin(admin.ModelAdmin):
    list_display = ['student', 'book', 'borrowed_date', 'return_date', 'is_returned', 'issued_by']
    list_filter = ['is_returned', 'borrowed_date']
    search_fields = ['student__full_name', 'book__title']

@admin.register(FeeRecord)
class FeeRecordAdmin(admin.ModelAdmin):
    list_display = ['student', 'total_fee', 'amount_paid', 'balance', 'is_balanced', 'fee_type', 'payment_date', 'payment_method']
    list_filter = ['fee_type', 'payment_method', 'is_balanced', 'payment_date']
    search_fields = ['student__full_name']
    readonly_fields = ['created_at', 'balance', 'is_balanced']

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ['action', 'performed_by_name', 'performed_by_type', 'timestamp']
    list_filter = ['action', 'performed_by_type', 'timestamp']
    search_fields = ['description', 'performed_by_name']
    readonly_fields = ['timestamp']

@admin.register(AcademicSession)
class AcademicSessionAdmin(admin.ModelAdmin):
    list_display = ['session_name', 'is_current', 'created_at']
    list_filter = ['is_current', 'created_at']
    search_fields = ['session_name']

@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
    list_display = ['session', 'term', 'is_current', 'created_at']
    list_filter = ['term', 'is_current', 'created_at']
    search_fields = ['session__session_name']

@admin.register(SubjectGrade)
class SubjectGradeAdmin(admin.ModelAdmin):
    list_display = ['student', 'term', 'subject', 'test_1', 'test_2', 'test_3', 'total_ca', 'exam', 'total_score', 'grade', 'remark']
    list_filter = ['term', 'subject', 'grade', 'remark']
    search_fields = ['student__full_name', 'subject']
    readonly_fields = ['total_ca', 'total_score', 'grade', 'remark', 'created_at', 'updated_at']

@admin.register(ResultSummary)
class ResultSummaryAdmin(admin.ModelAdmin):
    list_display = ['student', 'term', 'total_subjects', 'average_score', 'position_in_class']
    list_filter = ['term']
    search_fields = ['student__full_name']
    readonly_fields = ['created_at', 'updated_at']