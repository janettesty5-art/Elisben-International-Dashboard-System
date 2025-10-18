from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import random
import string

# Admin Model (extends User)
class Admin(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    admin_id = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.admin_id:
            self.admin_id = f"ADM{''.join(random.choices(string.digits, k=6))}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} ({self.admin_id})"


# NEW: Principal Model
class Principal(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    principal_id = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.principal_id:
            self.principal_id = f"PRI{''.join(random.choices(string.digits, k=6))}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} ({self.principal_id})"


# NEW: Bursar Model
class Bursar(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bursar_id = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.bursar_id:
            self.bursar_id = f"BUR{''.join(random.choices(string.digits, k=6))}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} ({self.bursar_id})"


# Teacher Model
class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    teacher_id = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    subject = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    registered_by = models.ForeignKey(Admin, on_delete=models.SET_NULL, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.teacher_id:
            self.teacher_id = f"TCH{''.join(random.choices(string.digits, k=6))}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} ({self.teacher_id})"


# Student Model
class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student_id = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=200)
    email = models.EmailField(blank=True, null=True)  # Made optional
    phone = models.CharField(max_length=15, blank=True, null=True)  # Made optional
    class_name = models.CharField(max_length=50)
    profile_picture = models.ImageField(upload_to='student_profiles/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    registered_by = models.ForeignKey(Admin, on_delete=models.SET_NULL, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.student_id:
            self.student_id = f"STD{''.join(random.choices(string.digits, k=6))}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} ({self.student_id})"


# NEW: Alumni Model
class Alumni(models.Model):
    REASON_CHOICES = [
        ('Graduated', 'Graduated'),
        ('Transferred', 'Transferred'),
        ('Withdrawn', 'Withdrawn'),
    ]
    
    student_id = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=200)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    last_class = models.CharField(max_length=50)  # Last class attended
    profile_picture = models.ImageField(upload_to='alumni_profiles/', null=True, blank=True)
    
    # Alumni specific info
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    year_left = models.CharField(max_length=10)  # e.g., "2024/2025"
    moved_on = models.DateField(auto_now_add=True)
    moved_by = models.ForeignKey(Admin, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Keep original data
    original_registration_date = models.DateTimeField()
    
    # Additional info
    current_institution = models.CharField(max_length=200, blank=True, null=True)  # Where they went
    notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Alumni"

    def __str__(self):
        return f"{self.full_name} ({self.student_id}) - {self.reason}"


# Exam Model
class Exam(models.Model):
    exam_id = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=200)
    subject = models.CharField(max_length=100)
    class_name = models.CharField(max_length=50)
    duration_minutes = models.IntegerField(default=60)
    created_by = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    shuffle_questions = models.BooleanField(default=True)  # NEW: Shuffle for each student

    def save(self, *args, **kwargs):
        if not self.exam_id:
            self.exam_id = f"EXM{''.join(random.choices(string.ascii_uppercase + string.digits, k=6))}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.exam_id})"


# Question Model
class Question(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    option_a = models.CharField(max_length=500)
    option_b = models.CharField(max_length=500)
    option_c = models.CharField(max_length=500)
    option_d = models.CharField(max_length=500)
    correct_answer = models.CharField(max_length=1, choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')])
    question_number = models.IntegerField()

    class Meta:
        ordering = ['question_number']

    def __str__(self):
        return f"Q{self.question_number}: {self.question_text[:50]}"


# Student Exam Submission
class ExamSubmission(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    submitted_at = models.DateTimeField(auto_now_add=True)
    score = models.DecimalField(max_digits=5, decimal_places=2)
    total_questions = models.IntegerField()
    correct_answers = models.IntegerField()

    class Meta:
        unique_together = ['student', 'exam']

    def __str__(self):
        return f"{self.student.full_name} - {self.exam.title}: {self.score}%"


# Student Answer
class StudentAnswer(models.Model):
    submission = models.ForeignKey(ExamSubmission, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_answer = models.CharField(max_length=1, choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')])
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.submission.student.full_name} - Q{self.question.question_number}"


# NEW: School Settings Model
class SchoolSettings(models.Model):
    school_name = models.CharField(max_length=200, default="Elisben International College")
    school_motto = models.CharField(max_length=200, default="Excellence in Education")
    address = models.TextField(default="Surulere Quarters, Oke Osum Ikere Ekiti, Nigeria")
    phone = models.CharField(max_length=50, default="+234 803 634 3681")
    email = models.EmailField(default="admin@elisbencollege.com")
    website = models.URLField(blank=True, null=True)

    class Meta:
        verbose_name = "School Settings"
        verbose_name_plural = "School Settings"
    
    def __str__(self):
        return self.school_name


# Academic Result/Grade System
class AcademicSession(models.Model):
    session_name = models.CharField(max_length=50)  # e.g., "2024/2025"
    is_current = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.session_name


class Term(models.Model):
    TERM_CHOICES = [
        ('First', 'First Term'),
        ('Second', 'Second Term'),
        ('Third', 'Third Term'),
    ]
    session = models.ForeignKey(AcademicSession, on_delete=models.CASCADE)
    term = models.CharField(max_length=10, choices=TERM_CHOICES)
    is_current = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['session', 'term']

    def __str__(self):
        return f"{self.session.session_name} - {self.term} Term"


class SubjectGrade(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    term = models.ForeignKey(Term, on_delete=models.CASCADE)
    subject = models.CharField(max_length=100)
    
    # Test Scores (CA)
    test_1 = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # Max 100
    test_2 = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # Max 100
    test_3 = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # Max 100
    total_ca = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # Average of 3 tests (30%)
    
    # Exam Scores
    exam = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # Max 100 (70%)
    
    # Total and Grade
    total_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # CA + Exam
    grade = models.CharField(max_length=2, blank=True)  # A, B, C, D, E, F
    remark = models.CharField(max_length=20, blank=True)  # EXCELLENT, VERY GOOD, GOOD, PASS, FAIL
    
    # Position in subject and class average
    position_in_subject = models.IntegerField(null=True, blank=True)
    class_average = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Teacher
    recorded_by = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['student', 'term', 'subject']

    def calculate_totals(self):
        """Calculate CA (average of 3 tests as 30%), Total Score, and Grade"""
        # CA is average of 3 tests, scaled to 30%
        avg_test = (self.test_1 + self.test_2 + self.test_3) / 3
        self.total_ca = (avg_test * 30) / 100
        
        # Exam is already out of 100, scale to 70%
        exam_score = (self.exam * 70) / 100
        
        # Total score
        self.total_score = self.total_ca + exam_score
        
        # Calculate grade based on total score
        if self.total_score >= 80:
            self.grade = 'A'
            self.remark = 'EXCELLENT'
        elif self.total_score >= 70:
            self.grade = 'B'
            self.remark = 'VERY GOOD'
        elif self.total_score >= 60:
            self.grade = 'C'
            self.remark = 'GOOD'
        elif self.total_score >= 50:
            self.grade = 'D'
            self.remark = 'PASS'
        elif self.total_score >= 40:
            self.grade = 'E'
            self.remark = 'POOR'
        else:
            self.grade = 'F'
            self.remark = 'FAIL'

    def save(self, *args, **kwargs):
        self.calculate_totals()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.full_name} - {self.subject} - {self.term}"


# Result Summary with Remarks
class ResultSummary(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    term = models.ForeignKey(Term, on_delete=models.CASCADE)
    
    # Overall statistics
    total_subjects = models.IntegerField(default=0)
    score_gained = models.DecimalField(max_digits=7, decimal_places=2, default=0)  # Total score
    average_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    position_in_class = models.CharField(max_length=20, blank=True)  # "8th/21"
    promotion_status = models.CharField(max_length=50, blank=True)  # "PROMOTED" or "REPEAT"
    
    # Attendance
    times_school_opened = models.IntegerField(default=0)
    times_present = models.IntegerField(default=0)
    times_absent = models.IntegerField(default=0)
    
    # Remarks
    class_teacher_remark = models.TextField(blank=True)
    class_teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, related_name='class_teacher_remarks')
    
    principal_remark = models.TextField(blank=True)
    principal = models.ForeignKey(Principal, on_delete=models.SET_NULL, null=True, blank=True, related_name='principal_remarks')
    
    hos_remark = models.TextField(blank=True)  # Head of School
    hos = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True, related_name='hos_remarks')
    
    # Next term info
    vacation_date = models.DateField(null=True, blank=True)
    resumption_date = models.DateField(null=True, blank=True)
    next_term_begins = models.DateField(null=True, blank=True)
    next_term_fees = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    pta_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['student', 'term']

    def __str__(self):
        return f"{self.student.full_name} - {self.term} - Summary"


# Attendance Model
class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    class_name = models.CharField(max_length=50)
    date = models.DateField()
    status = models.CharField(max_length=10, choices=[('Present', 'Present'), ('Absent', 'Absent'), ('Late', 'Late')])
    marked_by = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['student', 'date']

    def __str__(self):
        return f"{self.student.full_name} - {self.date}: {self.status}"


# Library Book Model
class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=200)
    isbn = models.CharField(max_length=20, unique=True)
    quantity = models.IntegerField(default=1)
    available = models.IntegerField(default=1)
    added_by = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} by {self.author}"


# Borrow Record
class BorrowRecord(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    borrowed_date = models.DateField(auto_now_add=True)
    return_date = models.DateField(null=True, blank=True)
    is_returned = models.BooleanField(default=False)
    issued_by = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.student.full_name} - {self.book.title}"


# NEW: Enhanced Fee Record for Bursar
class FeeRecord(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    term = models.ForeignKey(Term, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Fee details
    total_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Payment tracking
    fee_type = models.CharField(max_length=100)
    payment_date = models.DateField()
    payment_method = models.CharField(max_length=50, choices=[('Cash', 'Cash'), ('Bank Transfer', 'Bank Transfer'), ('Card', 'Card')])
    is_balanced = models.BooleanField(default=False)
    
    # Who recorded
    recorded_by = models.ForeignKey(Bursar, on_delete=models.SET_NULL, null=True, blank=True, related_name='bursar_records')
    recorded_by_admin = models.ForeignKey(Admin, on_delete=models.SET_NULL, null=True, blank=True, related_name='admin_records')
    
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.balance = self.total_fee - self.amount_paid
        self.is_balanced = (self.balance <= 0)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.full_name} - {self.fee_type}: ₦{self.amount_paid}"


# Recent Activity Log
class ActivityLog(models.Model):
    ACTION_CHOICES = [
        ('student_registered', 'Student Registered'),
        ('teacher_registered', 'Teacher Registered'),
        ('student_deleted', 'Student Deleted'),
        ('teacher_deleted', 'Teacher Deleted'),
        ('exam_created', 'Exam Created'),
        ('exam_edited', 'Exam Edited'),  # NEW
        ('exam_deleted', 'Exam Deleted'),  # NEW
        ('exam_submitted', 'Exam Submitted'),
        ('attendance_marked', 'Attendance Marked'),
        ('fee_recorded', 'Fee Recorded'),
        ('grades_entered', 'Grades Entered'),  # NEW
        ('result_generated', 'Result Generated'),  # NEW
        ('book_added', 'Book Added'),
        ('book_borrowed', 'Book Borrowed'),
        ('book_returned', 'Book Returned'),
    ]
    
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    description = models.TextField()
    performed_by_type = models.CharField(max_length=20)  # 'admin', 'teacher', 'student', 'principal', 'bursar'
    performed_by_name = models.CharField(max_length=200)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.action} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"