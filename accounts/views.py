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


try:
    call_command('loaddata', 'data_final.json')
except Exception as e:
    print("Error loading data:", e)

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
            created_by=teacher,
            shuffle_questions=True
        )
        
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


# NEW: Complete Result Entry System
@login_required
def complete_result_entry(request):
    try:
        teacher = Teacher.objects.get(user=request.user)
    except:
        messages.error(request, 'Access denied.')
        return redirect('unified_login')
    
    # Standard subjects for all classes
    STANDARD_SUBJECTS = [
        'ENGLISH LANGUAGE',
        'MATHEMATICS',
        'YORUBA LANGUAGE',
        'BASIC SCIENCE',
        'SOCIAL STUDIES',
        'CIVIC EDUCATION',
        'CULTURAL & CREATIVE ARTS',
        'C.R.K / I.R.K',
        'PHYSICAL & HEALTH EDUCATION',
        'ICT (COMPUTER STUDIES)',
        'AGRIC SCIENCE',
        'HOME ECONOMICS',
        'BUSINESS STUDIES',
        'MUSIC',
        'FRENCH LANGUAGE',
        'BASIC TECHNOLOGY',
    ]
    
    if request.method == 'POST':
        try:
            student_id = request.POST.get('student_id')
            term_id = request.POST.get('term_id')
            
            student = Student.objects.get(id=student_id)
            term = Term.objects.get(id=term_id)
            
            # Save all subject grades
            for subject in STANDARD_SUBJECTS:
                test1 = float(request.POST.get(f'test1_{subject}', 0) or 0)
                test2 = float(request.POST.get(f'test2_{subject}', 0) or 0)
                test3 = float(request.POST.get(f'test3_{subject}', 0) or 0)
                exam = float(request.POST.get(f'exam_{subject}', 0) or 0)
                
                # Skip if all zeros
                if test1 == 0 and test2 == 0 and test3 == 0 and exam == 0:
                    continue
                
                SubjectGrade.objects.update_or_create(
                    student=student,
                    term=term,
                    subject=subject,
                    defaults={
                        'test_1': test1,
                        'test_2': test2,
                        'test_3': test3,
                        'exam': exam,
                        'recorded_by': teacher
                    }
                )
            
            # Calculate positions and class averages
            calculate_class_positions(student.class_name, term)
            
            # Create/Update Result Summary
            create_result_summary(student, term)
            
            ActivityLog.objects.create(
                action='grades_entered',
                description=f'Complete result entered for {student.full_name} - {term}',
                performed_by_type='teacher',
                performed_by_name=teacher.full_name
            )
            
            messages.success(request, f'✅ Result saved successfully for {student.full_name}!')
            return redirect('result_preview', student_id=student.id, term_id=term.id)
            
        except Exception as e:
            messages.error(request, f'Error saving result: {str(e)}')
            return redirect('complete_result_entry')
    
    # GET request - show form
    classes = Student.objects.values_list('class_name', flat=True).distinct()
    terms = Term.objects.all()
    selected_class = request.GET.get('class_name')
    students = Student.objects.filter(class_name=selected_class).order_by('full_name') if selected_class else []
    
    context = {
        'teacher': teacher,
        'classes': classes,
        'terms': terms,
        'students': students,
        'selected_class': selected_class,
        'subjects': STANDARD_SUBJECTS,
    }
    return render(request, 'complete_result_entry.html', context)


# Helper function to calculate positions
def calculate_class_positions(class_name, term):
    """Calculate position for each student in the class"""
    students = Student.objects.filter(class_name=class_name)
    
    # Calculate total scores for each student
    student_totals = []
    for student in students:
        grades = SubjectGrade.objects.filter(student=student, term=term)
        total = sum([g.total_score for g in grades])
        student_totals.append((student, total, grades.count()))
    
    # Sort by total score (descending)
    student_totals.sort(key=lambda x: x[1], reverse=True)
    
    # Assign positions
    total_students = len(student_totals)
    for position, (student, total, subject_count) in enumerate(student_totals, 1):
        # Update or create result summary
        summary, created = ResultSummary.objects.get_or_create(
            student=student,
            term=term
        )
        summary.position_in_class = f"{position}/{total_students}"
        summary.total_subjects = subject_count
        summary.score_gained = total
        summary.average_score = total / subject_count if subject_count > 0 else 0
        summary.promotion_status = "PROMOTED" if summary.average_score >= 50 else "REPEAT"
        summary.save()
    
    # Calculate class average for each subject
    all_subjects = SubjectGrade.objects.filter(term=term, student__class_name=class_name).values_list('subject', flat=True).distinct()
    
    for subject in all_subjects:
        grades = SubjectGrade.objects.filter(term=term, student__class_name=class_name, subject=subject)
        if grades.exists():
            avg = sum([g.total_score for g in grades]) / grades.count()
            grades.update(class_average=round(avg, 2))
            
            # Calculate position in subject
            subject_scores = [(g.student, g.total_score) for g in grades]
            subject_scores.sort(key=lambda x: x[1], reverse=True)
            
            for pos, (student, score) in enumerate(subject_scores, 1):
                SubjectGrade.objects.filter(
                    student=student, 
                    term=term, 
                    subject=subject
                ).update(position_in_subject=pos)


