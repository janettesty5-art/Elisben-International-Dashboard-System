from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from .models import *
import csv
from datetime import datetime


# ============= UNIFIED LOGIN =============
def unified_login(request):
    if request.method == 'POST':
        role = request.POST.get('role')
        user_id = request.POST.get('user_id')
        
        try:
            # Check which model has this ID
            if role == 'admin':
                admin = Admin.objects.get(admin_id=user_id)
                user = admin.user
                login(request, user)
                return redirect('admin_dashboard')
            elif role == 'teacher':
                teacher = Teacher.objects.get(teacher_id=user_id)
                user = teacher.user
                login(request, user)
                return redirect('teacher_dashboard')
            elif role == 'student':
                student = Student.objects.get(student_id=user_id)
                user = student.user
                login(request, user)
                return redirect('student_dashboard')
        except:
            messages.error(request, 'Invalid ID or Role. Please try again.')
            return redirect('unified_login')
    
    return render(request, 'login.html')


def user_logout(request):
    logout(request)
    return redirect('unified_login')


# ============= ADMIN VIEWS =============
@login_required
def admin_dashboard(request):
    try:
        admin = Admin.objects.get(user=request.user)
    except:
        messages.error(request, 'Access denied.')
        return redirect('unified_login')
    
    # Get all data for admin dashboard
    students = Student.objects.all().order_by('-created_at')
    teachers = Teacher.objects.all().order_by('-created_at')
    recent_activities = ActivityLog.objects.all()[:20]
    total_fees = FeeRecord.objects.aggregate(models.Sum('amount'))['amount__sum'] or 0
    
    context = {
        'admin': admin,
        'students': students,
        'teachers': teachers,
        'activities': recent_activities,
        'total_fees': total_fees,
        'student_count': students.count(),
        'teacher_count': teachers.count(),
    }
    return render(request, 'admin_dashboard.html', context)


@login_required
def register_student(request):
    try:
        admin = Admin.objects.get(user=request.user)
    except:
        messages.error(request, 'Access denied.')
        return redirect('unified_login')
    
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        class_name = request.POST.get('class_name')
        
        # Create user account
        username = email.split('@')[0] + str(random.randint(100, 999))
        user = User.objects.create_user(username=username, email=email)
        
        # Create student
        student = Student.objects.create(
            user=user,
            full_name=full_name,
            email=email,
            phone=phone,
            class_name=class_name,
            registered_by=admin
        )
        
        # Log activity
        ActivityLog.objects.create(
            action='student_registered',
            description=f'Student {full_name} registered with ID {student.student_id}',
            performed_by_type='admin',
            performed_by_name=admin.full_name
        )
        
        messages.success(request, f'Student registered successfully! Student ID: {student.student_id}')
        return redirect('admin_dashboard')
    
    return render(request, 'register_student.html')


@login_required
def register_teacher(request):
    try:
        admin = Admin.objects.get(user=request.user)
    except:
        messages.error(request, 'Access denied.')
        return redirect('unified_login')
    
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        subject = request.POST.get('subject')
        
        # Create user account
        username = email.split('@')[0] + str(random.randint(100, 999))
        user = User.objects.create_user(username=username, email=email)
        
        # Create teacher
        teacher = Teacher.objects.create(
            user=user,
            full_name=full_name,
            email=email,
            phone=phone,
            subject=subject,
            registered_by=admin
        )
        
        # Log activity
        ActivityLog.objects.create(
            action='teacher_registered',
            description=f'Teacher {full_name} registered with ID {teacher.teacher_id}',
            performed_by_type='admin',
            performed_by_name=admin.full_name
        )
        
        messages.success(request, f'Teacher registered successfully! Teacher ID: {teacher.teacher_id}')
        return redirect('admin_dashboard')
    
    return render(request, 'register_teacher.html')


@login_required
def delete_student(request, student_id):
    try:
        admin = Admin.objects.get(user=request.user)
        student = Student.objects.get(id=student_id)
        student_name = student.full_name
        student.user.delete()  # This will cascade delete the student
        
        # Log activity
        ActivityLog.objects.create(
            action='student_deleted',
            description=f'Student {student_name} deleted',
            performed_by_type='admin',
            performed_by_name=admin.full_name
        )
        
        messages.success(request, 'Student deleted successfully!')
    except:
        messages.error(request, 'Error deleting student.')
    
    return redirect('admin_dashboard')


@login_required
def delete_teacher(request, teacher_id):
    try:
        admin = Admin.objects.get(user=request.user)
        teacher = Teacher.objects.get(id=teacher_id)
        teacher_name = teacher.full_name
        teacher.user.delete()  # This will cascade delete the teacher
        
        # Log activity
        ActivityLog.objects.create(
            action='teacher_deleted',
            description=f'Teacher {teacher_name} deleted',
            performed_by_type='admin',
            performed_by_name=admin.full_name
        )
        
        messages.success(request, 'Teacher deleted successfully!')
    except:
        messages.error(request, 'Error deleting teacher.')
    
    return redirect('admin_dashboard')


