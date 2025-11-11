from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q, Sum, Avg
from django.http import JsonResponse, HttpResponse
from .models import *
import csv
from datetime import datetime
import random
from django.core.management import call_command

# ============= UNIFIED LOGIN (Updated with Principal & Bursar) =============
def unified_login(request):
    if request.method == 'POST':
        role = request.POST.get('role')
        user_id = request.POST.get('user_id')
        
        try:
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
            elif role == 'principal':
                principal = Principal.objects.get(principal_id=user_id)
                user = principal.user
                login(request, user)
                return redirect('principal_dashboard')
            elif role == 'bursar':
                bursar = Bursar.objects.get(bursar_id=user_id)
                user = bursar.user
                login(request, user)
                return redirect('bursar_dashboard')
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
    
    students = Student.objects.all().order_by('-created_at')
    teachers = Teacher.objects.all().order_by('-created_at')
    recent_activities = ActivityLog.objects.all()[:20]
    total_fees = FeeRecord.objects.aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
    
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
        try:
            principal = Principal.objects.get(user=request.user)
        except:
            messages.error(request, 'Access denied.')
            return redirect('unified_login')
    
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')  # Optional now
        phone = request.POST.get('phone')  # Optional now
        class_name = request.POST.get('class_name')
        
        username = full_name.replace(' ', '').lower() + str(random.randint(100, 999))
        user = User.objects.create_user(username=username, email=email if email else '')
        
        student = Student.objects.create(
            user=user,
            full_name=full_name,
            email=email if email else None,
            phone=phone if phone else None,
            class_name=class_name,
            registered_by=admin if 'admin' in request.path else None
        )
        
        ActivityLog.objects.create(
            action='student_registered',
            description=f'Student {full_name} registered with ID {student.student_id}',
            performed_by_type='admin' if 'admin' in request.path else 'principal',
            performed_by_name=admin.full_name if 'admin' in request.path else principal.full_name
        )
        
        messages.success(request, f'Student registered successfully! Student ID: {student.student_id}')
        return redirect('admin_dashboard' if 'admin' in request.path else 'principal_dashboard')
    
    return render(request, 'register_student.html')


# NEW: Move Student to Alumni
@login_required
def move_to_alumni(request, student_id):
    try:
        admin = Admin.objects.get(user=request.user)
    except:
        messages.error(request, 'Access denied.')
        return redirect('unified_login')
    
    if request.method == 'POST':
        student = Student.objects.get(id=student_id)
        reason = request.POST.get('reason')
        year_left = request.POST.get('year_left')
        current_institution = request.POST.get('current_institution')
        notes = request.POST.get('notes')
        
        # Create Alumni record
        Alumni.objects.create(
            student_id=student.student_id,
            full_name=student.full_name,
            email=student.email,
            phone=student.phone,
            last_class=student.class_name,
            profile_picture=student.profile_picture,
            reason=reason,
            year_left=year_left,
            current_institution=current_institution,
            notes=notes,
            original_registration_date=student.created_at,
            moved_by=admin
        )
        
        # Delete user account (this removes student from active list)
        student_name = student.full_name
        student.user.delete()
        
        ActivityLog.objects.create(
            action='student_deleted',
            description=f'Student {student_name} moved to Alumni - {reason}',
            performed_by_type='admin',
            performed_by_name=admin.full_name
        )
        
        messages.success(request, f'{student_name} successfully moved to Alumni!')
        return redirect('admin_dashboard')
    
    student = Student.objects.get(id=student_id)
    context = {'student': student}
    return render(request, 'move_to_alumni.html', context)


# NEW: View Alumni
@login_required
def view_alumni(request):
    try:
        admin = Admin.objects.get(user=request.user)
    except:
        try:
            principal = Principal.objects.get(user=request.user)
        except:
            messages.error(request, 'Access denied.')
            return redirect('unified_login')
    
    alumni_list = Alumni.objects.all().order_by('-moved_on')
    
    context = {
        'alumni_list': alumni_list,
    }
    return render(request, 'view_alumni.html', context)


@login_required
def register_teacher(request):
    try:
        admin = Admin.objects.get(user=request.user)
    except:
        try:
            principal = Principal.objects.get(user=request.user)
        except:
            messages.error(request, 'Access denied.')
            return redirect('unified_login')
    
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        subject = request.POST.get('subject')
        
        username = email.split('@')[0] + str(random.randint(100, 999))
        user = User.objects.create_user(username=username, email=email)
        
        teacher = Teacher.objects.create(
            user=user,
            full_name=full_name,
            email=email,
            phone=phone,
            subject=subject,
            registered_by=admin if 'admin' in request.path else None
        )
        
        ActivityLog.objects.create(
            action='teacher_registered',
            description=f'Teacher {full_name} registered with ID {teacher.teacher_id}',
            performed_by_type='admin' if 'admin' in request.path else 'principal',
            performed_by_name=admin.full_name if 'admin' in request.path else principal.full_name
        )
        
        messages.success(request, f'Teacher registered successfully! Teacher ID: {teacher.teacher_id}')
        return redirect('admin_dashboard' if 'admin' in request.path else 'principal_dashboard')
    
    return render(request, 'register_teacher.html')


