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
from django.utils import timezone

# ============= UNIFIED LOGIN =============
def unified_login(request):
    # ===== DEBUG: Check authenticated user =====
    if request.user.is_authenticated:
        login_intent = request.session.get('login_intent')
        
        print("=" * 60)
        print(f"🔍 DEBUG: User authenticated: {request.user.username}")
        print(f"🔍 DEBUG: login_intent = '{login_intent}'")
        print(f"🔍 DEBUG: All session data: {dict(request.session)}")
        print("=" * 60)
        
        if login_intent == 'make_result':
            print("✅ DEBUG: login_intent is 'make_result' - checking user role...")
            try:
                if hasattr(request.user, 'teacher'):
                    print("✅ DEBUG: User is TEACHER -> Redirecting to teacher_role_selection")
                    return redirect('teacher_role_selection')
                elif hasattr(request.user, 'principal'):
                    print("✅ DEBUG: User is PRINCIPAL -> Redirecting to principal_result_review")
                    return redirect('principal_result_review')
                elif hasattr(request.user, 'admin'):
                    print("✅ DEBUG: User is ADMIN -> Redirecting to admin_result_management")
                    return redirect('admin_result_management')
            except Exception as e:
                print(f"❌ DEBUG ERROR: {e}")
        else:
            print(f"⚠️ DEBUG: login_intent is NOT 'make_result' (it's: '{login_intent}')")
            print("⚠️ DEBUG: Using default dashboard redirects...")
        
        # Default redirect for regular login
        try:
            if hasattr(request.user, 'admin'):
                print("📍 DEBUG: Redirecting to admin_dashboard")
                return redirect('admin_dashboard')
            elif hasattr(request.user, 'teacher'):
                print("📍 DEBUG: Redirecting to teacher_dashboard")
                return redirect('teacher_dashboard')
            elif hasattr(request.user, 'student'):
                print("📍 DEBUG: Redirecting to student_dashboard")
                return redirect('student_dashboard')
            elif hasattr(request.user, 'principal'):
                print("📍 DEBUG: Redirecting to principal_dashboard")
                return redirect('principal_dashboard')
            elif hasattr(request.user, 'bursar'):
                print("📍 DEBUG: Redirecting to bursar_dashboard")
                return redirect('bursar_dashboard')
        except Exception as e:
            print(f"❌ DEBUG: Error in default redirects: {e}")
    
    # Clear session for new logins (GET requests only)
    if 'login_intent' in request.session and request.method != 'POST':
        print("🧹 DEBUG: Clearing old login_intent")
        del request.session['login_intent']
    
    # ===== Handle POST (form submission) =====
    if request.method == 'POST':
        role = request.POST.get('role')
        user_id = request.POST.get('user_id')
        result_pin = request.POST.get('result_pin')
        
        print("\n" + "=" * 60)
        print(f"📮 DEBUG POST REQUEST:")
        print(f"   Role selected: '{role}'")
        print(f"   User ID: '{user_id}'")
        print("=" * 60)

        try:
            if role == 'admin':
                admin = Admin.objects.get(admin_id=user_id)
                user = admin.user
                login(request, user)
                print("✅ DEBUG: Admin logged in -> admin_dashboard")
                return redirect('admin_dashboard')

            elif role == 'teacher':
                teacher = Teacher.objects.get(teacher_id=user_id)
                user = teacher.user
                login(request, user)
                print("✅ DEBUG: Teacher logged in -> teacher_dashboard")
                return redirect('teacher_dashboard')

            elif role == 'student':
                student = Student.objects.get(student_id=user_id)
                user = student.user
                login(request, user)
                print("✅ DEBUG: Student logged in -> student_dashboard")
                return redirect('student_dashboard')

            elif role == 'principal':
                principal = Principal.objects.get(principal_id=user_id)
                user = principal.user
                login(request, user)
                print("✅ DEBUG: Principal logged in -> principal_dashboard")
                return redirect('principal_dashboard')

            elif role == 'bursar':
                bursar = Bursar.objects.get(bursar_id=user_id)
                user = bursar.user
                login(request, user)
                print("✅ DEBUG: Bursar logged in -> bursar_dashboard")
                return redirect('bursar_dashboard')

            elif role == 'make_result':
                print("\n🎯 DEBUG: 'make_result' selected - searching for user...")
                
                user_found = False
                user_role = None

                # Try Teacher
                try:
                    teacher = Teacher.objects.get(teacher_id=user_id)
                    user = teacher.user
                    user_found = True
                    user_role = 'teacher'
                    print(f"   ✅ Found TEACHER: {teacher.full_name}")
                except Teacher.DoesNotExist:
                    print(f"   ❌ Not a teacher")

                # Try Principal
                if not user_found:
                    try:
                        principal = Principal.objects.get(principal_id=user_id)
                        user = principal.user
                        user_found = True
                        user_role = 'principal'
                        print(f"   ✅ Found PRINCIPAL: {principal.full_name}")
                    except Principal.DoesNotExist:
                        print(f"   ❌ Not a principal")

                # Try Admin
                if not user_found:
                    try:
                        admin = Admin.objects.get(admin_id=user_id)
                        user = admin.user
                        user_found = True
                        user_role = 'admin'
                        print(f"   ✅ Found ADMIN: {admin.full_name}")
                    except Admin.DoesNotExist:
                        print(f"   ❌ Not an admin")

                # Login and set session
                if user_found:
                    print(f"\n🔐 DEBUG: Logging in as {user_role}...")
                    login(request, user)
                    
                    print(f"💾 DEBUG: Setting session login_intent = 'make_result'")
                    request.session['login_intent'] = 'make_result'
                    request.session.modified = True
                    request.session.save()
                    
                    print(f"📋 DEBUG: Session after save:")
                    for key, value in request.session.items():
                        print(f"      {key}: {value}")
                    
                    print(f"\n🚀 DEBUG: Redirecting based on role...")
                    if user_role == 'teacher':
                        print(f"   → Going to: teacher_role_selection")
                        return redirect('teacher_role_selection')
                    elif user_role == 'principal':
                        print(f"   → Going to: principal_result_review")
                        return redirect('principal_result_review')
                    elif user_role == 'admin':
                        print(f"   → Going to: admin_result_management")
                        return redirect('admin_result_management')
                else:
                    print("❌ DEBUG: No valid user found!")
                    messages.error(request, 'Invalid ID. Only Teachers, Principals, and Admins can access Make Result.')
                    return redirect('unified_login')
                
            elif role == 'check_result':
                if result_pin:
                    try:
                        published_result = PublishedResult.objects.get(pin=result_pin)
                        result = published_result.result
                        
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
                        messages.error(request, 'Invalid PIN. Please check your PIN and try again.')
                        return redirect('unified_login')
                else:
                    messages.error(request, 'Please enter your result PIN.')
                    return redirect('unified_login')

        except Exception as e:
            print(f"\n❌❌❌ DEBUG EXCEPTION: {str(e)}")
            import traceback
            traceback.print_exc()
            messages.error(request, 'Invalid ID or Role. Please try again.')
            return redirect('unified_login')
    
    return render(request, 'login.html')

