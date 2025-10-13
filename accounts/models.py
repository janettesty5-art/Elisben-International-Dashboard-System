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


# Teacher Model
class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    teacher_id = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    subject = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    registered_by = models.ForeignKey(Admin, on_delete=models.SET_NULL, null=True)

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
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    class_name = models.CharField(max_length=50)
    profile_picture = models.ImageField(upload_to='student_profiles/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    registered_by = models.ForeignKey(Admin, on_delete=models.SET_NULL, null=True)

    def save(self, *args, **kwargs):
        if not self.student_id:
            self.student_id = f"STD{''.join(random.choices(string.digits, k=6))}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} ({self.student_id})"


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


# Finance/Fee Record
class FeeRecord(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    fee_type = models.CharField(max_length=100)
    payment_date = models.DateField()
    payment_method = models.CharField(max_length=50, choices=[('Cash', 'Cash'), ('Bank Transfer', 'Bank Transfer'), ('Card', 'Card')])
    recorded_by = models.ForeignKey(Admin, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.full_name} - {self.fee_type}: ₦{self.amount}"


# Recent Activity Log
class ActivityLog(models.Model):
    ACTION_CHOICES = [
        ('student_registered', 'Student Registered'),
        ('teacher_registered', 'Teacher Registered'),
        ('student_deleted', 'Student Deleted'),
        ('teacher_deleted', 'Teacher Deleted'),
        ('exam_created', 'Exam Created'),
        ('exam_submitted', 'Exam Submitted'),
        ('attendance_marked', 'Attendance Marked'),
        ('fee_recorded', 'Fee Recorded'),
        ('book_added', 'Book Added'),
        ('book_borrowed', 'Book Borrowed'),
        ('book_returned', 'Book Returned'),
    ]
    
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    description = models.TextField()
    performed_by_type = models.CharField(max_length=20)  # 'admin', 'teacher', 'student'
    performed_by_name = models.CharField(max_length=200)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.action} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"