# Helper function to create result summary
def create_result_summary(student, term):
    """Create or update result summary"""
    grades = SubjectGrade.objects.filter(student=student, term=term)
    
    if not grades.exists():
        return
    
    total_score = sum([g.total_score for g in grades])
    subject_count = grades.count()
    average = total_score / subject_count if subject_count > 0 else 0
    
    summary, created = ResultSummary.objects.get_or_create(
        student=student,
        term=term
    )
    
    summary.total_subjects = subject_count
    summary.score_gained = round(total_score, 2)
    summary.average_score = round(average, 2)
    summary.promotion_status = "PROMOTED" if average >= 50 else "REPEAT"
    summary.save()


# NEW: Result Preview
@login_required  
def result_preview(request, student_id, term_id):
    try:
        teacher = Teacher.objects.get(user=request.user)
    except:
        try:
            principal = Principal.objects.get(user=request.user)
        except:
            messages.error(request, 'Access denied.')
            return redirect('unified_login')
    
    student = Student.objects.get(id=student_id)
    term = Term.objects.get(id=term_id)
    grades = SubjectGrade.objects.filter(student=student, term=term).order_by('subject')
    summary = ResultSummary.objects.filter(student=student, term=term).first()
    school_settings = SchoolSettings.objects.first()
    
    # Handle remarks submission
    if request.method == 'POST':
        if 'class_teacher_remark' in request.POST:
            summary.class_teacher_remark = request.POST.get('class_teacher_remark')
            summary.class_teacher = teacher if 'teacher' in request.path else None
            summary.save()
            messages.success(request, '✅ Class Teacher remark saved!')
        
        if 'principal_remark' in request.POST:
            summary.principal_remark = request.POST.get('principal_remark')
            summary.principal = principal if 'principal' in request.path else None
            summary.save()
            messages.success(request, '✅ Principal remark saved!')
        
        if 'hos_remark' in request.POST:
            summary.hos_remark = request.POST.get('hos_remark')
            summary.save()
            messages.success(request, '✅ HOS remark saved!')
        
        return redirect('result_preview', student_id=student_id, term_id=term_id)
    
    context = {
        'student': student,
        'term': term,
        'grades': grades,
        'summary': summary,
        'school_settings': school_settings,
    }
    return render(request, 'result_preview.html', context)
@login_required
def enter_grades(request):
    try:
        teacher = Teacher.objects.get(user=request.user)
    except:
        messages.error(request, 'Access denied.')
        return redirect('unified_login')
    
    if request.method == 'POST':
        class_name = request.POST.get('class_name')
        subject = request.POST.get('subject')
        term_id = request.POST.get('term')
        
        try:
            term = Term.objects.get(id=term_id)
            students = Student.objects.filter(class_name=class_name)
            
            for student in students:
                test_1 = float(request.POST.get(f'test1_{student.id}', 0))
                test_2 = float(request.POST.get(f'test2_{student.id}', 0))
                test_3 = float(request.POST.get(f'test3_{student.id}', 0))
                exam = float(request.POST.get(f'exam_{student.id}', 0))
                
                SubjectGrade.objects.update_or_create(
                    student=student,
                    term=term,
                    subject=subject,
                    defaults={
                        'test_1': test_1,
                        'test_2': test_2,
                        'test_3': test_3,
                        'exam': exam,
                        'recorded_by': teacher
                    }
                )
            
            ActivityLog.objects.create(
                action='grades_entered',
                description=f'Grades entered for {subject} - {class_name}',
                performed_by_type='teacher',
                performed_by_name=teacher.full_name
            )
            
            messages.success(request, '✅ Grades saved successfully!')
            return redirect('enter_grades')
        except Exception as e:
            messages.error(request, f'Error saving grades: {str(e)}')
            return redirect('enter_grades')
    
    classes = Student.objects.values_list('class_name', flat=True).distinct()
    terms = Term.objects.all()
    selected_class = request.GET.get('class_name')
    students = Student.objects.filter(class_name=selected_class) if selected_class else []
    
    context = {
        'teacher': teacher,
        'classes': classes,
        'terms': terms,
        'students': students,
        'selected_class': selected_class,
    }
    return render(request, 'enter_grades.html', context)


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