@login_required
def delete_student(request, student_id):
    try:
        admin = Admin.objects.get(user=request.user)
        student = Student.objects.get(id=student_id)
        student_name = student.full_name
        student.user.delete()
        
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
        teacher.user.delete()
        
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
        is_admin = True
        user_name = admin.full_name
    except:
        try:
            bursar = Bursar.objects.get(user=request.user)
            is_admin = False
            user_name = bursar.full_name
        except:
            messages.error(request, 'Access denied.')
            return redirect('unified_login')
    
    if request.method == 'POST':
        try:
            student_id = request.POST.get('student_id')
            total_fee = float(request.POST.get('total_fee'))
            amount_paid = float(request.POST.get('amount_paid'))
            fee_type = request.POST.get('fee_type')
            payment_method = request.POST.get('payment_method')
            payment_date = request.POST.get('payment_date')
            
            student = Student.objects.get(student_id=student_id)
            current_term = Term.objects.filter(is_current=True).first()
            
            fee_record = FeeRecord.objects.create(
                student=student,
                term=current_term,
                total_fee=total_fee,
                amount_paid=amount_paid,
                fee_type=fee_type,
                payment_method=payment_method,
                payment_date=payment_date,
                recorded_by=None if is_admin else bursar,
                recorded_by_admin=admin if is_admin else None
            )
            
            ActivityLog.objects.create(
                action='fee_recorded',
                description=f'Fee payment of ₦{amount_paid} recorded for {student.full_name}',
                performed_by_type='admin' if is_admin else 'bursar',
                performed_by_name=user_name
            )
            
            messages.success(request, '✅ PAYMENT RECORDED SUCCESSFULLY!')
            return redirect('bursar_dashboard' if not is_admin else 'manage_finance')
        except Exception as e:
            messages.error(request, f'Error recording payment: {str(e)}')
            return redirect('manage_finance')
    
    fee_records = FeeRecord.objects.all().order_by('-payment_date')
    students = Student.objects.all()
    
    context = {
        'fee_records': fee_records,
        'students': students,
        'is_admin': is_admin,
    }
    return render(request, 'manage_finance.html', context)


# ============= PRINCIPAL VIEWS =============
@login_required
def principal_dashboard(request):
    try:
        principal = Principal.objects.get(user=request.user)
    except:
        messages.error(request, 'Access denied.')
        return redirect('unified_login')
    
    students = Student.objects.all().order_by('-created_at')
    teachers = Teacher.objects.all().order_by('-created_at')
    
    context = {
        'principal': principal,
        'students': students,
        'teachers': teachers,
        'student_count': students.count(),
        'teacher_count': teachers.count(),
    }
    return render(request, 'principal_dashboard.html', context)


# ============= BURSAR VIEWS =============
@login_required
def bursar_dashboard(request):
    try:
        bursar = Bursar.objects.get(user=request.user)
    except:
        messages.error(request, 'Access denied.')
        return redirect('unified_login')
    
    fee_records = FeeRecord.objects.all().order_by('-payment_date')
    students = Student.objects.all()
    total_fees = FeeRecord.objects.aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
    total_balance = FeeRecord.objects.aggregate(Sum('balance'))['balance__sum'] or 0
    recent_activities = ActivityLog.objects.filter(performed_by_type='bursar')[:20]
    
    context = {
        'bursar': bursar,
        'fee_records': fee_records,
        'students': students,
        'total_fees': total_fees,
        'total_balance': total_balance,
        'activities': recent_activities,
    }
    return render(request, 'bursar_dashboard.html', context)


# ============= TEACHER VIEWS =============
@login_required
def teacher_dashboard(request):
    try:
        teacher = Teacher.objects.get(user=request.user)
    except:
        messages.error(request, 'Access denied.')
        return redirect('unified_login')
    
    # Separate published and draft exams (THIS IS THE KEY CHANGE!)
    published_exams = Exam.objects.filter(created_by=teacher, is_published=True).order_by('-created_at')
    draft_exams = Exam.objects.filter(created_by=teacher, is_published=False).order_by('-created_at')
    
    submissions = ExamSubmission.objects.filter(exam__created_by=teacher).order_by('-submitted_at')[:10]
    
    context = {
        'teacher': teacher,
        'published_exams': published_exams,
        'draft_exams': draft_exams,
        'recent_submissions': submissions,
        'total_exams': published_exams.count() + draft_exams.count(),
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
            created_by=teacher,
            shuffle_questions=True,
            is_published=False  # NEW: Start as draft!
        )
        
        ActivityLog.objects.create(
            action='exam_created',
            description=f'Exam "{title}" created as DRAFT with ID {exam.exam_id}',
            performed_by_type='teacher',
            performed_by_name=teacher.full_name
        )
        
        messages.success(request, f'✅ Exam created as DRAFT! Add questions then publish. Exam ID: {exam.exam_id}')
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


# NEW: Edit Question
@login_required
def edit_question(request, question_id):
    try:
        teacher = Teacher.objects.get(user=request.user)
        question = Question.objects.get(id=question_id, exam__created_by=teacher)
    except:
        messages.error(request, 'Access denied.')
        return redirect('teacher_dashboard')
    
    if request.method == 'POST':
        question.question_text = request.POST.get('question_text')
        question.option_a = request.POST.get('option_a')
        question.option_b = request.POST.get('option_b')
        question.option_c = request.POST.get('option_c')
        question.option_d = request.POST.get('option_d')
        question.correct_answer = request.POST.get('correct_answer')
        question.save()
        
        messages.success(request, 'Question updated successfully!')
        return redirect('add_questions', exam_id=question.exam.id)
    
    context = {'question': question}
    return render(request, 'edit_question.html', context)


# NEW: Delete Exam
@login_required
def delete_exam(request, exam_id):
    try:
        teacher = Teacher.objects.get(user=request.user)
        exam = Exam.objects.get(id=exam_id, created_by=teacher)
        exam_title = exam.title
        exam.delete()
        
        ActivityLog.objects.create(
            action='exam_deleted',
            description=f'Exam "{exam_title}" deleted',
            performed_by_type='teacher',
            performed_by_name=teacher.full_name
        )
        
        messages.success(request, 'Exam deleted successfully!')
    except:
        messages.error(request, 'Error deleting exam.')
    
    return redirect('teacher_dashboard')