@login_required
def manage_finance(request):
    try:
        admin = Admin.objects.get(user=request.user)
    except:
        messages.error(request, 'Access denied.')
        return redirect('unified_login')
    
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        amount = request.POST.get('amount')
        fee_type = request.POST.get('fee_type')
        payment_method = request.POST.get('payment_method')
        payment_date = request.POST.get('payment_date')
        
        student = Student.objects.get(student_id=student_id)
        
        FeeRecord.objects.create(
            student=student,
            amount=amount,
            fee_type=fee_type,
            payment_method=payment_method,
            payment_date=payment_date,
            recorded_by=admin
        )
        
        # Log activity
        ActivityLog.objects.create(
            action='fee_recorded',
            description=f'Fee payment of ₦{amount} recorded for {student.full_name}',
            performed_by_type='admin',
            performed_by_name=admin.full_name
        )
        
        messages.success(request, 'Fee recorded successfully!')
        return redirect('manage_finance')
    
    fee_records = FeeRecord.objects.all().order_by('-payment_date')
    students = Student.objects.all()
    
    context = {
        'fee_records': fee_records,
        'students': students,
    }
    return render(request, 'manage_finance.html', context)


# ============= TEACHER VIEWS =============
@login_required
def teacher_dashboard(request):
    try:
        teacher = Teacher.objects.get(user=request.user)
    except:
        messages.error(request, 'Access denied.')
        return redirect('unified_login')
    
    exams = Exam.objects.filter(created_by=teacher).order_by('-created_at')
    submissions = ExamSubmission.objects.filter(exam__created_by=teacher).order_by('-submitted_at')[:10]
    
    context = {
        'teacher': teacher,
        'exams': exams,
        'recent_submissions': submissions,
    }
    return render(request, 'teacher_dashboard.html', context)


@login_required
def create_exam(request):
    try:
        teacher = Teacher.objects.get(user=request.user)
    except:
        messages.error(request, 'Access denied.')
        return redirect('unified_login')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        subject = request.POST.get('subject')
        class_name = request.POST.get('class_name')
        duration = request.POST.get('duration')
        
        exam = Exam.objects.create(
            title=title,
            subject=subject,
            class_name=class_name,
            duration_minutes=duration,
            created_by=teacher
        )
        
        # Log activity
        ActivityLog.objects.create(
            action='exam_created',
            description=f'Exam "{title}" created with ID {exam.exam_id}',
            performed_by_type='teacher',
            performed_by_name=teacher.full_name
        )
        
        messages.success(request, f'Exam created! Exam ID: {exam.exam_id}')
        return redirect('add_questions', exam_id=exam.id)
    
    return render(request, 'create_exam.html')


@login_required
def add_questions(request, exam_id):
    try:
        teacher = Teacher.objects.get(user=request.user)
        exam = Exam.objects.get(id=exam_id, created_by=teacher)
    except:
        messages.error(request, 'Access denied.')
        return redirect('teacher_dashboard')
    
    if request.method == 'POST':
        question_text = request.POST.get('question_text')
        option_a = request.POST.get('option_a')
        option_b = request.POST.get('option_b')
        option_c = request.POST.get('option_c')
        option_d = request.POST.get('option_d')
        correct_answer = request.POST.get('correct_answer')
        
        question_number = exam.questions.count() + 1
        
        Question.objects.create(
            exam=exam,
            question_text=question_text,
            option_a=option_a,
            option_b=option_b,
            option_c=option_c,
            option_d=option_d,
            correct_answer=correct_answer,
            question_number=question_number
        )
        
        if 'add_another' in request.POST:
            messages.success(request, 'Question added! Add another.')
            return redirect('add_questions', exam_id=exam_id)
        else:
            messages.success(request, 'Exam completed successfully!')
            return redirect('teacher_dashboard')
    
    questions = exam.questions.all()
    context = {
        'exam': exam,
        'questions': questions,
    }
    return render(request, 'add_questions.html', context)


