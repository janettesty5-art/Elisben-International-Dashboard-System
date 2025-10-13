from django.contrib import admin
from .models import (
    Admin, Teacher, Student, Exam, Question, 
    ExamSubmission, StudentAnswer, Attendance, 
    Book, BorrowRecord, FeeRecord, ActivityLog
)

@admin.register(Admin)
class AdminModelAdmin(admin.ModelAdmin):
    list_display = ['admin_id', 'full_name', 'user', 'created_at']
    search_fields = ['admin_id', 'full_name']
    readonly_fields = ['admin_id', 'created_at']

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

@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ['exam_id', 'title', 'subject', 'class_name', 'created_by', 'is_active', 'created_at']
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
    list_display = ['student', 'amount', 'fee_type', 'payment_date', 'payment_method', 'recorded_by']
    list_filter = ['fee_type', 'payment_method', 'payment_date']
    search_fields = ['student__full_name']
    readonly_fields = ['created_at']

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ['action', 'performed_by_name', 'performed_by_type', 'timestamp']
    list_filter = ['action', 'performed_by_type', 'timestamp']
    search_fields = ['description', 'performed_by_name']
    readonly_fields = ['timestamp']