@login_required
def mark_attendance(request):
    try:
        teacher = Teacher.objects.get(user=request.user)
    except:
        messages.error(request, 'Access denied.')
        return redirect('unified_login')
    
    if request.method == 'POST':
        try:
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
            
            messages.success(request, '✅ Attendance saved successfully!')
            return redirect('mark_attendance')
        except Exception as e:
            messages.error(request, f'Error saving attendance: {str(e)}')
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


# NEW: View Attendance Records
@login_required
def view_attendance(request):
    try:
        teacher = Teacher.objects.get(user=request.user)
    except:
        messages.error(request, 'Access denied.')
        return redirect('unified_login')
    
    # Get filters
    filter_class = request.GET.get('class_name')
    filter_date = request.GET.get('date')
    
    # Build query
    attendance_records = Attendance.objects.all().order_by('-date')
    
    if filter_class:
        attendance_records = attendance_records.filter(class_name=filter_class)
    
    if filter_date:
        attendance_records = attendance_records.filter(date=filter_date)
    
    classes = Student.objects.values_list('class_name', flat=True).distinct()
    
    context = {
        'teacher': teacher,
        'attendance_records': attendance_records,
        'classes': classes,
        'filter_class': filter_class,
        'filter_date': filter_date,
    }
    return render(request, 'view_attendance.html', context)



# ============= STUDENT VIEWS =============
@login_required
def student_dashboard(request):
    try:
        student = Student.objects.get(user=request.user)
    except:
        messages.error(request, 'Access denied.')
        return redirect('unified_login')
    
    submissions = ExamSubmission.objects.filter(student=student).order_by('-submitted_at')
    
    # ONLY SHOW PUBLISHED EXAMS (THIS IS THE CRITICAL CHANGE!)
    available_exams = Exam.objects.filter(
        class_name=student.class_name, 
        is_active=True,
        is_published=True  # NEW: Only published exams visible to students!
    )
    
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
    
    if request.method == 'POST':
        if request.FILES.get('profile_picture'):
            student.profile_picture = request.FILES['profile_picture']
            student.save()
            messages.success(request, '✅ Profile picture updated successfully!')
            return redirect('student_profile')
        else:
            messages.error(request, 'Please select a picture to upload.')
    
    context = {'student': student}
    return render(request, 'student_profile.html', context)


@login_required
def take_exam(request, exam_id):
    try:
        student = Student.objects.get(user=request.user)
        exam = Exam.objects.get(exam_id=exam_id, class_name=student.class_name, is_active=True)
        
        if ExamSubmission.objects.filter(student=student, exam=exam).exists():
            messages.error(request, 'You have already taken this exam.')
            return redirect('student_dashboard')
    except:
        messages.error(request, 'Invalid exam ID or access denied.')
        return redirect('student_dashboard')
    
    # SHUFFLE QUESTIONS FOR EACH STUDENT
    questions = list(exam.questions.all())
    if exam.shuffle_questions:
        random.shuffle(questions)
    
    if request.method == 'POST':
        submission = ExamSubmission.objects.create(
            student=student,
            exam=exam,
            total_questions=len(questions),
            correct_answers=0,
            score=0
        )
        
        correct_count = 0
        
        for question in exam.questions.all():
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
        
        score = (correct_count / len(questions)) * 100
        submission.correct_answers = correct_count
        submission.score = round(score, 2)
        submission.save()
        
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
    
    # DON'T show answers anymore (as requested)
    context = {
        'submission': submission,
    }
    return render(request, 'view_result_simple.html', context)


    # ============= FEATURE 1: DELETE INDIVIDUAL QUESTION =============
@login_required
def delete_single_question(request, exam_id, question_number):
    """Delete a specific question by its number"""
    try:
        teacher = Teacher.objects.get(user=request.user)
        exam = Exam.objects.get(id=exam_id, created_by=teacher)
    except:
        messages.error(request, 'Access denied.')
        return redirect('teacher_dashboard')
    
    if request.method == 'POST':
        try:
            # Get the specific question to delete
            question = Question.objects.get(exam=exam, question_number=question_number)
            question.delete()
            
            # Renumber remaining questions
            remaining_questions = Question.objects.filter(exam=exam).order_by('question_number')
            for idx, q in enumerate(remaining_questions, 1):
                q.question_number = idx
                q.save()
            
            ActivityLog.objects.create(
                action='exam_edited',
                description=f'Question {question_number} deleted from "{exam.title}"',
                performed_by_type='teacher',
                performed_by_name=teacher.full_name
            )
            
            messages.success(request, f'✅ Question {question_number} deleted successfully!')
        except Exception as e:
            messages.error(request, f'Error deleting question: {str(e)}')
    
    return redirect('add_questions', exam_id=exam_id)


# ============= FEATURE 2: DELETE STUDENT WITH CONFIRMATION =============
@login_required
def delete_student_confirm(request, student_id):
    """Show confirmation page before permanently deleting student"""
    try:
        admin = Admin.objects.get(user=request.user)
        admin_name = admin.full_name
        is_admin = True
    except:
        try:
            principal = Principal.objects.get(user=request.user)
            admin_name = principal.full_name
            is_admin = False
        except:
            messages.error(request, 'Access denied.')
            return redirect('unified_login')
    
    student = get_object_or_404(Student, id=student_id)
    
    if request.method == 'POST':
        student_name = student.full_name
        student_id_num = student.student_id
        
        # Permanently delete student (cascades to all related records)
        student.user.delete()
        
        ActivityLog.objects.create(
            action='student_deleted',
            description=f'Student {student_name} ({student_id_num}) permanently deleted',
            performed_by_type='admin' if is_admin else 'principal',
            performed_by_name=admin_name
        )
        
        messages.success(request, f'✅ Student {student_name} has been permanently deleted!')
        return redirect('admin_dashboard' if is_admin else 'principal_dashboard')
    
    context = {'student': student}
    return render(request, 'confirm_delete_student.html', context)