# ======== LOG-OUT HANDLE =======
def user_logout(request):
    # Clear session data
    request.session.flush()
    logout(request)
    return redirect('unified_login')

# ============== SELECTION VIEW ===============
@login_required
def teacher_role_selection(request):
    """Allow teachers to choose between subject teacher and class teacher roles"""
    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        messages.error(request, 'Access denied.')
        return redirect('unified_login')
    
    return render(request, 'result/teacher_role_selection.html', {'teacher': teacher})

# ============= ADMIN VIEWS =============
@login_required
def toggle_exam_publish(request, exam_id):
    try:
        teacher = Teacher.objects.get(user=request.user)
        exam = Exam.objects.get(id=exam_id, created_by=teacher)
    except:
        messages.error(request, 'Access denied.')
        return redirect('teacher_dashboard')
    
    if request.method == 'POST':
        try:
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
        except Exception as e:
            messages.error(request, f'Error updating exam: {str(e)}')
    
    return redirect('teacher_dashboard')

@login_required
def mark_attendance(request):
    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
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

@login_required
def view_attendance(request):
    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        messages.error(request, 'Access denied.')
        return redirect('unified_login')
    
    filter_class = request.GET.get('class_name')
    filter_date = request.GET.get('date')
    
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
    except Student.DoesNotExist:
        messages.error(request, 'Access denied.')
        return redirect('unified_login')
    
    submissions = ExamSubmission.objects.filter(student=student).order_by('-submitted_at')
    
    available_exams = Exam.objects.filter(
        class_name=student.class_name, 
        is_active=True,
        is_published=True
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
    except Student.DoesNotExist:
        messages.error(request, 'Access denied.')
        return redirect('unified_login')
    
    if request.method == 'POST':
        if request.FILES.get('profile_picture'):
            try:
                student.profile_picture = request.FILES['profile_picture']
                student.save()
                messages.success(request, '✅ Profile picture updated successfully!')
                return redirect('student_profile')
            except Exception as e:
                messages.error(request, f'Error updating profile: {str(e)}')
        else:
            messages.error(request, 'Please select a picture to upload.')
    
    context = {'student': student}
    return render(request, 'student_profile.html', context)

@login_required
def take_exam(request, exam_id):
    try:
        student = Student.objects.get(user=request.user)
        exam = Exam.objects.get(exam_id=exam_id, class_name=student.class_name, is_active=True)
    except:
        messages.error(request, 'Invalid exam or access denied.')
        return redirect('student_dashboard')
    
    if ExamSubmission.objects.filter(student=student, exam=exam).exists():
        messages.error(request, 'You have already taken this exam.')
        return redirect('student_dashboard')
    
    questions = list(exam.questions.all())
    if exam.shuffle_questions:
        random.shuffle(questions)
    
    if request.method == 'POST':
        try:
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
        except Exception as e:
            messages.error(request, f'Error submitting exam: {str(e)}')
            return redirect('student_dashboard')
    
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
    
    context = {
        'submission': submission,
    }
    return render(request, 'view_result.html', context)

# ============= RESULT SYSTEM VIEWS =============
@login_required
def make_result_portal(request):
    try:
        Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        try:
            Principal.objects.get(user=request.user)
        except Principal.DoesNotExist:
            try:
                Admin.objects.get(user=request.user)
            except Admin.DoesNotExist:
                messages.error(request, 'Access denied. Only Teachers, Principals, and Admins can access Make Result.')
                return redirect('unified_login')
    
    return render(request, 'result/make_result_portal.html')

# ============= REPLACE YOUR subject_teacher_entry VIEW =============
@login_required
def subject_teacher_entry(request):
    from django.db.models import Count, Max  # ✅ Add imports
    
    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        messages.error(request, 'Access denied. Teachers only.')
        return redirect('unified_login')
    
    if request.method == 'POST':
        try:
            subject_name = request.POST.get('subject_name', '').upper()
            term = request.POST.get('term')
            academic_year = request.POST.get('academic_year')
            student_ids = request.POST.getlist('student_id')
            
            for student_id in student_ids:
                student = Student.objects.get(id=student_id)
                
                test_a = float(request.POST.get(f'test_a_{student_id}', 0))
                test_b = float(request.POST.get(f'test_b_{student_id}', 0))
                test_c = float(request.POST.get(f'test_c_{student_id}', 0))
                exam = float(request.POST.get(f'exam_{student_id}', 0))
                
                ltcum = 0
                if term in ['Second Term', 'Third Term']:
                    ltcum = float(request.POST.get(f'ltcum_{student_id}', 0))
                
                position = request.POST.get(f'position_{student_id}')
                position_value = int(position) if position and position.strip() else None
                
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
                        'ltcum': ltcum if term in ['Second Term', 'Third Term'] else None,
                        'position_ranking': position_value,
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
    
    from datetime import datetime
    current_year = datetime.now().year
    current_month = datetime.now().month
    
    if current_month <= 8:
        academic_year = f"{current_year - 1}/{current_year}"
    else:
        academic_year = f"{current_year}/{current_year + 1}"
    
    classes = Student.objects.values_list('class_name', flat=True).distinct()
    selected_class = request.GET.get('class_name')
    department = request.GET.get('department', '')
    
    students = []
    is_senior_class = False
    
    if selected_class:
        class_upper = selected_class.upper()
        # ✅ FIXED: More precise check for SS1, SS2, SS3 only
        is_senior_class = (
            class_upper in ['SS1', 'SS2', 'SS3'] or 
            class_upper.startswith('SS1') or 
            class_upper.startswith('SS2') or 
            class_upper.startswith('SS3')
        )
        
        if is_senior_class and department:
            students = Student.objects.filter(
                class_name=selected_class,
                department=department
            ).order_by('full_name')
        elif not is_senior_class:
            students = Student.objects.filter(class_name=selected_class).order_by('full_name')
    
    subject_name = request.GET.get('subject_name', '').upper()
    term = request.GET.get('term', 'First Term')
    
    departments = ['Science', 'Art', 'Commercial']
    
    existing_results = {}
    if subject_name and term and selected_class:
        for student in students:
            try:
                result = SubjectResult.objects.get(
                    student=student,
                    subject_name=subject_name,
                    term=term,
                    academic_year=academic_year
                )
                existing_results[student.id] = result
            except SubjectResult.DoesNotExist:
                pass
    
    # Get all recorded results by this teacher
    recorded_results = SubjectResult.objects.filter(
        entered_by=teacher
    ).values('subject_name', 'term', 'academic_year', 'student__class_name').annotate(
        student_count=Count('id'),
        last_updated=Max('updated_at')
    ).order_by('-last_updated')
    
    context = {
        'teacher': teacher,
        'classes': classes,
        'selected_class': selected_class,
        'students': students,
        'existing_results': existing_results,
        'subject_name': subject_name,
        'term': term,
        'academic_year': academic_year,
        'department': department,
        'departments': departments,
        'is_senior_class': is_senior_class,
        'recorded_results': recorded_results,
    }
    return render(request, 'result/subject_teacher_entry.html', context)


def test_subject_teacher(request):
    print("🎯 TEST VIEW CALLED!")
    return HttpResponse("Test view working!")


@login_required
def class_teacher_collate(request):
    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        messages.error(request, 'Access denied. Teachers only.')
        return redirect('unified_login')
    
    selected_class = request.GET.get('class_name')
    term = request.GET.get('term', 'First Term')
    department = request.GET.get('department', '')
    
    from datetime import datetime
    current_year = datetime.now().year
    current_month = datetime.now().month
    
    if current_month <= 8:
        academic_year = f"{current_year - 1}/{current_year}"
    else:
        academic_year = f"{current_year}/{current_year + 1}"
    
    classes = Student.objects.values_list('class_name', flat=True).distinct()
    departments = ['Science', 'Art', 'Commercial']
    
    unsent_results = []
    sent_results = []
    is_senior_class = False
    
    if selected_class and term and academic_year:
        class_upper = selected_class.upper()
        # ✅ FIXED: More precise check for SS1, SS2, SS3 only
        is_senior_class = (
            class_upper in ['SS1', 'SS2', 'SS3'] or 
            class_upper.startswith('SS1') or 
            class_upper.startswith('SS2') or 
            class_upper.startswith('SS3')
        )
        
        if is_senior_class and department:
            students = Student.objects.filter(
                class_name=selected_class,
                department=department
            ).order_by('full_name')
        elif not is_senior_class:
            students = Student.objects.filter(class_name=selected_class).order_by('full_name')
        else:
            students = []
        
        for student in students:
            try:
                result = StudentResult.objects.get(
                    student=student,
                    term=term,
                    academic_year=academic_year,
                    class_teacher=teacher
                )
                subject_count = SubjectResult.objects.filter(
                    student=student,
                    term=term,
                    academic_year=academic_year
                ).count()
                
                result_data = {
                    'student': student,
                    'result': result,
                    'subject_count': subject_count,
                }
                
                if result.status in ['sent_to_principal', 'sent_to_admin', 'published']:
                    sent_results.append(result_data)
                else:
                    unsent_results.append(result_data)
                    
            except StudentResult.DoesNotExist:
                subject_count = SubjectResult.objects.filter(
                    student=student,
                    term=term,
                    academic_year=academic_year
                ).count()
                unsent_results.append({
                    'student': student,
                    'result': None,
                    'subject_count': subject_count,
                })
    
    context = {
        'teacher': teacher,
        'classes': classes,
        'selected_class': selected_class,
        'term': term,
        'academic_year': academic_year,
        'unsent_results': unsent_results,
        'sent_results': sent_results,
        'department': department,
        'departments': departments,
        'is_senior_class': is_senior_class,
    }
    
    return render(request, 'result/class_teacher_collate.html', context)



    # ============= ADD THESE NEW VIEWS TO YOUR views.py =============

# ============= EDIT PAYMENT RECORD (NEW) =============
@login_required
def edit_payment_record(request, record_id):
    """Edit payment record - Bursar only"""
    try:
        bursar = Bursar.objects.get(user=request.user)
    except Bursar.DoesNotExist:
        try:
            admin = Admin.objects.get(user=request.user)
        except Admin.DoesNotExist:
            messages.error(request, 'Access denied.')
            return redirect('unified_login')
    
    record = get_object_or_404(FeeRecord, id=record_id)
    
    if request.method == 'POST':
        try:
            # Update ALL fields
            record.student = Student.objects.get(student_id=request.POST.get('student_id'))
            record.total_fee = float(request.POST.get('total_fee'))
            record.amount_paid = float(request.POST.get('amount_paid'))
            record.fee_type = request.POST.get('fee_type')
            record.payment_method = request.POST.get('payment_method')
            record.payment_date = request.POST.get('payment_date')
            record.save()  # This auto-calculates balance
            
            messages.success(request, '✅ Payment record updated successfully!')
            return redirect('bursar_dashboard')
        except Exception as e:
            messages.error(request, f'Error updating record: {str(e)}')
    
    students = Student.objects.all().order_by('full_name')
    context = {
        'record': record,
        'students': students,
    }
    return render(request, 'edit_payment_record.html', context)


# ============= DELETE PAYMENT RECORD (NEW) =============
@login_required
def delete_payment_record(request, record_id):
    """Delete payment record - Bursar only"""
    try:
        bursar = Bursar.objects.get(user=request.user)
    except Bursar.DoesNotExist:
        try:
            admin = Admin.objects.get(user=request.user)
        except Admin.DoesNotExist:
            messages.error(request, 'Access denied.')
            return redirect('unified_login')
    
    if request.method == 'POST':
        try:
            record = FeeRecord.objects.get(id=record_id)
            student_name = record.student.full_name
            amount = record.amount_paid
            record.delete()
            
            messages.success(request, f'✅ Payment record for {student_name} (₦{amount}) deleted successfully!')
        except FeeRecord.DoesNotExist:
            messages.error(request, 'Payment record not found.')
        except Exception as e:
            messages.error(request, f'Error deleting record: {str(e)}')
    
    return redirect('bursar_dashboard')


# ============= UPDATE OUTSTANDING PAYMENT (NEW) =============
@login_required
def update_outstanding_payment(request, student_id):
    """Update payment for student with outstanding balance"""
    from decimal import Decimal
    
    try:
        bursar = Bursar.objects.get(user=request.user)
    except Bursar.DoesNotExist:
        try:
            admin = Admin.objects.get(user=request.user)
        except Admin.DoesNotExist:
            messages.error(request, 'Access denied.')
            return redirect('unified_login')
    
    student = get_object_or_404(Student, student_id=student_id)
    
    # Get ALL records for this student to calculate total balance
    all_student_records = FeeRecord.objects.filter(student=student).order_by('-payment_date')
    
    # Calculate current outstanding balance
    total_fees = sum([Decimal(str(r.total_fee)) for r in all_student_records])
    total_paid = sum([Decimal(str(r.amount_paid)) for r in all_student_records])
    current_balance = total_fees - total_paid
    
    # Get most recent record for display
    latest_record = all_student_records.first()
    
    if request.method == 'POST':
        try:
            additional_payment = Decimal(request.POST.get('additional_payment', 0))
            payment_method = request.POST.get('payment_method')
            payment_date = request.POST.get('payment_date')
            
            # Validate payment doesn't exceed balance
            if additional_payment > current_balance:
                messages.error(request, f'Payment amount (₦{additional_payment}) cannot exceed outstanding balance (₦{current_balance})!')
                return redirect('update_outstanding_payment', student_id=student_id)
            
            # Calculate new balance
            new_balance = current_balance - additional_payment
            
            # Create new payment record
            FeeRecord.objects.create(
                student=student,
                term=latest_record.term if latest_record else None,
                total_fee=Decimal('0.00'),  # Don't add to total fees again
                amount_paid=additional_payment,  # Just the payment amount
                balance=new_balance,  # New balance after this payment
                fee_type=f"Balance Payment" if latest_record else "Payment",
                payment_method=payment_method,
                payment_date=payment_date,
                recorded_by=bursar if hasattr(request.user, 'bursar') else None,
                recorded_by_admin=admin if hasattr(request.user, 'admin') else None,
                is_balanced=(new_balance <= 0)  # Mark as balanced if fully paid
            )
            
            # Log activity
            ActivityLog.objects.create(
                action='fee_recorded',
                description=f'Balance payment of ₦{additional_payment} recorded for {student.full_name}. New balance: ₦{new_balance}',
                performed_by_type='bursar' if hasattr(request.user, 'bursar') else 'admin',
                performed_by_name=bursar.full_name if hasattr(request.user, 'bursar') else admin.full_name
            )
            
            if new_balance <= 0:
                messages.success(request, f'✅ Payment of ₦{additional_payment} recorded! {student.full_name} is now FULLY BALANCED! 🎉')
            else:
                messages.success(request, f'✅ Payment of ₦{additional_payment} recorded! Remaining balance: ₦{new_balance:.2f}')
            
            return redirect('bursar_dashboard')
            
        except Exception as e:
            messages.error(request, f'Error recording payment: {str(e)}')
            return redirect('update_outstanding_payment', student_id=student_id)
    
    context = {
        'student': student,
        'latest_record': latest_record,
        'current_balance': current_balance,  # Pass the actual calculated balance
        'total_fees': total_fees,
        'total_paid': total_paid,
    }
    return render(request, 'update_outstanding_payment.html', context)
    


    # ADD THESE NEW VIEWS TO YOUR views.py FILE

# ============= EDIT STUDENT VIEW (NEW) =============
@login_required
def edit_student(request, student_id):
    """Edit student information without affecting ID, scores, or other data"""
    try:
        admin = Admin.objects.get(user=request.user)
    except Admin.DoesNotExist:
        messages.error(request, 'Access denied.')
        return redirect('unified_login')
    
    student = get_object_or_404(Student, id=student_id)
    
    if request.method == 'POST':
        try:
            # Update student information (NOT the student_id)
            student.full_name = request.POST.get('full_name', student.full_name)
            student.email = request.POST.get('email', student.email)
            student.phone = request.POST.get('phone', student.phone)
            student.class_name = request.POST.get('class_name', student.class_name)
            
            # Handle department for SS1-3
            class_name_upper = student.class_name.upper()
            if any(cls in class_name_upper for cls in ['SS1', 'SS2', 'SS3']):
                department = request.POST.get('department', '')
                if not department:
                    messages.error(request, 'Department is required for SS1, SS2, and SS3 students!')
                    return redirect('edit_student', student_id=student_id)
                student.department = department
            else:
                # Clear department for junior classes
                student.department = ''
            
            student.save()
            
            ActivityLog.objects.create(
                action='student_edited',
                description=f'Student {student.full_name} ({student.student_id}) information updated',
                performed_by_type='admin',
                performed_by_name=admin.full_name
            )
            
            messages.success(request, f'✅ Student {student.full_name} updated successfully!')
            return redirect('admin_dashboard')
            
        except Exception as e:
            messages.error(request, f'Error updating student: {str(e)}')
            return redirect('edit_student', student_id=student_id)
    
    context = {
        'admin': admin,
        'student': student,
    }
    return render(request, 'edit_student.html', context)


# ADD THIS NEW VIEW - for creating new results
# REPLACE class_teacher_start_result in your views.py

@login_required
def class_teacher_start_result(request):
    """Start a new result for a student"""
    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        messages.error(request, 'Access denied. Teachers only.')
        return redirect('unified_login')
    
    # Get parameters from URL
    student_id = request.GET.get('student_id')
    term = request.GET.get('term')
    academic_year = request.GET.get('year')
    
    if not all([student_id, term, academic_year]):
        messages.error(request, 'Missing required parameters.')
        return redirect('class_teacher_collate')
    
    try:
        student = Student.objects.get(id=student_id)
    except Student.DoesNotExist:
        messages.error(request, 'Student not found.')
        return redirect('class_teacher_collate')
    
    # Get subject results for this student
    subject_results = SubjectResult.objects.filter(
        student=student,
        term=term,
        academic_year=academic_year
    ).order_by('subject_name')
    
    if request.method == 'POST':
        try:
            result, created = StudentResult.objects.get_or_create(
                student=student,
                term=term,
                academic_year=academic_year,
                defaults={
                    'class_name': student.class_name,
                    'class_teacher': teacher,
                }
            )
            
            # Save all the form data
            result.times_school_opened = int(request.POST.get('times_opened', 0))
            result.times_present = int(request.POST.get('times_present', 0))
            result.times_absent = int(request.POST.get('times_absent', 0))
            result.vacation_date = request.POST.get('vacation_date') or None
            result.resumption_date = request.POST.get('resumption_date') or None
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
            
            # Teacher comment
            result.class_teacher_comment = request.POST.get('class_teacher_comment', '')
            result.class_teacher = teacher
            
            # Calculate totals using CUM (not avg_2)
            result.total_subjects = subject_results.count()
            result.score_gained = sum([sr.cum for sr in subject_results])  # Changed from avg_2 to cum
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
            
            messages.success(request, f'✅ Result saved for {student.full_name}!')
            return redirect('class_teacher_collate')
            
        except Exception as e:
            messages.error(request, f'Error saving result: {str(e)}')
    
    context = {
        'teacher': teacher,
        'student': student,
        'subject_results': subject_results,
        'term': term,
        'academic_year': academic_year,
        'result': None,  # No existing result
    }
    return render(request, 'result/class_teacher_start_result.html', context)

# UPDATED VERSION of class_teacher_edit_result
@login_required
def class_teacher_edit_result(request, result_id):
    try:
        teacher = Teacher.objects.get(user=request.user)
        result = StudentResult.objects.get(id=result_id, class_teacher=teacher)
    except Teacher.DoesNotExist:
        messages.error(request, 'Access denied. Teachers only.')
        return redirect('unified_login')
    except StudentResult.DoesNotExist:
        messages.error(request, 'Result not found or you do not have permission to edit it.')
        return redirect('class_teacher_collate')
    
    subject_results = SubjectResult.objects.filter(
        student=result.student,
        term=result.term,
        academic_year=result.academic_year
    ).order_by('subject_name')
    
    if request.method == 'POST':
        try:
            # Update all fields
            result.times_school_opened = int(request.POST.get('times_opened', result.times_school_opened))
            result.times_present = int(request.POST.get('times_present', result.times_present))
            result.times_absent = int(request.POST.get('times_absent', result.times_absent))
            result.vacation_date = request.POST.get('vacation_date') or result.vacation_date
            result.resumption_date = request.POST.get('resumption_date') or result.resumption_date
            result.next_term_pta_fee = float(request.POST.get('pta_fee', result.next_term_pta_fee))
            result.next_term_school_fee = float(request.POST.get('school_fee', result.next_term_school_fee))
            
            # Affective domain
            result.affective_punctuality = request.POST.get('aff_punctuality', result.affective_punctuality)
            result.affective_neatness = request.POST.get('aff_neatness', result.affective_neatness)
            result.affective_politeness = request.POST.get('aff_politeness', result.affective_politeness)
            result.affective_honesty = request.POST.get('aff_honesty', result.affective_honesty)
            result.affective_relationship = request.POST.get('aff_relationship', result.affective_relationship)
            result.affective_self_control = request.POST.get('aff_self_control', result.affective_self_control)
            result.affective_attentiveness = request.POST.get('aff_attentiveness', result.affective_attentiveness)
            
            # Psychomotor domain
            result.psycho_handwriting = request.POST.get('psycho_handwriting', result.psycho_handwriting)
            result.psycho_sports = request.POST.get('psycho_sports', result.psycho_sports)
            result.psycho_handling_tools = request.POST.get('psycho_tools', result.psycho_handling_tools)
            result.psycho_verbal_fluency = request.POST.get('psycho_verbal', result.psycho_verbal_fluency)
            result.psycho_games = request.POST.get('psycho_games', result.psycho_games)
            result.psycho_drawing = request.POST.get('psycho_drawing', result.psycho_drawing)
            
            result.class_teacher_comment = request.POST.get('class_teacher_comment', result.class_teacher_comment)
            
            # Recalculate totals
            result.total_subjects = subject_results.count()
            result.score_gained = sum([sr.avg_2 for sr in subject_results])
            result.average_score = result.score_gained / result.total_subjects if result.total_subjects > 0 else 0
            result.status_promotion = "PROMOTED" if result.average_score >= 50 else "REPEAT"
            
            result.save()
            
            messages.success(request, 'Result updated successfully!')
            return redirect('class_teacher_collate')
        except Exception as e:
            messages.error(request, f'Error updating result: {str(e)}')
    
    context = {
        'result': result,
        'subject_results': subject_results,
        'teacher': teacher,
    }
    return render(request, 'result/edit_result.html', context)

@login_required
def send_result_to_principal(request, result_id):
    try:
        teacher = Teacher.objects.get(user=request.user)
        result = StudentResult.objects.get(id=result_id, class_teacher=teacher)
        
        # Check if this is a resend (result was already sent before)
        is_resend = result.status == 'sent_to_principal'
        
        result.status = 'sent_to_principal'
        result.sent_to_principal_at = timezone.now()
        result.save()
        
        # Create notification for ALL principals
        principals = Principal.objects.all()
        for principal in principals:
            ResultNotification.objects.create(
                recipient_type='principal',
                recipient=principal.user,
                student_result=result,
                notification_type='result_resent' if is_resend else 'new_result',
                message=f"{'UPDATED RESULT' if is_resend else 'New result'} from {teacher.full_name} for {result.student.full_name} ({result.class_name}) - {result.term} {result.academic_year}"
            )
        
        # Log activity
        ResultActivityLog.objects.create(
            action='sent_to_principal',
            description=f"{'RESENT (Updated)' if is_resend else 'Sent'} result for {result.student.full_name} to Principal",
            student_result=result,
            performed_by_type='teacher',
            performed_by_name=teacher.full_name
        )
        
        messages.success(request, f"✅ Result {'resent (updated)' if is_resend else 'sent'} to Principal!")
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
    
    return redirect('class_teacher_collate')

@login_required
def send_batch_to_principal(request):
    if request.method == 'POST':
        try:
            teacher = Teacher.objects.get(user=request.user)
            result_ids = request.POST.getlist('result_ids')
            
            count = 0
            resent_count = 0
            
            for result_id in result_ids:
                result = StudentResult.objects.get(id=result_id, class_teacher=teacher)
                
                is_resend = result.status == 'sent_to_principal'
                if is_resend:
                    resent_count += 1
                
                result.status = 'sent_to_principal'
                result.sent_to_principal_at = timezone.now()
                result.save()
                
                # Create notification for ALL principals
                principals = Principal.objects.all()
                for principal in principals:
                    ResultNotification.objects.create(
                        recipient_type='principal',
                        recipient=principal.user,
                        student_result=result,
                        notification_type='result_resent' if is_resend else 'new_result',
                        message=f"{'UPDATED RESULT' if is_resend else 'New result'} from {teacher.full_name} for {result.student.full_name} ({result.class_name})"
                    )
                
                count += 1
            
            ResultActivityLog.objects.create(
                action='sent_to_principal',
                description=f'{count} results sent to Principal by {teacher.full_name} ({resent_count} resent)',
                performed_by_type='teacher',
                performed_by_name=teacher.full_name
            )
            
            msg = f'✅ {count} results sent to Principal!'
            if resent_count > 0:
                msg += f' ({resent_count} updated and resent)'
            messages.success(request, msg)
            
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    
    return redirect('class_teacher_collate')

# REPLACE principal_result_review in your views.py

@login_required
def principal_result_review(request):
    try:
        principal = Principal.objects.get(user=request.user)
    except Principal.DoesNotExist:
        messages.error(request, 'Access denied. Principal only.')
        return redirect('unified_login')
    
    # Get incoming results (sent to principal)
    incoming_results = StudentResult.objects.filter(
        status='sent_to_principal'
    ).order_by('class_name', 'student__full_name')
    
    # Get sent results (sent to admin)
    sent_results = StudentResult.objects.filter(
        status__in=['sent_to_admin', 'published'],
        principal=principal
    ).order_by('-sent_to_admin_at')
    
    # Get unread notifications
    unread_notifications = ResultNotification.objects.filter(
        recipient=principal.user,
        is_read=False
    ).order_by('-created_at')
    
    # Get all notifications (last 20)
    all_notifications = ResultNotification.objects.filter(
        recipient=principal.user
    ).order_by('-created_at')[:20]
    
    context = {
        'principal': principal,
        'incoming_results': incoming_results,
        'sent_results': sent_results,
        'unread_notifications': unread_notifications,
        'all_notifications': all_notifications,
        'unread_count': unread_notifications.count(),
    }
    return render(request, 'result/principal_review.html', context)


# ADD THIS NEW VIEW - Mark notification as read
@login_required
def mark_notification_read(request, notification_id):
    try:
        notification = ResultNotification.objects.get(id=notification_id, recipient=request.user)
        notification.is_read = True
        notification.save()
        return JsonResponse({'status': 'success'})
    except ResultNotification.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Notification not found'})


# ADD THIS NEW VIEW - Mark all notifications as read
@login_required
def mark_all_notifications_read(request):
    try:
        ResultNotification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        messages.success(request, '✅ All notifications marked as read!')
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
    
    if hasattr(request.user, 'principal'):
        return redirect('principal_result_review')
    elif hasattr(request.user, 'admin'):
        return redirect('admin_result_management')
    else:
        return redirect('unified_login')

        
@login_required
def principal_add_comment(request, result_id):
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

@login_required
def send_result_to_admin(request, result_id):
    try:
        principal = Principal.objects.get(user=request.user)
        result = StudentResult.objects.get(id=result_id)
        
        is_resend = result.status == 'sent_to_admin'
        
        result.status = 'sent_to_admin'
        result.sent_to_admin_at = timezone.now()
        result.save()
        
        # Create notification for ALL admins
        admins = Admin.objects.all()
        for admin in admins:
            ResultNotification.objects.create(
                recipient_type='admin',
                recipient=admin.user,
                student_result=result,
                notification_type='result_resent' if is_resend else 'new_result',
                message=f"{'UPDATED RESULT' if is_resend else 'New result'} from Principal for {result.student.full_name} ({result.class_name}) - {result.term} {result.academic_year}"
            )
        
        ResultActivityLog.objects.create(
            action='sent_to_admin',
            description=f"{'RESENT (Updated)' if is_resend else 'Sent'} result for {result.student.full_name} to Admin",
            student_result=result,
            performed_by_type='principal',
            performed_by_name=principal.full_name
        )
        
        messages.success(request, f"✅ Result {'resent (updated)' if is_resend else 'sent'} to Admin!")
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
    
    return redirect('principal_result_review')

@login_required
def send_batch_to_admin(request):
    if request.method == 'POST':
        try:
            principal = Principal.objects.get(user=request.user)
            result_ids = request.POST.getlist('result_ids')
            
            count = 0
            resent_count = 0
            
            for result_id in result_ids:
                result = StudentResult.objects.get(id=result_id)
                
                is_resend = result.status == 'sent_to_admin'
                if is_resend:
                    resent_count += 1
                
                result.status = 'sent_to_admin'
                result.sent_to_admin_at = timezone.now()
                result.save()
                
                # Create notification for ALL admins
                admins = Admin.objects.all()
                for admin in admins:
                    ResultNotification.objects.create(
                        recipient_type='admin',
                        recipient=admin.user,
                        student_result=result,
                        notification_type='result_resent' if is_resend else 'new_result',
                        message=f"{'UPDATED' if is_resend else 'New'} result from Principal for {result.student.full_name}"
                    )
                
                count += 1
            
            ResultActivityLog.objects.create(
                action='sent_to_admin',
                description=f'{count} results sent to Admin by {principal.full_name} ({resent_count} resent)',
                performed_by_type='principal',
                performed_by_name=principal.full_name
            )
            
            msg = f'✅ {count} results sent to Admin!'
            if resent_count > 0:
                msg += f' ({resent_count} updated and resent)'
            messages.success(request, msg)
            
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    
    return redirect('principal_result_review')

@login_required
def admin_result_management(request):
    try:
        admin = Admin.objects.get(user=request.user)
    except Admin.DoesNotExist:
        messages.error(request, 'Access denied. Admin only.')
        return redirect('unified_login')
    
    incoming_results = StudentResult.objects.filter(
        status='sent_to_admin'
    ).order_by('class_name', 'student__full_name')
    
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

@login_required
def admin_edit_result(request, result_id):
    try:
        admin = Admin.objects.get(user=request.user)
        result = StudentResult.objects.get(id=result_id)
    except:
        messages.error(request, 'Access denied.')
        return redirect('admin_result_management')
    
    subject_results = SubjectResult.objects.filter(
        student=result.student,
        term=result.term,
        academic_year=result.academic_year
    ).order_by('subject_name')
    
    if request.method == 'POST':
        try:
            result.student.full_name = request.POST.get('student_name', result.student.full_name)
            result.student.save()
            
            result.times_school_opened = int(request.POST.get('times_opened', result.times_school_opened))
            result.times_present = int(request.POST.get('times_present', result.times_present))
            result.times_absent = int(request.POST.get('times_absent', result.times_absent))
            result.vacation_date = request.POST.get('vacation_date', result.vacation_date)
            result.resumption_date = request.POST.get('resumption_date', result.resumption_date)
            result.next_term_pta_fee = float(request.POST.get('pta_fee', result.next_term_pta_fee))
            result.next_term_school_fee = float(request.POST.get('school_fee', result.next_term_school_fee))
            
            result.class_teacher_comment = request.POST.get('class_teacher_comment', result.class_teacher_comment)
            result.principal_comment = request.POST.get('principal_comment', result.principal_comment)
            
            result.save()
            
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
        except Exception as e:
            messages.error(request, f'Error updating result: {str(e)}')
            return redirect('admin_result_management')
    
    context = {
        'result': result,
        'subject_results': subject_results,
        'admin': admin,
    }
    return render(request, 'result/admin_edit_result.html', context)

@login_required
def admin_add_stamp(request, result_id):
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

@login_required
def admin_publish_result(request, result_id):
    try:
        admin = Admin.objects.get(user=request.user)
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

@login_required
def admin_publish_batch(request):
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

@login_required
def admin_view_published(request):
    try:
        admin = Admin.objects.get(user=request.user)
    except Admin.DoesNotExist:
        messages.error(request, 'Access denied.')
        return redirect('unified_login')
    
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

def check_result_portal(request):
    return render(request, 'result/check_result_portal.html')

def view_student_result(request):
    if request.method == 'POST':
        pin = request.POST.get('result_pin')
        
        try:
            published_result = PublishedResult.objects.get(pin=pin)
            result = published_result.result
            
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

@login_required
def print_result(request, result_id):
    try:
        result = StudentResult.objects.get(id=result_id)
        
        subject_results = SubjectResult.objects.filter(
            student=result.student,
            term=result.term,
            academic_year=result.academic_year
        ).order_by('subject_name')
        
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

def export_results(request, exam_id):
    """Export exam results as CSV"""
    try:
        exam = Exam.objects.get(id=exam_id)
        submissions = ExamSubmission.objects.filter(exam=exam).order_by('-score')
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="results_{exam.exam_id}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Student ID', 'Student Name', 'Score', 'Correct', 'Total', 'Date'])
        
        for sub in submissions:
            writer.writerow([
                sub.student.student_id,
                sub.student.full_name,
                f'{sub.score}%',
                sub.correct_answers,
                sub.total_questions,
                sub.submitted_at.strftime('%Y-%m-%d %H:%M')
            ])
        
        return response
    except Exception as e:
        messages.error(request, f'Error exporting results: {str(e)}')
        return redirect('teacher_dashboard')

@login_required
def delete_teacher(request, teacher_id):
    """Simple delete teacher function (redirects to confirm version)"""
    return redirect('delete_teacher_confirm', teacher_id=teacher_id)

@login_required
def admin_dashboard(request):
    try:
        admin = Admin.objects.get(user=request.user)
    except Admin.DoesNotExist:
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
        is_admin = True
        user_obj = admin
    except Admin.DoesNotExist:
        try:
            principal = Principal.objects.get(user=request.user)
            is_admin = False
            user_obj = principal
        except Principal.DoesNotExist:
            messages.error(request, 'Access denied.')
            return redirect('unified_login')
    
    if request.method == 'POST':
        try:
            full_name = request.POST.get('full_name')
            email = request.POST.get('email')
            phone = request.POST.get('phone')
            class_name = request.POST.get('class_name')
            department = request.POST.get('department', '')
            
            # Validate department for SS1-3
            class_name_upper = class_name.upper()
            if any(cls in class_name_upper for cls in ['SS1', 'SS2', 'SS3']):
                if not department:
                    messages.error(request, '⚠️ Department is required for SS1, SS2, and SS3 students!')
                    return redirect('register_student')
            else:
                # Clear department for junior classes
                department = ''
            
            username = full_name.replace(' ', '').lower() + str(random.randint(100, 999))
            user = User.objects.create_user(
                username=username, 
                email=email if email else '',
                password='default123'
            )
            
            student = Student.objects.create(
                user=user,
                full_name=full_name,
                email=email if email else None,
                phone=phone if phone else None,
                class_name=class_name,
                department=department,  # NEW FIELD
                registered_by=admin if is_admin else None
            )
            
            dept_info = f" - {department} Department" if department else ""
            ActivityLog.objects.create(
                action='student_registered',
                description=f'Student {full_name} registered with ID {student.student_id}{dept_info}',
                performed_by_type='admin' if is_admin else 'principal',
                performed_by_name=user_obj.full_name
            )
            
            messages.success(request, f'Student registered successfully! Student ID: {student.student_id}')
            return redirect('admin_dashboard' if is_admin else 'principal_dashboard')
            
        except Exception as e:
            messages.error(request, f'Error registering student: {str(e)}')
            return redirect('register_student')
    
    return render(request, 'register_student.html')

@login_required
def move_to_alumni(request, student_id):
    try:
        admin = Admin.objects.get(user=request.user)
    except Admin.DoesNotExist:
        messages.error(request, 'Access denied.')
        return redirect('unified_login')
    
    if request.method == 'POST':
        try:
            student = Student.objects.get(id=student_id)
            reason = request.POST.get('reason')
            year_left = request.POST.get('year_left')
            current_institution = request.POST.get('current_institution')
            notes = request.POST.get('notes')
            
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
            
        except Student.DoesNotExist:
            messages.error(request, 'Student not found.')
            return redirect('admin_dashboard')
        except Exception as e:
            messages.error(request, f'Error moving student to alumni: {str(e)}')
            return redirect('admin_dashboard')
    
    student = get_object_or_404(Student, id=student_id)
    context = {'student': student}
    return render(request, 'move_to_alumni.html', context)

@login_required
def view_alumni(request):
    try:
        Admin.objects.get(user=request.user)
    except Admin.DoesNotExist:
        try:
            Principal.objects.get(user=request.user)
        except Principal.DoesNotExist:
            messages.error(request, 'Access denied.')
            return redirect('unified_login')
    
    alumni_list = Alumni.objects.all().order_by('-moved_on')
    context = {'alumni_list': alumni_list}
    return render(request, 'view_alumni.html', context)

@login_required
def register_teacher(request):
    try:
        admin = Admin.objects.get(user=request.user)
        is_admin = True
        user_obj = admin
    except Admin.DoesNotExist:
        try:
            principal = Principal.objects.get(user=request.user)
            is_admin = False
            user_obj = principal
        except Principal.DoesNotExist:
            messages.error(request, 'Access denied.')
            return redirect('unified_login')
    
    if request.method == 'POST':
        try:
            full_name = request.POST.get('full_name')
            email = request.POST.get('email')
            phone = request.POST.get('phone')
            subject = request.POST.get('subject')
            
            username = email.split('@')[0] + str(random.randint(100, 999))
            user = User.objects.create_user(username=username, email=email, password='default123')
            
            teacher = Teacher.objects.create(
                user=user,
                full_name=full_name,
                email=email,
                phone=phone,
                subject=subject,
                registered_by=admin if is_admin else None
            )
            
            ActivityLog.objects.create(
                action='teacher_registered',
                description=f'Teacher {full_name} registered with ID {teacher.teacher_id}',
                performed_by_type='admin' if is_admin else 'principal',
                performed_by_name=user_obj.full_name
            )
            
            messages.success(request, f'Teacher registered successfully! Teacher ID: {teacher.teacher_id}')
            return redirect('admin_dashboard' if is_admin else 'principal_dashboard')
            
        except Exception as e:
            messages.error(request, f'Error registering teacher: {str(e)}')
            return redirect('register_teacher')
    
    return render(request, 'register_teacher.html')

@login_required
def delete_student_confirm(request, student_id):
    try:
        admin = Admin.objects.get(user=request.user)
    except Admin.DoesNotExist:
        messages.error(request, 'Access denied.')
        return redirect('unified_login')
    
    student = get_object_or_404(Student, id=student_id)
    
    if request.method == 'POST':
        try:
            student_name = student.full_name
            student_id_num = student.student_id
            
            student.user.delete()
            
            ActivityLog.objects.create(
                action='student_deleted',
                description=f'Student {student_name} ({student_id_num}) permanently deleted',
                performed_by_type='admin',
                performed_by_name=admin.full_name
            )
            
            messages.success(request, f'✅ Student {student_name} has been permanently deleted!')
            return redirect('admin_dashboard')
        except Exception as e:
            messages.error(request, f'Error deleting student: {str(e)}')
            return redirect('admin_dashboard')
    
    context = {'student': student}
    return render(request, 'confirm_delete_student.html', context)

@login_required
def delete_teacher_confirm(request, teacher_id):
    try:
        admin = Admin.objects.get(user=request.user)
    except Admin.DoesNotExist:
        messages.error(request, 'Access denied.')
        return redirect('unified_login')
    
    teacher = get_object_or_404(Teacher, id=teacher_id)
    
    if request.method == 'POST':
        try:
            teacher_name = teacher.full_name
            teacher_id_num = teacher.teacher_id
            
            teacher.user.delete()
            
            ActivityLog.objects.create(
                action='teacher_deleted',
                description=f'Teacher {teacher_name} ({teacher_id_num}) permanently deleted',
                performed_by_type='admin',
                performed_by_name=admin.full_name
            )
            
            messages.success(request, f'✅ Teacher {teacher_name} has been permanently deleted!')
            return redirect('admin_dashboard')
        except Exception as e:
            messages.error(request, f'Error deleting teacher: {str(e)}')
            return redirect('admin_dashboard')
    
    context = {'teacher': teacher}
    return render(request, 'confirm_delete_teacher.html', context)

@login_required
def search_students(request):
    try:
        admin = Admin.objects.get(user=request.user)
        is_admin = True
    except Admin.DoesNotExist:
        try:
            principal = Principal.objects.get(user=request.user)
            is_admin = False
        except Principal.DoesNotExist:
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

@login_required
def search_teachers(request):
    try:
        admin = Admin.objects.get(user=request.user)
        is_admin = True
    except Admin.DoesNotExist:
        try:
            principal = Principal.objects.get(user=request.user)
            is_admin = False
        except Principal.DoesNotExist:
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

# ============= FINANCE MANAGEMENT =============
@login_required
def manage_finance(request):
    try:
        admin = Admin.objects.get(user=request.user)
        is_admin = True
        user_name = admin.full_name
    except Admin.DoesNotExist:
        try:
            bursar = Bursar.objects.get(user=request.user)
            is_admin = False
            user_name = bursar.full_name
        except Bursar.DoesNotExist:
            messages.error(request, 'Access denied.')
            return redirect('unified_login')
    
    if request.method == 'POST':
        try:
            student_id = request.POST.get('student_id')
            total_fee = float(request.POST.get('total_fee', 0))
            amount_paid = float(request.POST.get('amount_paid', 0))
            fee_type = request.POST.get('fee_type')
            payment_method = request.POST.get('payment_method')
            payment_date = request.POST.get('payment_date') or timezone.now().date()
            
            student = Student.objects.get(student_id=student_id)
            current_term = Term.objects.filter(is_current=True).first()
            
            fee_record = FeeRecord.objects.create(
                student=student,
                term=current_term,
                total_fee=total_fee,
                amount_paid=amount_paid,
                balance=total_fee - amount_paid,
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
        except Student.DoesNotExist:
            messages.error(request, 'Student not found.')
        except Exception as e:
            messages.error(request, f'Error recording payment: {str(e)}')
    
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
    except Principal.DoesNotExist:
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

# ============= REPLACE YOUR bursar_dashboard VIEW =============

@login_required
def bursar_dashboard(request):
    try:
        bursar = Bursar.objects.get(user=request.user)
    except Bursar.DoesNotExist:
        messages.error(request, 'Access denied.')
        return redirect('unified_login')
    
    from decimal import Decimal
    
    search_query = request.GET.get('search', '')
    
    # Get all students
    students = Student.objects.all()
    
    # Calculate balanced and outstanding records
    balanced_records = []
    outstanding_records = []
    
    for student in students:
        # Get all payment records for this student
        student_records = FeeRecord.objects.filter(student=student).order_by('-payment_date')
        
        if student_records.exists():
            # Calculate total fees and total paid using Decimal for precision
            total_fees = sum([Decimal(str(r.total_fee)) for r in student_records])
            total_paid = sum([Decimal(str(r.amount_paid)) for r in student_records])
            balance = total_fees - total_paid
            
            latest_record = student_records.first()
            
            record_data = {
                'student': student,
                'total_fees': total_fees,
                'total_paid': total_paid,
                'balance': balance,
                'latest_record': latest_record,
                'record_count': student_records.count(),
            }
            
            # Use Decimal comparison for accuracy
            if balance <= Decimal('0.00'):
                balanced_records.append(record_data)
            else:
                outstanding_records.append(record_data)
    
    # Apply search filter
    if search_query:
        balanced_records = [r for r in balanced_records if search_query.lower() in r['student'].full_name.lower() or search_query.lower() in r['student'].student_id.lower()]
        outstanding_records = [r for r in outstanding_records if search_query.lower() in r['student'].full_name.lower() or search_query.lower() in r['student'].student_id.lower()]
    
    # Calculate totals
    total_fees_collected = sum([r['total_paid'] for r in balanced_records + outstanding_records])
    total_outstanding = sum([r['balance'] for r in outstanding_records])
    
    recent_activities = ActivityLog.objects.filter(performed_by_type='bursar')[:20]
    
    context = {
        'bursar': bursar,
        'balanced_records': balanced_records,
        'outstanding_records': outstanding_records,
        'total_fees': total_fees_collected,
        'total_outstanding': total_outstanding,
        'total_students': students.count(),
        'activities': recent_activities,
        'search_query': search_query,
    }
    return render(request, 'bursar_dashboard.html', context)

# ============= TEACHER VIEWS =============
@login_required
def teacher_dashboard(request):
    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        messages.error(request, 'Access denied.')
        return redirect('unified_login')
    
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
    except Teacher.DoesNotExist:
        messages.error(request, 'Access denied.')
        return redirect('unified_login')
    
    if request.method == 'POST':
        try:
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
                is_published=False
            )
            
            ActivityLog.objects.create(
                action='exam_created',
                description=f'Exam "{title}" created as DRAFT with ID {exam.exam_id}',
                performed_by_type='teacher',
                performed_by_name=teacher.full_name
            )
            
            messages.success(request, f'✅ Exam created as DRAFT! Add questions then publish. Exam ID: {exam.exam_id}')
            return redirect('add_questions', exam_id=exam.id)
        except Exception as e:
            messages.error(request, f'Error creating exam: {str(e)}')
            return redirect('create_exam')
    
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
        try:
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
        except Exception as e:
            messages.error(request, f'Error adding question: {str(e)}')
            return redirect('add_questions', exam_id=exam_id)
    
    questions = exam.questions.all()
    context = {
        'exam': exam,
        'questions': questions,
    }
    return render(request, 'add_questions.html', context)

@login_required
def edit_question(request, question_id):
    try:
        teacher = Teacher.objects.get(user=request.user)
        question = Question.objects.get(id=question_id, exam__created_by=teacher)
    except:
        messages.error(request, 'Access denied.')
        return redirect('teacher_dashboard')
    
    if request.method == 'POST':
        try:
            question.question_text = request.POST.get('question_text')
            question.option_a = request.POST.get('option_a')
            question.option_b = request.POST.get('option_b')
            question.option_c = request.POST.get('option_c')
            question.option_d = request.POST.get('option_d')
            question.correct_answer = request.POST.get('correct_answer')
            question.save()
            
            messages.success(request, 'Question updated successfully!')
            return redirect('add_questions', exam_id=question.exam.id)
        except Exception as e:
            messages.error(request, f'Error updating question: {str(e)}')
            return redirect('add_questions', exam_id=question.exam.id)
    
    context = {'question': question}
    return render(request, 'edit_question.html', context)

@login_required
def delete_single_question(request, exam_id, question_number):
    try:
        teacher = Teacher.objects.get(user=request.user)
        exam = Exam.objects.get(id=exam_id, created_by=teacher)
    except:
        messages.error(request, 'Access denied.')
        return redirect('teacher_dashboard')
    
    if request.method == 'POST':
        try:
            question = Question.objects.get(exam=exam, question_number=question_number)
            question_text = question.question_text
            question.delete()
            
            remaining_questions = Question.objects.filter(exam=exam).order_by('id')
            for idx, q in enumerate(remaining_questions, 1):
                q.question_number = idx
                q.save()
            
            ActivityLog.objects.create(
                action='question_deleted',
                description=f'Question deleted from {exam.title}',
                performed_by_type='teacher',
                performed_by_name=teacher.full_name
            )
            
            messages.success(request, f'Question deleted successfully!')
            return redirect('add_questions', exam_id=exam_id)
        except Question.DoesNotExist:
            messages.error(request, 'Question not found.')
        except Exception as e:
            messages.error(request, f'Error deleting question: {str(e)}')
    
    return redirect('add_questions', exam_id=exam_id)

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
    except Exception as e:
        messages.error(request, f'Error deleting exam: {str(e)}')
    
    return redirect('teacher_dashboard')

def delete_student(request, student_id):
    student = get_object_or_404(Student, id=student_id)

    if request.method == "POST":
        student.delete()
        messages.success(request, f"{student.full_name} has been permanently deleted.")
        return redirect('admin_dashboard')

    return render(request, 'admin/delete_student_confirm.html', {'student': student})