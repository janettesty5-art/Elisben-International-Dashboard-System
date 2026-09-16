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
from io import StringIO
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
                        
                        # ✅ AUTO-CALCULATE SUBJECT POSITIONS (display only, no DB write)
                        for subject_result in subject_results:
                            all_results = SubjectResult.objects.filter(
                                subject_name=subject_result.subject_name,
                                term=subject_result.term,
                                academic_year=subject_result.academic_year,
                                student__class_name=result.student.class_name
                            ).order_by('-cum')
                            for idx, sr in enumerate(all_results, start=1):
                                if sr.id == subject_result.id:
                                    subject_result.calculated_position = idx
                                    break
                        
                        # ✅ AUTO-CALCULATE CLASS POSITION if empty (display only, no DB write)
                        display_position = result.position_in_class
                        if not display_position:
                            all_class_results = StudentResult.objects.filter(
                                term=result.term,
                                academic_year=result.academic_year,
                                class_name=result.class_name
                            ).order_by('-average_score')
                            total = all_class_results.count()
                            for idx, r in enumerate(all_class_results, start=1):
                                if r.id == result.id:
                                    display_position = f"{idx}/{total}"
                                    break
                        
                        context = {
                            'result': result,
                            'subject_results': subject_results,
                            'published': published_result,
                            'display_position': display_position,
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
            if exam.is_published:
                # Unpublishing
                exam.is_published = False
                exam.save()
                status = "unpublished (moved to drafts) 📝"
            else:
                # Publishing or RE-publishing
                if exam.version > 1:
                    # This is a re-publish! Increment version so students can retake
                    exam.version += 1
                exam.is_published = True
                exam.save()
                status = f"published ✅ (Version {exam.version})"
            
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
 
    # Show ALL submissions - no limit, no filter
    submissions = ExamSubmission.objects.filter(
        student=student
    ).order_by('-submitted_at')
 
    # Get published exams for student's class
    available_exams_all = Exam.objects.filter(
        class_name=student.class_name,
        is_active=True,
        is_published=True
    )
 
    # Only exclude exams the student has ALREADY submitted for CURRENT version
    available_exams = []
    for exam in available_exams_all:
        already_taken = ExamSubmission.objects.filter(
            student=student,
            exam=exam,
            exam_version=exam.version
        ).exists()
        if not already_taken:
            available_exams.append(exam)
 
    context = {
        'student': student,
        'submissions': submissions,       # ALL results, no limit
        'available_exams': available_exams,
    }
    return render(request, 'student_dashboard.html', context)

@login_required
def track_payment(request):
    """Student (or their parent, logging in with the student's ID) can see every
    single fee entry the Bursar has recorded, plus a % paid chart."""
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, 'Access denied.')
        return redirect('unified_login')

    from decimal import Decimal

    fee_records = FeeRecord.objects.filter(student=student).order_by('-payment_date', '-created_at')

    total_fees = sum([Decimal(str(r.total_fee)) for r in fee_records]) or Decimal('0.00')
    total_paid = sum([Decimal(str(r.amount_paid)) for r in fee_records]) or Decimal('0.00')
    balance = total_fees - total_paid

    if total_fees > 0:
        percent_paid = float((total_paid / total_fees) * 100)
    else:
        percent_paid = 0.0

    # Clamp the chart fill to 0-100 even if there's an overpayment,
    # but keep the real figures for the breakdown text below the chart.
    percent_paid_display = round(percent_paid, 1)
    percent_paid_chart = max(0, min(100, percent_paid))
    is_fully_paid = balance <= 0 and total_fees > 0
    is_overpaid = balance < 0

    # NEW: If this student was part of a sibling discount batch, show the
    # other children in that same batch (no permanent family link — this is
    # just the group they were discounted together with, per batch).
    discount_groups = []
    seen_group_ids = set()
    for fr in fee_records:
        if fr.sibling_group_id and fr.sibling_group_id not in seen_group_ids:
            seen_group_ids.add(fr.sibling_group_id)
            group = fr.sibling_group
            sibling_entries = SiblingDiscountEntry.objects.filter(group=group).exclude(student=student)
            my_entry = SiblingDiscountEntry.objects.filter(group=group, student=student).first()
            discount_groups.append({
                'group': group,
                'my_entry': my_entry,
                'siblings': sibling_entries,
            })

    context = {
        'student': student,
        'fee_records': fee_records,
        'total_fees': total_fees,
        'total_paid': total_paid,
        'balance': balance,
        'percent_paid_display': percent_paid_display,
        'percent_paid_chart': percent_paid_chart,
        'is_fully_paid': is_fully_paid,
        'is_overpaid': is_overpaid,
        'has_records': fee_records.exists(),
        'discount_groups': discount_groups,
    }
    return render(request, 'track_payment.html', context)

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
    import random

    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, 'Access denied.')
        return redirect('student_dashboard')

    try:
        exam = Exam.objects.get(
            exam_id=exam_id,
            class_name=student.class_name,
            is_active=True,
            is_published=True,
        )
    except Exam.DoesNotExist:
        messages.error(request, 'Invalid exam or access denied.')
        return redirect('student_dashboard')

    if ExamSubmission.objects.filter(
        student=student,
        exam=exam,
        exam_version=exam.version,
    ).exists():
        messages.error(request, 'You have already taken this version of the exam.')
        return redirect('student_dashboard')

    questions = list(
        Question.objects.filter(exam__pk=exam.pk).order_by('question_number')
    )

    if not questions:
        messages.error(request, 'This exam has no questions yet.')
        return redirect('student_dashboard')

    shuffled = questions[:]
    if exam.shuffle_questions:
        random.shuffle(shuffled)

    # ── POST: grade the submission ────────────────────────────────────────────
    if request.method == 'POST':
        try:
            submission = ExamSubmission.objects.create(
                student=student,
                exam=exam,
                exam_version=exam.version,
                total_questions=len(questions),
                correct_answers=0,
                score=0,
            )

            correct_count = 0
            for question in questions:   # grade against original unshuffled list
                selected = request.POST.get(f'question_{question.id}', '')
                if selected:
                    is_correct = (
                        selected.strip().upper()
                        == question.correct_answer.strip().upper()
                    )
                    if is_correct:
                        correct_count += 1
                    StudentAnswer.objects.create(
                        submission=submission,
                        question=question,
                        selected_answer=selected,
                        is_correct=is_correct,
                    )

            total_q = len(questions)
            score = round((correct_count / total_q * 100), 2) if total_q > 0 else 0
            submission.correct_answers = correct_count
            submission.score = score
            submission.save()

            ActivityLog.objects.create(
                action='exam_submitted',
                description=(
                    f'{student.full_name} submitted {exam.title} '
                    f'(v{exam.version}) - Score: {score:.2f}%'
                ),
                performed_by_type='student',
                performed_by_name=student.full_name,
            )

            messages.success(request, f'Exam submitted! Your score: {score:.2f}%')
            return redirect('view_result', submission_id=submission.id)

        except Exception as e:
            messages.error(request, f'Error submitting exam: {str(e)}')
            return redirect('student_dashboard')

    # ── GET: build the plain Python list — NO json.dumps() ───────────────────
    # json_script in the template handles serialisation itself.
    # Passing a pre-serialised string causes double-encoding → QS.length = char count.
    questions_data = [
        {
            'id':   q.id,
            'text': q.question_text,
            'a':    q.option_a,
            'b':    q.option_b,
            'c':    q.option_c,
            'd':    q.option_d,
        }
        for q in shuffled          # shuffled order for the student
    ]

    context = {
        'exam':           exam,
        'questions':      shuffled,       # {{ questions|length }} in template
        'questions_data': questions_data, # passed to {{ questions_data|json_script:"questionsData" }}
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

@login_required
def subject_teacher_entry(request):
    from django.db.models import Count, Max
    
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
            
            selected_class = None
            department = ''
            saved_count = 0
            skipped_count = 0
            
            for student_id in student_ids:
                student = Student.objects.get(id=student_id)
                
                if not selected_class:
                    selected_class = student.class_name
                    department = student.department if hasattr(student, 'department') else ''
                
                test_a = float(request.POST.get(f'test_a_{student_id}', 0))
                test_b = float(request.POST.get(f'test_b_{student_id}', 0))
                test_c = float(request.POST.get(f'test_c_{student_id}', 0))
                exam = float(request.POST.get(f'exam_{student_id}', 0))
                
                if test_a == 0 and test_b == 0 and test_c == 0 and exam == 0:
                    skipped_count += 1
                    continue
                
                ltcum = 0
                if term in ['Second Term', 'Third Term']:
                    ltcum = float(request.POST.get(f'ltcum_{student_id}', 0))
                
                position = request.POST.get(f'position_{student_id}')
                position_value = int(position) if position and position.strip() else None
                
                result, created = SubjectResult.objects.update_or_create(
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
                result.save()
                saved_count += 1
                print(f"✅ SAVED: {student.full_name} - Test A: {test_a}, Grade: {result.grade}")
            
            # Auto-calculate positions after saving
            if saved_count > 0 and selected_class:
                calculate_subject_positions(
                    class_name=selected_class,
                    subject_name=subject_name,
                    term=term,
                    academic_year=academic_year
                )
            
            ResultActivityLog.objects.create(
                action='subject_result_entered',
                description=f'{teacher.full_name} entered {subject_name} results for {saved_count} student(s) in {term} (Skipped {skipped_count} empty records)',
                performed_by_type='teacher',
                performed_by_name=teacher.full_name
            )
            
            if saved_count > 0:
                messages.success(request, f'✅ Results saved for {saved_count} student(s) in {subject_name}!')
            else:
                messages.warning(request, f'⚠️ No results saved. Please enter at least one score for at least one student.')
            
            redirect_url = f'/make-result/subject-teacher/?class_name={selected_class}&subject_name={subject_name}&term={term}&academic_year={academic_year}'
            if department:
                redirect_url += f'&department={department}'
            return redirect(redirect_url)
            
        except Exception as e:
            messages.error(request, f'Error saving results: {str(e)}')
            import traceback
            print("SAVE ERROR:", traceback.format_exc())
            return redirect('subject_teacher_entry')
    
    # GET REQUEST
    from datetime import datetime
    current_year = datetime.now().year
    current_month = datetime.now().month
    
    if current_month <= 8:
        academic_year = f"{current_year - 1}/{current_year}"
    else:
        academic_year = f"{current_year}/{current_year + 1}"
    
    academic_year = request.GET.get('academic_year', academic_year)
    classes = Student.objects.values_list('class_name', flat=True).distinct()
    selected_class = request.GET.get('class_name')
    department = request.GET.get('department', '')
    subject_name = request.GET.get('subject_name', '').upper()
    term = request.GET.get('term', 'First Term')
    
    students = []
    is_senior_class = False
    
    if selected_class and subject_name:
        class_upper = selected_class.upper()
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
    
    departments = ['Science', 'Art', 'Commercial']
    
    existing_results = {}
    if subject_name and term and selected_class and students:
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
    
    previous_term_results = {}
    if selected_class and subject_name and term in ['Second Term', 'Third Term'] and students:
        prev_term = 'First Term' if term == 'Second Term' else 'Second Term'
        for student in students:
            try:
                prev_result = SubjectResult.objects.get(
                    student=student,
                    subject_name=subject_name,
                    term=prev_term,
                    academic_year=academic_year
                )
                previous_term_results[student.id] = prev_result.cum
            except SubjectResult.DoesNotExist:
                pass
    
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
        'previous_term_results': previous_term_results,
    }
    
    return render(request, 'result/subject_teacher_entry.html', context)


def test_subject_teacher(request):
    print("🎯 TEST VIEW CALLED!")
    return HttpResponse("Test view working!")


    # ============= DELETE ALL PAYMENT RECORDS FOR A STUDENT (NEW) =============
@login_required
def delete_all_student_payments(request, student_id):
    """Delete ALL payment records for a student - Bursar only"""
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
            student = Student.objects.get(student_id=student_id)
            student_name = student.full_name
            
            # Get all records for this student
            all_records = FeeRecord.objects.filter(student=student)
            record_count = all_records.count()
            total_amount = sum([r.amount_paid for r in all_records])
            
            # Delete all records
            all_records.delete()
            
            # Log activity
            ActivityLog.objects.create(
                action='fee_recorded',
                description=f'All payment records ({record_count} records, ₦{total_amount}) deleted for {student_name}',
                performed_by_type='bursar' if hasattr(request.user, 'bursar') else 'admin',
                performed_by_name=bursar.full_name if hasattr(request.user, 'bursar') else admin.full_name
            )
            
            messages.success(request, f'✅ All payment records for {student_name} deleted successfully! ({record_count} records removed)')
        except Student.DoesNotExist:
            messages.error(request, 'Student not found.')
        except Exception as e:
            messages.error(request, f'Error deleting records: {str(e)}')
    
    return redirect('bursar_dashboard')


# ============= DELETE STUDENT RESULT RECORD (CLASS TEACHER) =============
@login_required
def delete_student_result(request, result_id):
    """Delete a student's result record - Class Teacher only"""
    try:
        teacher = Teacher.objects.get(user=request.user)
        result = StudentResult.objects.get(id=result_id, class_teacher=teacher)
    except:
        messages.error(request, 'Access denied or result not found.')
        return redirect('class_teacher_collate')
    
    if request.method == 'POST':
        try:
            student_name = result.student.full_name
            result.delete()
            
            ResultActivityLog.objects.create(
                action='result_collated',
                description=f'Result record deleted for {student_name}',
                performed_by_type='teacher',
                performed_by_name=teacher.full_name
            )
            
            messages.success(request, f'✅ Result record for {student_name} deleted successfully!')
        except Exception as e:
            messages.error(request, f'Error deleting result: {str(e)}')
    
    return redirect('class_teacher_collate')


# ============= DELETE SUBJECT RESULT RECORD (SUBJECT TEACHER) =============
@login_required
def delete_subject_result(request, student_id, subject_name, term, academic_year):
    """Delete a student's subject result - Subject Teacher only"""
    try:
        teacher = Teacher.objects.get(user=request.user)
        student = Student.objects.get(id=student_id)
        
        result = SubjectResult.objects.get(
            student=student,
            subject_name=subject_name,
            term=term,
            academic_year=academic_year,
            entered_by=teacher
        )
    except:
        messages.error(request, 'Access denied or result not found.')
        return redirect('subject_teacher_entry')
    
    if request.method == 'POST':
        try:
            result.delete()
            
            ResultActivityLog.objects.create(
                action='subject_result_entered',
                description=f'Subject result deleted: {subject_name} for {student.full_name}',
                performed_by_type='teacher',
                performed_by_name=teacher.full_name
            )
            
            messages.success(request, f'✅ {subject_name} result for {student.full_name} deleted successfully!')
        except Exception as e:
            messages.error(request, f'Error deleting result: {str(e)}')
    
    # Redirect back to the same subject/class
    return redirect(f'/make-result/subject-teacher/?class_name={student.class_name}&subject_name={subject_name}&term={term}&academic_year={academic_year}')


# ============= SUBJECT TEACHER EDIT (BULLETPROOF) =============
@login_required
def edit_subject_result(request, result_id):
    """Edit a single subject result - Subject Teacher"""
    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        messages.error(request, 'Access denied. Teachers only.')
        return redirect('subject_teacher_entry')
    
    try:
        result = SubjectResult.objects.get(id=result_id)
    except SubjectResult.DoesNotExist:
        messages.error(request, 'Result not found.')
        return redirect('subject_teacher_entry')
    except Exception as e:
        messages.error(request, f'Error loading result: {str(e)}')
        return redirect('subject_teacher_entry')
    
    if request.method == 'POST':
        try:
            result.subject_name = request.POST.get('subject_name', result.subject_name).upper()
            result.test_a = float(request.POST.get('test_a', result.test_a))
            result.test_b = float(request.POST.get('test_b', result.test_b))
            result.test_c = float(request.POST.get('test_c', result.test_c))
            result.exam = float(request.POST.get('exam', result.exam))
            
            if result.term in ['Second Term', 'Third Term']:
                ltcum_value = request.POST.get('ltcum', '0')
                result.ltcum = float(ltcum_value) if ltcum_value else 0
            
            position = request.POST.get('position')
            result.position_ranking = int(position) if position and position.strip() else None
            
            result.save()
            
            messages.success(request, f'✅ Result updated for {result.student.full_name}!')

            # Redirect back to the same class/subject/term
            from urllib.parse import urlencode
            params = {
                'class_name': result.student.class_name,
                'subject_name': result.subject_name,
                'term': result.term,
                'academic_year': result.academic_year
            }
            return redirect(f'/make-result/subject-teacher/?{urlencode(params)}')
        except Exception as e:
            messages.error(request, f'Error updating result: {str(e)}')
    
    # GET request - show the form
    context = {
        'teacher': teacher,
        'result': result,
    }
    
    # ✅ USE THE CORRECT TEMPLATE PATH (based on your project structure)
    return render(request, 'result/edit_subject_result.html', context)

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
            if class_name_upper in ['SS1', 'SS2', 'SS3']:
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
            # Calculate totals using CUM (not avg_2)
            result.total_subjects = subject_results.count()
            result.score_gained = sum([sr.cum for sr in subject_results])  # Changed from avg_2 to cum
            result.average_score = result.score_gained / result.total_subjects if result.total_subjects > 0 else 0

            if result.average_score >= 45:
                result.status_promotion = "PROMOTED"
            elif result.average_score >= 40:
                result.status_promotion = "PROMOTED ON TRIAL"
            else:
                result.status_promotion = "REPEAT"
            
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

# ============= CLASS TEACHER EDIT (BULLETPROOF) =============
@login_required
def class_teacher_edit_result(request, result_id):
    """Class Teacher Edit - FULL CONTROL"""
    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        messages.error(request, 'Access denied. Teachers only.')
        return redirect('class_teacher_collate')
    
    try:
        result = StudentResult.objects.get(id=result_id)
    except StudentResult.DoesNotExist:
        messages.error(request, 'Result not found.')
        return redirect('class_teacher_collate')
    except Exception as e:
        messages.error(request, f'Error loading result: {str(e)}')
        return redirect('class_teacher_collate')
    
    if request.method == 'POST':
        try:
            # Handle subject deletions
            delete_subject_ids = request.POST.getlist('delete_subject_id')
            for subject_id in delete_subject_ids:
                try:
                    SubjectResult.objects.get(id=subject_id).delete()
                except:
                    pass
            
            # Update existing subjects
            existing_subject_ids = request.POST.getlist('existing_subject_id')
            for subject_id in existing_subject_ids:
                try:
                    subject = SubjectResult.objects.get(id=subject_id)
                    
                    subject.subject_name = request.POST.get(f'subject_name_{subject_id}', subject.subject_name).upper()
                    subject.test_a = float(request.POST.get(f'test_a_{subject_id}', subject.test_a))
                    subject.test_b = float(request.POST.get(f'test_b_{subject_id}', subject.test_b))
                    subject.test_c = float(request.POST.get(f'test_c_{subject_id}', subject.test_c))
                    subject.exam = float(request.POST.get(f'exam_{subject_id}', subject.exam))
                    
                    if result.term in ['Second Term', 'Third Term']:
                        ltcum_val = request.POST.get(f'ltcum_{subject_id}', '0')
                        subject.ltcum = float(ltcum_val) if ltcum_val else 0
                    
                    pos_val = request.POST.get(f'position_{subject_id}')
                    subject.position_ranking = int(pos_val) if pos_val and pos_val.strip() else None
                    
                    subject.save()
                except Exception as e:
                    messages.warning(request, f'Error updating subject: {str(e)}')
            
            # Add new subjects
            post_keys = list(request.POST.keys())
            new_subject_numbers = set()
            for key in post_keys:
                if key.startswith('new_subject_name_'):
                    num = key.replace('new_subject_name_', '')
                    new_subject_numbers.add(num)
            
            for num in new_subject_numbers:
                subject_name = request.POST.get(f'new_subject_name_{num}', '').upper().strip()
                if not subject_name:
                    continue
                
                test_a = float(request.POST.get(f'new_test_a_{num}', 0))
                test_b = float(request.POST.get(f'new_test_b_{num}', 0))
                test_c = float(request.POST.get(f'new_test_c_{num}', 0))
                exam = float(request.POST.get(f'new_exam_{num}', 0))
                
                ltcum = 0
                if result.term in ['Second Term', 'Third Term']:
                    ltcum = float(request.POST.get(f'new_ltcum_{num}', 0))
                
                position = request.POST.get(f'new_position_{num}')
                position_value = int(position) if position and position.strip() else None
                
                try:
                    SubjectResult.objects.create(
                        student=result.student,
                        subject_name=subject_name,
                        term=result.term,
                        academic_year=result.academic_year,
                        test_a=test_a,
                        test_b=test_b,
                        test_c=test_c,
                        exam=exam,
                        ltcum=ltcum if result.term in ['Second Term', 'Third Term'] else None,
                        position_ranking=position_value,
                        entered_by=teacher,
                    )
                except Exception as e:
                    messages.warning(request, f'Error adding new subject: {str(e)}')
            
            # Update other fields
            result.times_school_opened = int(request.POST.get('times_opened', result.times_school_opened))
            result.times_present = int(request.POST.get('times_present', result.times_present))
            result.times_absent = int(request.POST.get('times_absent', result.times_absent))
            
            # Update dates
            from datetime import datetime
            vac_date = request.POST.get('vacation_date')
            res_date = request.POST.get('resumption_date')
            
            if vac_date:
                try:
                    result.vacation_date = datetime.strptime(vac_date, '%Y-%m-%d').date()
                except:
                    pass
            if res_date:
                try:
                    result.resumption_date = datetime.strptime(res_date, '%Y-%m-%d').date()
                except:
                    pass
            
            # Update fees
            result.next_term_pta_fee = float(request.POST.get('pta_fee', result.next_term_pta_fee or 0))
            result.next_term_school_fee = float(request.POST.get('school_fee', result.next_term_school_fee or 0))
            
            # Update affective domain
            result.affective_punctuality = request.POST.get('aff_punctuality', result.affective_punctuality)
            result.affective_neatness = request.POST.get('aff_neatness', result.affective_neatness)
            result.affective_politeness = request.POST.get('aff_politeness', result.affective_politeness)
            result.affective_honesty = request.POST.get('aff_honesty', result.affective_honesty)
            result.affective_relationship = request.POST.get('aff_relationship', result.affective_relationship)
            result.affective_self_control = request.POST.get('aff_self_control', result.affective_self_control)
            result.affective_attentiveness = request.POST.get('aff_attentiveness', result.affective_attentiveness)
            
            # Update psychomotor domain
            result.psycho_handwriting = request.POST.get('psycho_handwriting', result.psycho_handwriting)
            result.psycho_sports = request.POST.get('psycho_sports', result.psycho_sports)
            result.psycho_handling_tools = request.POST.get('psycho_tools', result.psycho_handling_tools)
            result.psycho_verbal_fluency = request.POST.get('psycho_verbal', result.psycho_verbal_fluency)
            result.psycho_games = request.POST.get('psycho_games', result.psycho_games)
            result.psycho_drawing = request.POST.get('psycho_drawing', result.psycho_drawing)
            
            # Update comment
            result.class_teacher_comment = request.POST.get('class_teacher_comment', result.class_teacher_comment)
            
            # Recalculate statistics
            subject_results_fresh = SubjectResult.objects.filter(
                student=result.student,
                term=result.term,
                academic_year=result.academic_year
            )
            
            result.total_subjects = subject_results_fresh.count()
            if result.total_subjects > 0:
                result.score_gained = sum(float(sr.cum) for sr in subject_results_fresh)
                result.average_score = result.score_gained / result.total_subjects
            else:
                result.score_gained = 0
                result.average_score = 0
            
            # Calculate position
            results_in_class = StudentResult.objects.filter(
                term=result.term,
                academic_year=result.academic_year,
                class_name=result.class_name
            ).order_by('-average_score')
            
            position = 1
            for idx, r in enumerate(results_in_class, 1):
                if r.id == result.id:
                    position = idx
                    break
            
            result.position_in_class = f"{position}/{results_in_class.count()}"

            if result.average_score >= 45:
                result.status_promotion = "PROMOTED"
            elif result.average_score >= 40:
                result.status_promotion = "PROMOTED ON TRIAL"
            else:
                result.status_promotion = "REPEAT"
            
            result.save()
            
            # Log activity
            try:
                ResultActivityLog.objects.create(
                    action='result_edited',
                    description=f'Class teacher {teacher.full_name} edited result for {result.student.full_name}',
                    student_result=result,
                    performed_by_type='class_teacher',
                    performed_by_name=teacher.full_name
                )
            except:
                pass
            
            messages.success(request, f'✅ Result updated successfully for {result.student.full_name}!')

            # Redirect back to the same class/term
            from urllib.parse import urlencode
            params = {
                'class_name': result.class_name,
                'term': result.term,
                'academic_year': result.academic_year
            }
            return redirect(f'/make-result/class-teacher/?{urlencode(params)}')
            
        except Exception as e:
            messages.error(request, f'Error updating result: {str(e)}')
    
    # GET request - show the form
    subject_results = SubjectResult.objects.filter(
        student=result.student,
        term=result.term,
        academic_year=result.academic_year
    ).order_by('subject_name')
    
    context = {
        'teacher': teacher,
        'result': result,
        'subject_results': subject_results,
    }
    
    # ✅ USE THE CORRECT TEMPLATE PATH (based on your project structure)
    return render(request, 'result/edit_result.html', context)
    

@login_required
def delete_subject_result_post(request):
    """Delete a student's subject result via POST - Subject Teacher only"""
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('subject_teacher_entry')
    
    try:
        teacher = Teacher.objects.get(user=request.user)
        student_id = request.POST.get('student_id')
        subject_name = request.POST.get('subject_name')
        term = request.POST.get('term')
        academic_year = request.POST.get('academic_year')
        
        student = Student.objects.get(id=student_id)
        
        result = SubjectResult.objects.get(
            student=student,
            subject_name=subject_name,
            term=term,
            academic_year=academic_year
        )
        
        # Check if teacher has permission
        if result.entered_by != teacher and student.class_teacher != teacher:
            messages.error(request, 'You do not have permission to delete this result.')
            return redirect('subject_teacher_entry')
        
        result.delete()
        
        ResultActivityLog.objects.create(
            action='subject_result_deleted',
            description=f'Subject result deleted: {subject_name} for {student.full_name}',
            performed_by_type='teacher',
            performed_by_name=teacher.full_name
        )
        
        messages.success(request, f'✅ {subject_name} result for {student.full_name} deleted successfully!')
        
    except Teacher.DoesNotExist:
        messages.error(request, 'Access denied. Teachers only.')
    except Student.DoesNotExist:
        messages.error(request, 'Student not found.')
    except SubjectResult.DoesNotExist:
        messages.error(request, 'Result not found.')
    except Exception as e:
        messages.error(request, f'Error deleting result: {str(e)}')
    
    return redirect('subject_teacher_entry')


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

# ============================================================
# NEW: PRINCIPAL STAMP & PUBLISH (same power as Admin)
# ============================================================

@login_required
def principal_add_stamp(request, result_id):
    """Principal adds a stamp to a single result - mirrors admin_add_stamp"""
    try:
        principal = Principal.objects.get(user=request.user)
        result = StudentResult.objects.get(id=result_id)
        
        result.has_stamp = True
        result.stamped_at = timezone.now()
        result.stamped_by_principal = principal
        result.save()
        
        ResultActivityLog.objects.create(
            action='stamp_added',
            description=f'Stamp added to {result.student.full_name} result by Principal',
            student_result=result,
            performed_by_type='principal',
            performed_by_name=principal.full_name
        )
        
        messages.success(request, '✅ Stamp added!')
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
    
    return redirect('principal_result_review')

@login_required
def principal_stamp_batch(request):
    """Principal stamps multiple/all selected results at once"""
    if request.method == 'POST':
        try:
            principal = Principal.objects.get(user=request.user)
            result_ids = request.POST.getlist('result_ids')
            
            stamped_count = 0
            for result_id in result_ids:
                result = StudentResult.objects.get(id=result_id)
                result.has_stamp = True
                result.stamped_at = timezone.now()
                result.stamped_by_principal = principal
                result.save()
                stamped_count += 1
            
            if stamped_count:
                ResultActivityLog.objects.create(
                    action='stamp_added',
                    description=f'{stamped_count} results stamped in bulk by Principal {principal.full_name}',
                    performed_by_type='principal',
                    performed_by_name=principal.full_name
                )
            
            messages.success(request, f'✅ {stamped_count} result(s) stamped!')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    
    return redirect('principal_result_review')

@login_required
def principal_publish_result(request, result_id):
    """Principal publishes a single stamped result - mirrors admin_publish_result"""
    try:
        principal = Principal.objects.get(user=request.user)
        result = StudentResult.objects.get(id=result_id, has_stamp=True)
        
        pin = PublishedResult.generate_pin()
        
        PublishedResult.objects.create(
            result=result,
            pin=pin,
            published_by_principal=principal,
            academic_year=result.academic_year,
            term=result.term,
            class_name=result.class_name
        )
        
        result.status = 'published'
        result.save()
        
        ResultActivityLog.objects.create(
            action='result_published',
            description=f'Result published for {result.student.full_name} by Principal - PIN: {pin}',
            student_result=result,
            performed_by_type='principal',
            performed_by_name=principal.full_name
        )
        
        messages.success(request, f'✅ Result published! PIN: {pin}')
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
    
    return redirect('principal_result_review')

@login_required
def principal_publish_batch(request):
    """Principal publishes multiple/all selected results at once.
    Any result not yet stamped is auto-stamped first, so one click handles everything."""
    if request.method == 'POST':
        try:
            principal = Principal.objects.get(user=request.user)
            result_ids = request.POST.getlist('result_ids')
            
            published_count = 0
            auto_stamped_count = 0
            skipped_count = 0
            
            for result_id in result_ids:
                result = StudentResult.objects.get(id=result_id)
                
                # Skip results that are already published
                if result.status == 'published':
                    skipped_count += 1
                    continue
                
                # Auto-stamp if not already stamped
                if not result.has_stamp:
                    result.has_stamp = True
                    result.stamped_at = timezone.now()
                    result.stamped_by_principal = principal
                    result.save()
                    auto_stamped_count += 1
                
                pin = PublishedResult.generate_pin()
                PublishedResult.objects.create(
                    result=result,
                    pin=pin,
                    published_by_principal=principal,
                    academic_year=result.academic_year,
                    term=result.term,
                    class_name=result.class_name
                )
                
                result.status = 'published'
                result.save()
                published_count += 1
            
            if published_count:
                ResultActivityLog.objects.create(
                    action='result_published',
                    description=f'{published_count} results published in bulk by Principal {principal.full_name}' + (f' ({auto_stamped_count} auto-stamped first)' if auto_stamped_count else ''),
                    performed_by_type='principal',
                    performed_by_name=principal.full_name
                )
            
            msg = f'✅ {published_count} result(s) published!'
            if auto_stamped_count:
                msg += f' ({auto_stamped_count} were auto-stamped first)'
            if skipped_count:
                msg += f' {skipped_count} already published, skipped.'
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

def result_bulletin(request):
    """Show school bulletin before result checking"""
    return render(request, 'result/result_bulletin.html')

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
            
            # ✅ AUTO-CALCULATE SUBJECT POSITIONS (display only, no DB write)
            for subject_result in subject_results:
                all_results = SubjectResult.objects.filter(
                    subject_name=subject_result.subject_name,
                    term=subject_result.term,
                    academic_year=subject_result.academic_year,
                    student__class_name=result.student.class_name
                ).order_by('-cum')
                for idx, sr in enumerate(all_results, start=1):
                    if sr.id == subject_result.id:
                        subject_result.calculated_position = idx
                        break
            
            # ✅ AUTO-CALCULATE CLASS POSITION if empty (display only, no DB write)
            display_position = result.position_in_class
            if not display_position:
                all_class_results = StudentResult.objects.filter(
                    term=result.term,
                    academic_year=result.academic_year,
                    class_name=result.class_name
                ).order_by('-average_score')
                total = all_class_results.count()
                for idx, r in enumerate(all_class_results, start=1):
                    if r.id == result.id:
                        display_position = f"{idx}/{total}"
                        break
            
            context = {
                'result': result,
                'subject_results': subject_results,
                'published': published_result,
                'display_position': display_position,
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
        
        # ✅ AUTO-CALCULATE SUBJECT POSITIONS (same as student view)
        for subject_result in subject_results:
            all_results = SubjectResult.objects.filter(
                subject_name=subject_result.subject_name,
                term=subject_result.term,
                academic_year=subject_result.academic_year,
                student__class_name=result.student.class_name
            ).order_by('-cum')
            for idx, sr in enumerate(all_results, start=1):
                if sr.id == subject_result.id:
                    subject_result.calculated_position = idx
                    break
        
        # ✅ AUTO-CALCULATE CLASS POSITION if empty
        display_position = result.position_in_class
        if not display_position:
            all_class_results = StudentResult.objects.filter(
                term=result.term,
                academic_year=result.academic_year,
                class_name=result.class_name
            ).order_by('-average_score')
            total = all_class_results.count()
            for idx, r in enumerate(all_class_results, start=1):
                if r.id == result.id:
                    display_position = f"{idx}/{total}"
                    break
        
        try:
            published = PublishedResult.objects.get(result=result)
        except PublishedResult.DoesNotExist:
            published = None
        
        context = {
            'result': result,
            'subject_results': subject_results,
            'published': published,
            'display_position': display_position,
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
 
    # ALL activity logs - no [:20] limit
    recent_activities = ActivityLog.objects.all().order_by('-timestamp')
 
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
def admin_change_id(request):
    """Let the Admin (proprietor) change their own Admin ID for privacy."""
    try:
        admin = Admin.objects.get(user=request.user)
    except Admin.DoesNotExist:
        messages.error(request, 'Access denied. Admin only.')
        return redirect('unified_login')

    if request.method == 'POST':
        new_id = request.POST.get('new_admin_id', '').strip().upper()

        if not new_id:
            messages.error(request, 'Please enter a new ID.')
            return redirect('admin_change_id')

        if ' ' in new_id:
            messages.error(request, 'ID cannot contain spaces.')
            return redirect('admin_change_id')

        if new_id == admin.admin_id:
            messages.error(request, 'That is already your current ID.')
            return redirect('admin_change_id')

        if Admin.objects.filter(admin_id=new_id).exclude(pk=admin.pk).exists():
            messages.error(request, f'ID "{new_id}" is already taken. Please choose a different one.')
            return redirect('admin_change_id')

        old_id = admin.admin_id
        admin.admin_id = new_id
        admin.save()

        ActivityLog.objects.create(
            action='admin_id_changed',
            description=f'Admin changed their login ID from {old_id} to {new_id}',
            performed_by_type='admin',
            performed_by_name=admin.full_name
        )

        messages.success(request, f'✅ Your Admin ID has been changed to {new_id}. Please use this new ID next time you log in.')
        return redirect('admin_dashboard')

    context = {'admin': admin}
    return render(request, 'admin_change_id.html', context)

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
            if class_name_upper in ['SS1', 'SS2', 'SS3']:
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

# ============================================================
# NEW: SIBLING DISCOUNT (3+ children discounted together)
# ============================================================
@login_required
def start_discount_record(request):
    """Bursar (or Admin) records a discounted fee for 3+ siblings in one batch.
    This is picked manually each time — no permanent family link is stored."""
    try:
        bursar = Bursar.objects.get(user=request.user)
        is_admin = False
        user_name = bursar.full_name
    except Bursar.DoesNotExist:
        try:
            admin = Admin.objects.get(user=request.user)
            is_admin = True
            user_name = admin.full_name
        except Admin.DoesNotExist:
            messages.error(request, 'Access denied.')
            return redirect('unified_login')

    from decimal import Decimal, InvalidOperation

    if request.method == 'POST':
        try:
            student_ids = request.POST.getlist('student_id[]')
            original_fees = request.POST.getlist('original_fee[]')
            discounts = request.POST.getlist('discount_amount[]')
            amounts_paid = request.POST.getlist('amount_paid[]')

            fee_type = request.POST.get('fee_type', 'Tuition Fee').strip() or 'Tuition Fee'
            payment_method = request.POST.get('payment_method')
            payment_date = request.POST.get('payment_date') or timezone.now().date()
            current_term = Term.objects.filter(is_current=True).first()

            def to_decimal(val):
                try:
                    return Decimal(val) if val not in (None, '',) else Decimal('0')
                except InvalidOperation:
                    return Decimal('0')

            rows = []
            for i in range(len(student_ids)):
                sid = (student_ids[i] or '').strip()
                if not sid:
                    continue
                rows.append({
                    'student_id': sid,
                    'original_fee': to_decimal(original_fees[i] if i < len(original_fees) else '0'),
                    'discount': to_decimal(discounts[i] if i < len(discounts) else '0'),
                    'amount_paid': to_decimal(amounts_paid[i] if i < len(amounts_paid) else '0'),
                })

            if len(rows) < 3:
                messages.error(request, '⚠️ A sibling discount record needs at least 3 children. Please add more before submitting.')
                return redirect('start_discount_record')

            group = SiblingDiscountRecord.objects.create(
                fee_type=fee_type,
                payment_method=payment_method,
                payment_date=payment_date,
                term=current_term,
                created_by=None if is_admin else bursar,
                created_by_admin=admin if is_admin else None,
            )

            total_before = Decimal('0.00')
            total_discount = Decimal('0.00')
            total_after = Decimal('0.00')
            total_paid = Decimal('0.00')
            child_names = []

            for row in rows:
                student = Student.objects.get(student_id=row['student_id'])
                fee_after = row['original_fee'] - row['discount']
                if fee_after < 0:
                    fee_after = Decimal('0.00')

                SiblingDiscountEntry.objects.create(
                    group=group,
                    student=student,
                    fee_before_discount=row['original_fee'],
                    discount_amount=row['discount'],
                    amount_paid=row['amount_paid'],
                )

                FeeRecord.objects.create(
                    student=student,
                    term=current_term,
                    total_fee=fee_after,
                    amount_paid=row['amount_paid'],
                    fee_type=f"{fee_type} (Sibling Discount)",
                    payment_method=payment_method,
                    payment_date=payment_date,
                    recorded_by=None if is_admin else bursar,
                    recorded_by_admin=admin if is_admin else None,
                    sibling_group=group,
                )

                total_before += row['original_fee']
                total_discount += row['discount']
                total_after += fee_after
                total_paid += row['amount_paid']
                child_names.append(student.full_name)

            group.total_fee_before_discount = total_before
            group.total_discount_amount = total_discount
            group.total_fee_after_discount = total_after
            group.total_amount_paid = total_paid
            group.save()

            ActivityLog.objects.create(
                action='fee_recorded',
                description=f'Sibling discount record ({group.group_id}) created for {len(rows)} children: {", ".join(child_names)}. Before: ₦{total_before} → After: ₦{total_after} (saved ₦{total_discount})',
                performed_by_type='admin' if is_admin else 'bursar',
                performed_by_name=user_name
            )

            messages.success(
                request,
                f'✅ Discount record {group.group_id} created for {len(rows)} children! '
                f'Total before discount: ₦{total_before:.2f} → After discount: ₦{total_after:.2f} '
                f'(saved ₦{total_discount:.2f} total)'
            )
            return redirect('bursar_dashboard')

        except Student.DoesNotExist:
            messages.error(request, 'One of the selected students could not be found. Please check the student IDs.')
        except Exception as e:
            messages.error(request, f'Error creating discount record: {str(e)}')

    students = Student.objects.all().order_by('full_name')
    students_json = [
        {'student_id': s.student_id, 'full_name': s.full_name, 'class_name': s.class_name}
        for s in students
    ]
    recent_batches = SiblingDiscountRecord.objects.all().order_by('-created_at')[:15]
    context = {
        'students': students,
        'students_json': students_json,
        'is_admin': is_admin,
        'recent_batches': recent_batches,
    }
    return render(request, 'start_discount_record.html', context)

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
    active_tab = request.GET.get('tab', 'overview')
    
    context = {
        'bursar': bursar,
        'balanced_records': balanced_records,
        'outstanding_records': outstanding_records,
        'total_fees': total_fees_collected,
        'total_outstanding': total_outstanding,
        'total_students': students.count(),
        'activities': recent_activities,
        'search_query': search_query,
        'active_tab': active_tab,
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
 
    published_exams = Exam.objects.filter(
        created_by=teacher, is_published=True
    ).order_by('-created_at')
 
    draft_exams = Exam.objects.filter(
        created_by=teacher, is_published=False
    ).order_by('-created_at')
 
    # ALL submissions for this teacher's exams - no [:10] limit
    submissions = ExamSubmission.objects.filter(
        exam__created_by=teacher
    ).order_by('-submitted_at')
 
    context = {
        'teacher': teacher,
        'published_exams': published_exams,
        'draft_exams': draft_exams,
        'recent_submissions': submissions,   # ALL submissions, not just 10
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
            
            # ✅ NEW: Increment exam version when question is edited
            exam = question.exam
            if exam.is_published:
                exam.version += 1
                exam.save()
                messages.info(request, f'Exam version updated to v{exam.version}. Students can now retake.')
            
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


@login_required
def download_pins(request):
    """Download PINs as a printable HTML page grouped by class"""
    try:
        admin = Admin.objects.get(user=request.user)
    except Admin.DoesNotExist:
        messages.error(request, 'Access denied.')
        return redirect('unified_login')
    
    # Apply same filters as the published results page
    academic_year = request.GET.get('academic_year')
    term = request.GET.get('term')
    class_name = request.GET.get('class_name')
    
    published = PublishedResult.objects.all().order_by('class_name', 'result__student__full_name')
    
    if academic_year:
        published = published.filter(academic_year=academic_year)
    if term:
        published = published.filter(term=term)
    if class_name:
        published = published.filter(class_name=class_name)
    
    # Group by class
    from collections import OrderedDict
    pins_by_class = OrderedDict()
    for pub in published:
        cls = pub.class_name
        if cls not in pins_by_class:
            pins_by_class[cls] = []
        pins_by_class[cls].append(pub)
    
    # Build filter description for the header
    filter_info = []
    if academic_year:
        filter_info.append(f"Year: {academic_year}")
    if term:
        filter_info.append(f"Term: {term}")
    if class_name:
        filter_info.append(f"Class: {class_name}")
    filter_desc = " | ".join(filter_info) if filter_info else "All Records"
    
    context = {
        'pins_by_class': pins_by_class,
        'filter_desc': filter_desc,
        'academic_year': academic_year or 'All Years',
        'term': term or 'All Terms',
    }
    return render(request, 'result/download_pins.html', context)

def calculate_subject_positions(class_name, subject_name, term, academic_year):
    """
    Calculate and save position for all students in a subject
    Called after subject results are entered
    """
    # Get all results for this subject, ordered by CUM score
    subject_results = SubjectResult.objects.filter(
        student__class_name=class_name,
        subject_name=subject_name,
        term=term,
        academic_year=academic_year
    ).order_by('-cum')  # Highest score first
    
    # Assign positions
    for position, subject_result in enumerate(subject_results, start=1):
        subject_result.position_ranking = position
        subject_result.save()
    
    print(f"✅ Positions calculated for {subject_name} in {class_name}")

    from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

@login_required
def admin_wipe_all_exams(request):
    """
    Delete ALL exams and questions from the system (Admin only)
    """
    # Check if user is admin
    try:
        admin = Admin.objects.get(user=request.user)
    except Admin.DoesNotExist:
        messages.error(request, 'Unauthorized access.')
        return redirect('unified_login')
    
    if request.method == 'POST':
        confirmation = request.POST.get('confirmation')
        
        if confirmation == 'DELETE ALL EXAMS':
            # Count before deletion
            exam_count = Exam.objects.count()
            question_count = Question.objects.count()
            submission_count = ExamSubmission.objects.count()
            
            # Delete everything
            ExamSubmission.objects.all().delete()
            Question.objects.all().delete()
            Exam.objects.all().delete()
            
            # Log the action
            ActivityLog.objects.create(
                action='exam_deleted',
                description=f'Admin {admin.full_name} wiped entire CBT system: {exam_count} exams, {question_count} questions, {submission_count} submissions deleted',
                performed_by_type='admin',
                performed_by_name=admin.full_name
            )
            
            messages.success(request, f'✅ Successfully deleted {exam_count} exams, {question_count} questions, and {submission_count} submissions. CBT system is now clean.')
            return redirect('admin_dashboard')
        else:
            messages.error(request, 'Incorrect confirmation text. Deletion cancelled.')
    
    # Get counts for display
    context = {
        'exam_count': Exam.objects.count(),
        'question_count': Question.objects.count(),
        'submission_count': ExamSubmission.objects.count(),
    }
    
    return render(request, 'wipe_exams_confirm.html', context)
    """
    Delete ALL exams and questions from the system (Admin only)
    """
    # Check if user is admin
    if request.session.get('role') != 'admin':
        messages.error(request, 'Unauthorized access.')
        return redirect('unified_login')
    
    if request.method == 'POST':
        confirmation = request.POST.get('confirmation')
        
        if confirmation == 'DELETE ALL EXAMS':
            # Count before deletion
            exam_count = Exam.objects.count()
            question_count = Question.objects.count()
            submission_count = ExamSubmission.objects.count()
            
            # Delete everything
            ExamSubmission.objects.all().delete()
            Question.objects.all().delete()
            Exam.objects.all().delete()
            
            # Log the action
            ResultActivityLog.objects.create(
                action='exams_wiped',
                description=f'Admin wiped entire CBT system: {exam_count} exams, {question_count} questions, {submission_count} submissions deleted',
                performed_by_type='admin',
                performed_by_name=request.session.get('user_name', 'Admin')
            )
            
            messages.success(request, f'✅ Successfully deleted {exam_count} exams, {question_count} questions, and {submission_count} submissions. CBT system is now clean.')
            return redirect('admin_dashboard')
        else:
            messages.error(request, 'Incorrect confirmation text. Deletion cancelled.')
    
    # Get counts for display
    context = {
        'exam_count': Exam.objects.count(),
        'question_count': Question.objects.count(),
        'submission_count': ExamSubmission.objects.count(),
    }
    
    return render(request, 'admin/wipe_exams_confirm.html', context)

@login_required
def edit_exam_duration(request, exam_id):
    """Allow teacher to edit exam duration (time) only."""
    try:
        teacher = Teacher.objects.get(user=request.user)
        exam = Exam.objects.get(id=exam_id, created_by=teacher)
    except:
        messages.error(request, 'Access denied.')
        return redirect('teacher_dashboard')
 
    if request.method == 'POST':
        try:
            new_duration = int(request.POST.get('duration_minutes', exam.duration_minutes))
            if new_duration < 5:
                new_duration = 5
            if new_duration > 300:
                new_duration = 300
 
            old_duration = exam.duration_minutes
            exam.duration_minutes = new_duration
            exam.save()
 
            ActivityLog.objects.create(
                action='exam_edited',
                description=f'Exam "{exam.title}" duration changed from {old_duration} to {new_duration} minutes',
                performed_by_type='teacher',
                performed_by_name=teacher.full_name
            )
 
            messages.success(request, f'✅ Duration updated to {new_duration} minutes!')
            return redirect('teacher_dashboard')
        except Exception as e:
            messages.error(request, f'Error updating duration: {str(e)}')
 
    context = {'exam': exam, 'teacher': teacher}
    return render(request, 'edit_exam_duration.html', context)


@login_required
def admin_fix_promotion_status(request):
    """
    Recalculate status_promotion for ALL StudentResult records
    using the new thresholds (0-39 REPEAT, 40-44 PROMOTED ON TRIAL, 45+ PROMOTED).
    Works without shell access — runs as a normal web request.
    """
    try:
        admin = Admin.objects.get(user=request.user)
    except Admin.DoesNotExist:
        messages.error(request, 'Access denied.')
        return redirect('unified_login')

    if request.method == 'POST':
        confirmation = request.POST.get('confirmation')

        if confirmation == 'FIX PROMOTION STATUS':
            output = StringIO()
            try:
                call_command('fix_promotion_status', stdout=output)
                result_text = output.getvalue()

                ActivityLog.objects.create(
                    action='result_generated',
                    description=f'Admin {admin.full_name} ran promotion status fix for all results',
                    performed_by_type='admin',
                    performed_by_name=admin.full_name
                )

                messages.success(request, 'Promotion status fix completed! See output below.')
                context = {'output': result_text, 'ran': True}
                return render(request, 'fix_promotion_confirm.html', context)
            except Exception as e:
                messages.error(request, f'Error running fix: {str(e)}')
        else:
            messages.error(request, 'Incorrect confirmation text. Action cancelled.')

    from .models import StudentResult
    context = {
        'total_results': StudentResult.objects.count(),
    }
    return render(request, 'fix_promotion_confirm.html', context)

# ============================================================
# NEW: ID CARD GENERATOR (Admin & Principal only)
# ============================================================

def _get_id_card_actor(request):
    """Returns (admin_or_none, principal_or_none, is_admin, actor_name) or None if access denied."""
    try:
        admin = Admin.objects.get(user=request.user)
        return admin, None, True, admin.full_name
    except Admin.DoesNotExist:
        try:
            principal = Principal.objects.get(user=request.user)
            return None, principal, False, principal.full_name
        except Principal.DoesNotExist:
            return None, None, None, None


@login_required
def id_card_hub(request):
    """Landing page for the ID Card Generator - Admin and Principal only."""
    admin, principal, is_admin, actor_name = _get_id_card_actor(request)
    if is_admin is None:
        messages.error(request, 'Access denied. Admin or Principal only.')
        return redirect('unified_login')

    search_query = request.GET.get('search', '')
    cards = IDCard.objects.all()
    if search_query:
        cards = cards.filter(
            Q(full_name__icontains=search_query) | Q(id_number__icontains=search_query)
        )

    context = {
        'admin': admin,
        'principal': principal,
        'is_admin': is_admin,
        'cards': cards[:200],
        'search_query': search_query,
        'total_cards': IDCard.objects.count(),
    }
    return render(request, 'id_card_hub.html', context)


@login_required
def generate_student_id_card(request):
    """Generate an ID card for an already-registered student."""
    admin, principal, is_admin, actor_name = _get_id_card_actor(request)
    if is_admin is None:
        messages.error(request, 'Access denied. Admin or Principal only.')
        return redirect('unified_login')

    if request.method == 'POST':
        try:
            student = Student.objects.get(student_id=request.POST.get('student_id'))
            photo = request.FILES.get('photo') or student.profile_picture or None

            card = IDCard.objects.create(
                holder_type='student',
                student=student,
                full_name=student.full_name,
                id_number=student.student_id,
                phone_number=student.phone or '',
                role_title=f"{student.class_name} Student",
                photo=photo,
                generated_by_admin=admin,
                generated_by_principal=principal,
            )

            ActivityLog.objects.create(
                action='student_registered',
                description=f'ID Card generated for student {student.full_name} ({student.student_id})',
                performed_by_type='admin' if is_admin else 'principal',
                performed_by_name=actor_name
            )

            messages.success(request, f'✅ ID Card generated for {student.full_name}!')
            return redirect('view_id_card', card_id=card.id)
        except Student.DoesNotExist:
            messages.error(request, 'Student not found.')
        except Exception as e:
            messages.error(request, f'Error generating ID card: {str(e)}')

    students = Student.objects.all().order_by('full_name')
    context = {
        'students': students,
        'is_admin': is_admin,
    }
    return render(request, 'generate_student_id_card.html', context)


@login_required
def generate_staff_id_card(request):
    """Generate an ID card for Teaching Staff or Non-Teaching Staff.
    Teaching staff must already be a registered Teacher (picked from a dropdown).
    Non-Teaching staff can either be picked from existing records, or a brand
    new one can be registered right here in the same step."""
    admin, principal, is_admin, actor_name = _get_id_card_actor(request)
    if is_admin is None:
        messages.error(request, 'Access denied. Admin or Principal only.')
        return redirect('unified_login')

    if request.method == 'POST':
        try:
            staff_type = request.POST.get('staff_type')
            photo = request.FILES.get('photo')

            if staff_type == 'teaching':
                teacher = Teacher.objects.get(id=request.POST.get('teacher_id'))

                card = IDCard.objects.create(
                    holder_type='teaching_staff',
                    teacher=teacher,
                    full_name=teacher.full_name,
                    id_number=teacher.teacher_id,
                    phone_number=teacher.phone or '',
                    role_title=f"{teacher.subject} Teacher",
                    photo=photo,
                    generated_by_admin=admin,
                    generated_by_principal=principal,
                )
                holder_name = teacher.full_name

            elif staff_type == 'non_teaching':
                existing_id = request.POST.get('non_teaching_staff_id', '')

                if existing_id and existing_id != '__new__':
                    staff = NonTeachingStaff.objects.get(id=existing_id)
                    new_phone = request.POST.get('phone_number', '').strip()
                    new_role = request.POST.get('role_title', '').strip()
                    if new_phone:
                        staff.phone = new_phone
                    if new_role:
                        staff.role_title = new_role
                    staff.save()
                else:
                    full_name = request.POST.get('new_full_name', '').strip()
                    phone = request.POST.get('phone_number', '').strip()
                    role_title = request.POST.get('role_title', '').strip() or 'Staff'

                    if not full_name:
                        messages.error(request, 'Please enter the staff full name.')
                        return redirect('generate_staff_id_card')

                    staff = NonTeachingStaff.objects.create(
                        full_name=full_name,
                        phone=phone,
                        role_title=role_title,
                        registered_by=admin,
                        registered_by_principal=principal,
                    )

                    ActivityLog.objects.create(
                        action='teacher_registered',
                        description=f'New non-teaching staff registered: {staff.full_name} ({staff.staff_id}) - {staff.role_title}',
                        performed_by_type='admin' if is_admin else 'principal',
                        performed_by_name=actor_name
                    )

                card = IDCard.objects.create(
                    holder_type='non_teaching_staff',
                    non_teaching_staff=staff,
                    full_name=staff.full_name,
                    id_number=staff.staff_id,
                    phone_number=staff.phone or '',
                    role_title=staff.role_title or 'Staff',
                    photo=photo,
                    generated_by_admin=admin,
                    generated_by_principal=principal,
                )
                holder_name = staff.full_name
            else:
                messages.error(request, 'Please choose Teaching Staff or Non-Teaching Staff.')
                return redirect('generate_staff_id_card')

            messages.success(request, f'✅ ID Card generated for {holder_name}!')
            return redirect('view_id_card', card_id=card.id)

        except Teacher.DoesNotExist:
            messages.error(request, 'Selected teacher not found.')
        except NonTeachingStaff.DoesNotExist:
            messages.error(request, 'Selected staff member not found.')
        except Exception as e:
            messages.error(request, f'Error generating ID card: {str(e)}')

    teachers = Teacher.objects.all().order_by('full_name')
    non_teaching_staff = NonTeachingStaff.objects.all().order_by('full_name')
    context = {
        'teachers': teachers,
        'non_teaching_staff': non_teaching_staff,
        'is_admin': is_admin,
    }
    return render(request, 'generate_staff_id_card.html', context)


@login_required
def generate_principal_id_card(request):
    """Generate an ID card for the Principal - Admin only."""
    admin, principal, is_admin, actor_name = _get_id_card_actor(request)
    if is_admin is None:
        messages.error(request, 'Access denied. Admin or Principal only.')
        return redirect('unified_login')
    if not is_admin:
        messages.error(request, 'Only Admin can generate the Principal\'s ID card.')
        return redirect('id_card_hub')

    principals = Principal.objects.all().order_by('full_name')

    if request.method == 'POST':
        try:
            target_principal = Principal.objects.get(id=request.POST.get('principal_id'))
            photo = request.FILES.get('photo')

            card = IDCard.objects.create(
                holder_type='principal',
                principal=target_principal,
                full_name=target_principal.full_name,
                id_number=target_principal.principal_id,
                phone_number=request.POST.get('phone_number', '').strip(),
                role_title='Principal',
                photo=photo,
                generated_by_admin=admin,
            )

            messages.success(request, f'✅ ID Card generated for Principal {target_principal.full_name}!')
            return redirect('view_id_card', card_id=card.id)
        except Principal.DoesNotExist:
            messages.error(request, 'Principal not found.')
        except Exception as e:
            messages.error(request, f'Error generating ID card: {str(e)}')

    context = {'principals': principals}
    return render(request, 'generate_special_id_card.html', context)


@login_required
def generate_admin_id_card(request):
    """Admin (proprietor) generates their own ID card."""
    admin, principal, is_admin, actor_name = _get_id_card_actor(request)
    if is_admin is None:
        messages.error(request, 'Access denied. Admin or Principal only.')
        return redirect('unified_login')
    if not is_admin:
        messages.error(request, 'Only the Admin can generate their own card here.')
        return redirect('id_card_hub')

    if request.method == 'POST':
        try:
            photo = request.FILES.get('photo')

            card = IDCard.objects.create(
                holder_type='admin',
                admin=admin,
                full_name=admin.full_name,
                id_number=admin.admin_id,
                phone_number=request.POST.get('phone_number', '').strip(),
                role_title='Administrator / Proprietor',
                photo=photo,
                generated_by_admin=admin,
            )

            messages.success(request, '✅ Your ID Card has been generated!')
            return redirect('view_id_card', card_id=card.id)
        except Exception as e:
            messages.error(request, f'Error generating ID card: {str(e)}')

    context = {'admin_self': admin}
    return render(request, 'generate_special_id_card.html', context)


@login_required
def view_id_card(request, card_id):
    """View / print a single generated ID card."""
    admin, principal, is_admin, actor_name = _get_id_card_actor(request)
    if is_admin is None:
        messages.error(request, 'Access denied. Admin or Principal only.')
        return redirect('unified_login')

    card = get_object_or_404(IDCard, id=card_id)
    school = SchoolSettings.objects.first()

    context = {'card': card, 'school': school}
    return render(request, 'view_id_card.html', context)


@login_required
def id_card_print_sheet(request):
    """Print up to 4 selected ID cards on one A4 sheet (2 top, 2 bottom)."""
    admin, principal, is_admin, actor_name = _get_id_card_actor(request)
    if is_admin is None:
        messages.error(request, 'Access denied. Admin or Principal only.')
        return redirect('unified_login')

    ids_param = request.GET.get('ids', '')
    card_ids = [i for i in ids_param.split(',') if i.strip().isdigit()][:4]

    if not card_ids:
        messages.error(request, 'No cards selected to print.')
        return redirect('id_card_hub')

    # Preserve the order the user selected them in
    cards = list(IDCard.objects.filter(id__in=card_ids))
    cards.sort(key=lambda c: card_ids.index(str(c.id)))

    school = SchoolSettings.objects.first()
    context = {'cards': cards, 'school': school}
    return render(request, 'id_card_print_sheet.html', context)


@login_required
def delete_id_card(request, card_id):
    """Delete a generated ID card record (does not affect the underlying
    student/teacher/staff record it was generated from)."""
    admin, principal, is_admin, actor_name = _get_id_card_actor(request)
    if is_admin is None:
        messages.error(request, 'Access denied. Admin or Principal only.')
        return redirect('unified_login')

    if request.method == 'POST':
        try:
            card = IDCard.objects.get(id=card_id)
            name = card.full_name
            card.delete()
            messages.success(request, f'🗑️ ID Card for {name} deleted.')
        except IDCard.DoesNotExist:
            messages.error(request, 'ID Card not found.')

    return redirect('id_card_hub')