# ============= FEATURE 3: SEARCH STUDENTS =============
@login_required
def search_students(request):
    """Search students by name or ID"""
    try:
        admin = Admin.objects.get(user=request.user)
        is_admin = True
    except:
        try:
            principal = Principal.objects.get(user=request.user)
            is_admin = False
        except:
            messages.error(request, 'Access denied.')
            return redirect('unified_login')
    
    query = request.GET.get('q', '')
    students = Student.objects.all()
    
    if query:
        students = students.filter(
            Q(full_name__icontains=query) | 
            Q(student_id__icontains=query) |
            Q(email__icontains=query)
        ).order_by('-created_at')
    
    teachers = Teacher.objects.all().order_by('-created_at')
    recent_activities = ActivityLog.objects.all()[:20] if is_admin else []
    total_fees = FeeRecord.objects.aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0 if is_admin else 0
    
    context = {
        'admin': admin if is_admin else None,
        'principal': principal if not is_admin else None,
        'students': students,
        'teachers': teachers,
        'activities': recent_activities,
        'total_fees': total_fees,
        'student_count': students.count(),
        'teacher_count': teachers.count(),
        'search_query': query,
    }
    
    template = 'admin_dashboard.html' if is_admin else 'principal_dashboard.html'
    return render(request, template, context)


# ============= FEATURE 3: SEARCH TEACHERS =============
@login_required
def search_teachers(request):
    """Search teachers by name or email"""
    try:
        admin = Admin.objects.get(user=request.user)
        is_admin = True
    except:
        try:
            principal = Principal.objects.get(user=request.user)
            is_admin = False
        except:
            messages.error(request, 'Access denied.')
            return redirect('unified_login')
    
    query = request.GET.get('q', '')
    teachers = Teacher.objects.all()
    
    if query:
        teachers = teachers.filter(
            Q(full_name__icontains=query) | 
            Q(email__icontains=query) |
            Q(teacher_id__icontains=query) |
            Q(subject__icontains=query)
        ).order_by('-created_at')
    
    students = Student.objects.all().order_by('-created_at')
    recent_activities = ActivityLog.objects.all()[:20] if is_admin else []
    total_fees = FeeRecord.objects.aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0 if is_admin else 0
    
    context = {
        'admin': admin if is_admin else None,
        'principal': principal if not is_admin else None,
        'students': students,
        'teachers': teachers,
        'activities': recent_activities,
        'total_fees': total_fees,
        'student_count': students.count(),
        'teacher_count': teachers.count(),
        'search_query': query,
    }
    
    template = 'admin_dashboard.html' if is_admin else 'principal_dashboard.html'
    return render(request, template, context)


# ============= FEATURE 4: PUBLISH/UNPUBLISH EXAM =============
@login_required
def toggle_exam_publish(request, exam_id):
    """Toggle exam publish status (Draft <-> Published)"""
    try:
        teacher = Teacher.objects.get(user=request.user)
        exam = Exam.objects.get(id=exam_id, created_by=teacher)
    except:
        messages.error(request, 'Access denied.')
        return redirect('teacher_dashboard')
    
    if request.method == 'POST':
        exam.is_published = not exam.is_published
        exam.save()
        
        status = "published ✅" if exam.is_published else "unpublished (moved to drafts) 📝"
        
        ActivityLog.objects.create(
            action='exam_edited',
            description=f'Exam "{exam.title}" {status}',
            performed_by_type='teacher',
            performed_by_name=teacher.full_name
        )
        
        messages.success(request, f'Exam "{exam.title}" has been {status}!')
    
    return redirect('teacher_dashboard')




    # ============================================================================
# ADD THESE VIEWS TO YOUR views.py FILE
# PART 1: Make Result Portal & Subject Teacher Entry
# ============================================================================

from django.utils import timezone

# Make Result Portal - Role Selection
@login_required
def make_result_portal(request):
    """Landing page for Make Result - shows role tabs"""
    return render(request, 'result/make_result_portal.html')


# Subject Teacher - Enter Results for Their Subject
@login_required
def subject_teacher_entry(request):
    """Subject teachers enter results for their subject across all classes"""
    try:
        teacher = Teacher.objects.get(user=request.user)
    except:
        messages.error(request, 'Access denied. Teachers only.')
        return redirect('unified_login')
    
    if request.method == 'POST':
        try:
            # Get form data
            subject_name = request.POST.get('subject_name')
            term = request.POST.get('term')
            academic_year = request.POST.get('academic_year')
            student_ids = request.POST.getlist('student_id')
            
            # Save results for each student
            for student_id in student_ids:
                student = Student.objects.get(id=student_id)
                
                test_a = float(request.POST.get(f'test_a_{student_id}', 0))
                test_b = float(request.POST.get(f'test_b_{student_id}', 0))
                test_c = float(request.POST.get(f'test_c_{student_id}', 0))
                exam = float(request.POST.get(f'exam_{student_id}', 0))
                ltcum = float(request.POST.get(f'ltcum_{student_id}', 0))
                atcum = float(request.POST.get(f'atcum_{student_id}', 0))
                
                SubjectResult.objects.update_or_create(
                    student=student,
                    subject_name=subject_name,
                    term=term,
                    academic_year=academic_year,
                    defaults={
                        'test_a': test_a,
                        'test_b': test_b,
                        'test_c': test_c,
                        'exam': exam,
                        'ltcum': ltcum,
                        'atcum': atcum,
                        'entered_by': teacher,
                    }
                )
            
            ResultActivityLog.objects.create(
                action='subject_result_entered',
                description=f'{teacher.full_name} entered {subject_name} results for {term}',
                performed_by_type='teacher',
                performed_by_name=teacher.full_name
            )
            
            messages.success(request, f'✅ Results saved for {subject_name}!')
            return redirect('subject_teacher_entry')
            
        except Exception as e:
            messages.error(request, f'Error saving results: {str(e)}')
            return redirect('subject_teacher_entry')
    
    # GET request - show form
    classes = Student.objects.values_list('class_name', flat=True).distinct()
    selected_class = request.GET.get('class_name')
    students = Student.objects.filter(class_name=selected_class).order_by('full_name') if selected_class else []
    
    # Get existing results if any
    subject_name = request.GET.get('subject_name')
    term = request.GET.get('term')
    existing_results = {}
    if subject_name and term and selected_class:
        for student in students:
            try:
                result = SubjectResult.objects.get(
                    student=student,
                    subject_name=subject_name,
                    term=term
                )
                existing_results[student.id] = result
            except SubjectResult.DoesNotExist:
                pass
    
    context = {
        'teacher': teacher,
        'classes': classes,
        'selected_class': selected_class,
        'students': students,
        'existing_results': existing_results,
        'subject_name': subject_name,
        'term': term,
    }
    return render(request, 'result/subject_teacher_entry.html', context)