@login_required
def mark_attendance(request):
    try:
        teacher = Teacher.objects.get(user=request.user)
    except:
        messages.error(request, 'Access denied.')
        return redirect('unified_login')
    
    if request.method == 'POST':
        class_name = request.POST.get('class_name')
        date = request.POST.get('date')
        students = Student.objects.filter(class_name=class_name)
        
        for student in students:
            status = request.POST.get(f'status_{student.id}')
            if status:
                Attendance.objects.update_or_create(
                    student=student,
                    date=date,
                    defaults={
                        'status': status,
                        'class_name': class_name,
                        'marked_by': teacher
                    }
                )
        
        ActivityLog.objects.create(
            action='attendance_marked',
            description=f'Attendance marked for {class_name} on {date}',
            performed_by_type='teacher',
            performed_by_name=teacher.full_name
        )
        
        messages.success(request, 'Attendance marked successfully!')
        return redirect('mark_attendance')
    
    classes = Student.objects.values_list('class_name', flat=True).distinct()
    selected_class = request.GET.get('class_name')
    students = Student.objects.filter(class_name=selected_class) if selected_class else []
    
    context = {
        'classes': classes,
        'students': students,
        'selected_class': selected_class,
        'today': datetime.now().date(),
    }
    return render(request, 'mark_attendance.html', context)


@login_required
def export_results(request, exam_id):
    try:
        teacher = Teacher.objects.get(user=request.user)
        exam = Exam.objects.get(id=exam_id, created_by=teacher)
    except:
        messages.error(request, 'Access denied.')
        return redirect('teacher_dashboard')
    
    submissions = ExamSubmission.objects.filter(exam=exam)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{exam.title}_results.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Student ID', 'Student Name', 'Score (%)', 'Correct Answers', 'Total Questions', 'Submission Date'])
    
    for sub in submissions:
        writer.writerow([
            sub.student.student_id,
            sub.student.full_name,
            sub.score,
            sub.correct_answers,
            sub.total_questions,
            sub.submitted_at.strftime('%Y-%m-%d %H:%M')
        ])
    
    return response


# ============= STUDENT VIEWS =============
@login_required
def student_dashboard(request):
    try:
        student = Student.objects.get(user=request.user)
    except:
        messages.error(request, 'Access denied.')
        return redirect('unified_login')
    
    submissions = ExamSubmission.objects.filter(student=student).order_by('-submitted_at')
    available_exams = Exam.objects.filter(class_name=student.class_name, is_active=True)
    
    # Filter out already taken exams
    taken_exam_ids = submissions.values_list('exam_id', flat=True)
    available_exams = available_exams.exclude(id__in=taken_exam_ids)
    
    context = {
        'student': student,
        'submissions': submissions,
        'available_exams': available_exams,
    }
    return render(request, 'student_dashboard.html', context)


@login_required
def student_profile(request):
    try:
        student = Student.objects.get(user=request.user)
    except:
        messages.error(request, 'Access denied.')
        return redirect('unified_login')
    
    if request.method == 'POST' and request.FILES.get('profile_picture'):
        student.profile_picture = request.FILES['profile_picture']
        student.save()
        messages.success(request, 'Profile picture updated!')
        return redirect('student_profile')
    
    context = {'student': student}
    return render(request, 'student_profile.html', context)


@login_required
def take_exam(request, exam_id):
    try:
        student = Student.objects.get(user=request.user)
        exam = Exam.objects.get(exam_id=exam_id, class_name=student.class_name, is_active=True)
        
        # Check if already taken
        if ExamSubmission.objects.filter(student=student, exam=exam).exists():
            messages.error(request, 'You have already taken this exam.')
            return redirect('student_dashboard')
    except:
        messages.error(request, 'Invalid exam ID or access denied.')
        return redirect('student_dashboard')
    
    questions = exam.questions.all()
    
    if request.method == 'POST':
        # Create submission
        submission = ExamSubmission.objects.create(
            student=student,
            exam=exam,
            total_questions=questions.count(),
            correct_answers=0,
            score=0
        )
        
        correct_count = 0
        
        # Process answers
        for question in questions:
            selected = request.POST.get(f'question_{question.id}')
            if selected:
                is_correct = (selected == question.correct_answer)
                if is_correct:
                    correct_count += 1
                
                StudentAnswer.objects.create(
                    submission=submission,
                    question=question,
                    selected_answer=selected,
                    is_correct=is_correct
                )
        
        # Calculate score
        score = (correct_count / questions.count()) * 100
        submission.correct_answers = correct_count
        submission.score = round(score, 2)
        submission.save()
        
        # Log activity
        ActivityLog.objects.create(
            action='exam_submitted',
            description=f'{student.full_name} submitted {exam.title} - Score: {score}%',
            performed_by_type='student',
            performed_by_name=student.full_name
        )
        
        messages.success(request, f'Exam submitted! Your score: {score}%')
        return redirect('view_result', submission_id=submission.id)
    
    context = {
        'exam': exam,
        'questions': questions,
    }
    return render(request, 'take_exam.html', context)


@login_required
def view_result(request, submission_id):
    try:
        student = Student.objects.get(user=request.user)
        submission = ExamSubmission.objects.get(id=submission_id, student=student)
    except:
        messages.error(request, 'Result not found.')
        return redirect('student_dashboard')
    
    answers = submission.answers.all()
    
    context = {
        'submission': submission,
        'answers': answers,
    }
    return render(request, 'view_result.html', context)