# Calculate Class Positions for a Subject
def calculate_subject_positions(subject_name, term, academic_year, class_name):
    """Calculate position rankings and class average for a subject"""
    results = SubjectResult.objects.filter(
        subject_name=subject_name,
        term=term,
        academic_year=academic_year,
        student__class_name=class_name
    ).order_by('-avg_2')
    
    if not results.exists():
        return
    
    # Calculate class average
    total_score = sum([r.avg_2 for r in results])
    class_average = total_score / results.count()
    
    # Assign positions
    for position, result in enumerate(results, 1):
        result.position_ranking = position
        result.class_average = round(class_average, 2)
        result.save()




    # ============================================================================
# PART 2: Class Teacher Functions
# ============================================================================

# Class Teacher - Collate Results
@login_required
def class_teacher_collate(request):
    """Class teachers collate subject results for their class"""
    try:
        teacher = Teacher.objects.get(user=request.user)
    except:
        messages.error(request, 'Access denied. Teachers only.')
        return redirect('unified_login')
    
    # Get class teacher's class
    selected_class = request.GET.get('class_name')
    term = request.GET.get('term')
    academic_year = request.GET.get('academic_year')
    
    if request.method == 'POST':
        try:
            student_id = request.POST.get('student_id')
            student = Student.objects.get(id=student_id)
            
            # Create or update student result
            result, created = StudentResult.objects.get_or_create(
                student=student,
                term=term,
                academic_year=academic_year,
                defaults={
                    'class_name': student.class_name,
                    'class_teacher': teacher,
                }
            )
            
            # Update attendance and fees
            result.times_school_opened = int(request.POST.get('times_opened', 0))
            result.times_present = int(request.POST.get('times_present', 0))
            result.times_absent = int(request.POST.get('times_absent', 0))
            result.vacation_date = request.POST.get('vacation_date')
            result.resumption_date = request.POST.get('resumption_date')
            result.next_term_pta_fee = float(request.POST.get('pta_fee', 0))
            result.next_term_school_fee = float(request.POST.get('school_fee', 0))
            
            # Affective domain
            result.affective_punctuality = request.POST.get('aff_punctuality', '')
            result.affective_neatness = request.POST.get('aff_neatness', '')
            result.affective_politeness = request.POST.get('aff_politeness', '')
            result.affective_honesty = request.POST.get('aff_honesty', '')
            result.affective_relationship = request.POST.get('aff_relationship', '')
            result.affective_self_control = request.POST.get('aff_self_control', '')
            result.affective_attentiveness = request.POST.get('aff_attentiveness', '')
            
            # Psychomotor domain
            result.psycho_handwriting = request.POST.get('psycho_handwriting', '')
            result.psycho_sports = request.POST.get('psycho_sports', '')
            result.psycho_handling_tools = request.POST.get('psycho_tools', '')
            result.psycho_verbal_fluency = request.POST.get('psycho_verbal', '')
            result.psycho_games = request.POST.get('psycho_games', '')
            result.psycho_drawing = request.POST.get('psycho_drawing', '')
            
            # Class teacher comment
            result.class_teacher_comment = request.POST.get('class_teacher_comment', '')
            result.class_teacher = teacher
            
            # Calculate totals
            subject_results = SubjectResult.objects.filter(
                student=student,
                term=term,
                academic_year=academic_year
            )
            
            result.total_subjects = subject_results.count()
            result.score_gained = sum([sr.avg_2 for sr in subject_results])
            result.average_score = result.score_gained / result.total_subjects if result.total_subjects > 0 else 0
            result.status_promotion = "PROMOTED" if result.average_score >= 50 else "REPEAT"
            
            result.save()
            
            ResultActivityLog.objects.create(
                action='result_collated',
                description=f'Result collated for {student.full_name}',
                student_result=result,
                performed_by_type='teacher',
                performed_by_name=teacher.full_name
            )
            
            messages.success(request, f'✅ Result collated for {student.full_name}!')
            return redirect('class_teacher_collate')
            
        except Exception as e:
            messages.error(request, f'Error saving result: {str(e)}')
            return redirect('class_teacher_collate')
    
    # GET request
    students = Student.objects.filter(class_name=selected_class).order_by('full_name') if selected_class else []
    
    # Get existing results
    results = []
    if selected_class and term and academic_year:
        for student in students:
            try:
                result = StudentResult.objects.get(
                    student=student,
                    term=term,
                    academic_year=academic_year
                )
                # Get subject results count
                subject_count = SubjectResult.objects.filter(
                    student=student,
                    term=term,
                    academic_year=academic_year
                ).count()
                results.append({
                    'student': student,
                    'result': result,
                    'subject_count': subject_count,
                })
            except StudentResult.DoesNotExist:
                # Check if student has any subject results
                subject_count = SubjectResult.objects.filter(
                    student=student,
                    term=term,
                    academic_year=academic_year
                ).count()
                results.append({
                    'student': student,
                    'result': None,
                    'subject_count': subject_count,
                })
    
    classes = Student.objects.values_list('class_name', flat=True).distinct()
    
    context = {
        'teacher': teacher,
        'classes': classes,
        'selected_class': selected_class,
        'term': term,
        'academic_year': academic_year,
        'results': results,
    }
    return render(request, 'result/class_teacher_collate.html', context)


# Class Teacher - Edit Specific Result
@login_required
def class_teacher_edit_result(request, result_id):
    """Edit a specific student's result"""
    try:
        teacher = Teacher.objects.get(user=request.user)
        result = StudentResult.objects.get(id=result_id, class_teacher=teacher)
    except:
        messages.error(request, 'Access denied.')
        return redirect('class_teacher_collate')
    
    # Get subject results for this student
    subject_results = SubjectResult.objects.filter(
        student=result.student,
        term=result.term,
        academic_year=result.academic_year
    ).order_by('subject_name')
    
    if request.method == 'POST':
        # Update result (same as collate but for editing)
        # ... (similar code to collate)
        messages.success(request, 'Result updated!')
        return redirect('class_teacher_collate')
    
    context = {
        'result': result,
        'subject_results': subject_results,
        'teacher': teacher,
    }
    return render(request, 'result/edit_result.html', context)


# Send Single Result to Principal
@login_required
def send_result_to_principal(request, result_id):
    """Send single result to principal"""
    try:
        teacher = Teacher.objects.get(user=request.user)
        result = StudentResult.objects.get(id=result_id, class_teacher=teacher)
        
        result.status = 'sent_to_principal'
        result.sent_to_principal_at = timezone.now()
        result.save()
        
        ResultActivityLog.objects.create(
            action='sent_to_principal',
            description=f'Result for {result.student.full_name} sent to Principal',
            student_result=result,
            performed_by_type='teacher',
            performed_by_name=teacher.full_name
        )
        
        messages.success(request, f'✅ Result sent to Principal!')
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
    
    return redirect('class_teacher_collate')


# Send Batch Results to Principal
@login_required
def send_batch_to_principal(request):
    """Send entire class results to principal at once"""
    if request.method == 'POST':
        try:
            teacher = Teacher.objects.get(user=request.user)
            result_ids = request.POST.getlist('result_ids')
            
            count = 0
            for result_id in result_ids:
                result = StudentResult.objects.get(id=result_id, class_teacher=teacher)
                result.status = 'sent_to_principal'
                result.sent_to_principal_at = timezone.now()
                result.save()
                count += 1
            
            ResultActivityLog.objects.create(
                action='sent_to_principal',
                description=f'{count} results sent to Principal by {teacher.full_name}',
                performed_by_type='teacher',
                performed_by_name=teacher.full_name
            )
            
            messages.success(request, f'✅ {count} results sent to Principal!')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    
    return redirect('class_teacher_collate')





    # ============================================================================
# PART 3: Principal & Admin Functions
# ============================================================================

# Principal - Review Results
@login_required
def principal_result_review(request):
    """Principal reviews incoming results"""
    try:
        principal = Principal.objects.get(user=request.user)
    except:
        messages.error(request, 'Access denied. Principal only.')
        return redirect('unified_login')
    
    # Get incoming results
    incoming_results = StudentResult.objects.filter(
        status='sent_to_principal'
    ).order_by('class_name', 'student__full_name')
    
    context = {
        'principal': principal,
        'incoming_results': incoming_results,
    }
    return render(request, 'result/principal_review.html', context)


# Principal - Add Comment
@login_required
def principal_add_comment(request, result_id):
    """Principal adds comment to result"""
    try:
        principal = Principal.objects.get(user=request.user)
        result = StudentResult.objects.get(id=result_id, status='sent_to_principal')
    except:
        messages.error(request, 'Access denied.')
        return redirect('principal_result_review')
    
    if request.method == 'POST':
        result.principal_comment = request.POST.get('principal_comment')
        result.principal = principal
        result.save()
        
        ResultActivityLog.objects.create(
            action='principal_commented',
            description=f'Principal commented on {result.student.full_name} result',
            student_result=result,
            performed_by_type='principal',
            performed_by_name=principal.full_name
        )
        
        messages.success(request, 'Comment saved!')
        return redirect('principal_result_review')
    
    # Get subject results
    subject_results = SubjectResult.objects.filter(
        student=result.student,
        term=result.term,
        academic_year=result.academic_year
    ).order_by('subject_name')
    
    context = {
        'result': result,
        'subject_results': subject_results,
        'principal': principal,
    }
    return render(request, 'result/principal_add_comment.html', context)


# Principal - Send to Admin
@login_required
def send_result_to_admin(request, result_id):
    """Send single result to admin"""
    try:
        principal = Principal.objects.get(user=request.user)
        result = StudentResult.objects.get(id=result_id)
        
        result.status = 'sent_to_admin'
        result.sent_to_admin_at = timezone.now()
        result.save()
        
        ResultActivityLog.objects.create(
            action='sent_to_admin',
            description=f'Result for {result.student.full_name} sent to Admin',
            student_result=result,
            performed_by_type='principal',
            performed_by_name=principal.full_name
        )
        
        messages.success(request, 'Result sent to Admin!')
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
    
    return redirect('principal_result_review')


# Principal - Send Batch to Admin
@login_required
def send_batch_to_admin(request):
    """Send multiple results to admin at once"""
    if request.method == 'POST':
        try:
            principal = Principal.objects.get(user=request.user)
            result_ids = request.POST.getlist('result_ids')
            
            count = 0
            for result_id in result_ids:
                result = StudentResult.objects.get(id=result_id)
                result.status = 'sent_to_admin'
                result.sent_to_admin_at = timezone.now()
                result.save()
                count += 1
            
            ResultActivityLog.objects.create(
                action='sent_to_admin',
                description=f'{count} results sent to Admin by {principal.full_name}',
                performed_by_type='principal',
                performed_by_name=principal.full_name
            )
            
            messages.success(request, f'✅ {count} results sent to Admin!')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    
    return redirect('principal_result_review')


# Admin - Result Management
@login_required
def admin_result_management(request):
    """Admin views all incoming results by class"""
    try:
        admin = Admin.objects.get(user=request.user)
    except:
        messages.error(request, 'Access denied. Admin only.')
        return redirect('unified_login')
    
    # Get results grouped by class
    incoming_results = StudentResult.objects.filter(
        status='sent_to_admin'
    ).order_by('class_name', 'student__full_name')
    
    # Group by class
    results_by_class = {}
    for result in incoming_results:
        if result.class_name not in results_by_class:
            results_by_class[result.class_name] = []
        results_by_class[result.class_name].append(result)
    
    context = {
        'admin': admin,
        'results_by_class': results_by_class,
    }
    return render(request, 'result/admin_management.html', context)


# Admin - Edit Result (Full Permission)
@login_required
def admin_edit_result(request, result_id):
    """Admin can edit everything in the result"""
    try:
        admin = Admin.objects.get(user=request.user)
        result = StudentResult.objects.get(id=result_id)
    except:
        messages.error(request, 'Access denied.')
        return redirect('admin_result_management')
    
    # Get subject results
    subject_results = SubjectResult.objects.filter(
        student=result.student,
        term=result.term,
        academic_year=result.academic_year
    ).order_by('subject_name')
    
    if request.method == 'POST':
        # Admin can edit EVERYTHING
        # Update student info if changed
        result.student.full_name = request.POST.get('student_name', result.student.full_name)
        result.student.save()
        
        # Update all fields
        result.times_school_opened = int(request.POST.get('times_opened', result.times_school_opened))
        result.times_present = int(request.POST.get('times_present', result.times_present))
        result.times_absent = int(request.POST.get('times_absent', result.times_absent))
        result.vacation_date = request.POST.get('vacation_date', result.vacation_date)
        result.resumption_date = request.POST.get('resumption_date', result.resumption_date)
        result.next_term_pta_fee = float(request.POST.get('pta_fee', result.next_term_pta_fee))
        result.next_term_school_fee = float(request.POST.get('school_fee', result.next_term_school_fee))
        
        # Update comments
        result.class_teacher_comment = request.POST.get('class_teacher_comment', result.class_teacher_comment)
        result.principal_comment = request.POST.get('principal_comment', result.principal_comment)
        
        result.save()
        
        # Update subject results if provided
        for subject_result in subject_results:
            sr_id = subject_result.id
            if f'test_a_{sr_id}' in request.POST:
                subject_result.test_a = float(request.POST.get(f'test_a_{sr_id}', subject_result.test_a))
                subject_result.test_b = float(request.POST.get(f'test_b_{sr_id}', subject_result.test_b))
                subject_result.test_c = float(request.POST.get(f'test_c_{sr_id}', subject_result.test_c))
                subject_result.exam = float(request.POST.get(f'exam_{sr_id}', subject_result.exam))
                subject_result.save()
        
        ResultActivityLog.objects.create(
            action='admin_edited',
            description=f'Admin edited result for {result.student.full_name}',
            student_result=result,
            performed_by_type='admin',
            performed_by_name=admin.full_name
        )
        
        messages.success(request, 'Result updated successfully!')
        return redirect('admin_result_management')
    
    context = {
        'result': result,
        'subject_results': subject_results,
        'admin': admin,
    }
    return render(request, 'result/admin_edit_result.html', context)


# Admin - Add Stamp
@login_required
def admin_add_stamp(request, result_id):
    """Admin adds stamp to result"""
    try:
        admin = Admin.objects.get(user=request.user)
        result = StudentResult.objects.get(id=result_id)
        
        result.has_stamp = True
        result.stamped_at = timezone.now()
        result.stamped_by = admin
        result.save()
        
        ResultActivityLog.objects.create(
            action='stamp_added',
            description=f'Stamp added to {result.student.full_name} result',
            student_result=result,
            performed_by_type='admin',
            performed_by_name=admin.full_name
        )
        
        messages.success(request, '✅ Stamp added!')
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
    
    return redirect('admin_result_management')


# Admin - Publish Result
@login_required
def admin_publish_result(request, result_id):
    """Admin publishes result and generates PIN"""
    try:
        admin = Admin.objects.get(user=request.user)
        result = StudentResult.objects.get(id=result_id, has_stamp=True)
        
        # Generate PIN
        pin = PublishedResult.generate_pin()
        
        PublishedResult.objects.create(
            result=result,
            pin=pin,
            published_by=admin,
            academic_year=result.academic_year,
            term=result.term,
            class_name=result.class_name
        )
        
        result.status = 'published'
        result.save()
        
        ResultActivityLog.objects.create(
            action='result_published',
            description=f'Result published for {result.student.full_name} - PIN: {pin}',
            student_result=result,
            performed_by_type='admin',
            performed_by_name=admin.full_name
        )
        
        messages.success(request, f'✅ Result published! PIN: {pin}')
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
    
    return redirect('admin_result_management')


# Admin - Publish Batch
@login_required
def admin_publish_batch(request):
    """Publish multiple results at once"""
    if request.method == 'POST':
        try:
            admin = Admin.objects.get(user=request.user)
            result_ids = request.POST.getlist('result_ids')
            
            published_count = 0
            for result_id in result_ids:
                result = StudentResult.objects.get(id=result_id, has_stamp=True)
                
                pin = PublishedResult.generate_pin()
                PublishedResult.objects.create(
                    result=result,
                    pin=pin,
                    published_by=admin,
                    academic_year=result.academic_year,
                    term=result.term,
                    class_name=result.class_name
                )
                
                result.status = 'published'
                result.save()
                published_count += 1
            
            messages.success(request, f'✅ {published_count} results published!')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    
    return redirect('admin_result_management')


# Admin - View Published Results
@login_required
def admin_view_published(request):
    """View all published results with PINs"""
    try:
        admin = Admin.objects.get(user=request.user)
    except:
        messages.error(request, 'Access denied.')
        return redirect('unified_login')
    
    # Filter options
    academic_year = request.GET.get('academic_year')
    term = request.GET.get('term')
    class_name = request.GET.get('class_name')
    
    published = PublishedResult.objects.all().order_by('-published_at')
    
    if academic_year:
        published = published.filter(academic_year=academic_year)
    if term:
        published = published.filter(term=term)
    if class_name:
        published = published.filter(class_name=class_name)
    
    # Get unique values for filters
    years = PublishedResult.objects.values_list('academic_year', flat=True).distinct()
    terms = PublishedResult.objects.values_list('term', flat=True).distinct()
    classes = PublishedResult.objects.values_list('class_name', flat=True).distinct()
    
    context = {
        'admin': admin,
        'published_results': published,
        'years': years,
        'terms': terms,
        'classes': classes,
    }
    return render(request, 'result/admin_published.html', context)





    # ============================================================================
# PART 4: Check Result (Student) & Print
# ============================================================================

# Check Result Portal
def check_result_portal(request):
    """Student enters PIN to check their result"""
    return render(request, 'result/check_result_portal.html')


# View Student Result with PIN
def view_student_result(request):
    """Display result after PIN verification"""
    if request.method == 'POST':
        pin = request.POST.get('result_pin')
        
        try:
            published_result = PublishedResult.objects.get(pin=pin)
            result = published_result.result
            
            # Get subject results
            subject_results = SubjectResult.objects.filter(
                student=result.student,
                term=result.term,
                academic_year=result.academic_year
            ).order_by('subject_name')
            
            context = {
                'result': result,
                'subject_results': subject_results,
                'published': published_result,
            }
            return render(request, 'result/student_result_view.html', context)
            
        except PublishedResult.DoesNotExist:
            messages.error(request, 'Invalid PIN. Please check and try again.')
            return redirect('check_result_portal')
    
    return redirect('check_result_portal')


# Print Result
@login_required
def print_result(request, result_id):
    """Generate printable result sheet"""
    try:
        result = StudentResult.objects.get(id=result_id)
        
        # Get subject results
        subject_results = SubjectResult.objects.filter(
            student=result.student,
            term=result.term,
            academic_year=result.academic_year
        ).order_by('subject_name')
        
        # Check if published (has PIN)
        try:
            published = PublishedResult.objects.get(result=result)
        except PublishedResult.DoesNotExist:
            published = None
        
        context = {
            'result': result,
            'subject_results': subject_results,
            'published': published,
            'school_settings': SchoolSettings.objects.first(),
        }
        return render(request, 'result/print_result.html', context)
        
    except StudentResult.DoesNotExist:
        messages.error(request, 'Result not found.')
        return redirect('admin_result_management')


# UPDATE UNIFIED LOGIN to handle new roles
def unified_login(request):
    if request.method == 'POST':
        role = request.POST.get('role')
        user_id = request.POST.get('user_id')
        result_pin = request.POST.get('result_pin')
        
        try:
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
            
            elif role == 'principal':
                principal = Principal.objects.get(principal_id=user_id)
                user = principal.user
                login(request, user)
                return redirect('principal_dashboard')
            
            elif role == 'bursar':
                bursar = Bursar.objects.get(bursar_id=user_id)
                user = bursar.user
                login(request, user)
                return redirect('bursar_dashboard')
            
            elif role == 'make_result':
                # Verify user_id belongs to teacher, principal, or admin
                try:
                    teacher = Teacher.objects.get(teacher_id=user_id)
                    user = teacher.user
                    login(request, user)
                    return redirect('make_result_portal')
                except Teacher.DoesNotExist:
                    try:
                        principal = Principal.objects.get(principal_id=user_id)
                        user = principal.user
                        login(request, user)
                        return redirect('make_result_portal')
                    except Principal.DoesNotExist:
                        admin = Admin.objects.get(admin_id=user_id)
                        user = admin.user
                        login(request, user)
                        return redirect('make_result_portal')
            
            elif role == 'check_result':
                # Verify PIN and redirect directly to result
                if result_pin:
                    try:
                        published_result = PublishedResult.objects.get(pin=result_pin)
                        result = published_result.result
                        
                        # Get subject results
                        subject_results = SubjectResult.objects.filter(
                            student=result.student,
                            term=result.term,
                            academic_year=result.academic_year
                        ).order_by('subject_name')
                        
                        # Render result directly without login
                        context = {
                            'result': result,
                            'subject_results': subject_results,
                            'published': published_result,
                        }
                        return render(request, 'result/student_result_view.html', context)
                    except PublishedResult.DoesNotExist:
                        messages.error(request, 'Invalid PIN. Please try again.')
                        return redirect('unified_login')
                else:
                    messages.error(request, 'Please enter your PIN.')
                    return redirect('unified_login')
        
        except Exception as e:
            messages.error(request, 'Invalid ID/PIN or Role. Please try again.')
            return redirect('unified_login')
    
    return render(request, 'login.html')