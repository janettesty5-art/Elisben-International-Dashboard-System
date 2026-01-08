from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('', views.unified_login, name='unified_login'),
    path('logout/', views.user_logout, name='logout'),
    
    # Admin URLs
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/register-student/', views.register_student, name='register_student'),
    path('admin/register-teacher/', views.register_teacher, name='register_teacher'),
    path('admin/move-to-alumni/<int:student_id>/', views.move_to_alumni, name='move_to_alumni'),
    path('admin/view-alumni/', views.view_alumni, name='view_alumni'),
    path('admin/delete-student/<int:student_id>/', views.delete_student, name='delete_student'),
    path('admin/delete-teacher/<int:teacher_id>/', views.delete_teacher, name='delete_teacher'),
    path('admin/finance/', views.manage_finance, name='manage_finance'),
    path('admin/delete-student-confirm/<int:student_id>/', views.delete_student_confirm, name='delete_student_confirm'),
    path('admin/delete-teacher-confirm/<int:teacher_id>/', views.delete_teacher_confirm, name='delete_teacher_confirm'),
    
    # Search functionality
    path('search-students/', views.search_students, name='search_students'),
    path('search-teachers/', views.search_teachers, name='search_teachers'),
    
    # Principal URLs
    path('principal/dashboard/', views.principal_dashboard, name='principal_dashboard'),
    
    # Bursar URLs
    path('bursar/dashboard/', views.bursar_dashboard, name='bursar_dashboard'),
    path('bursar/finance/', views.manage_finance, name='bursar_finance'),
    
    # Teacher URLs
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/create-exam/', views.create_exam, name='create_exam'),
    path('teacher/add-questions/<int:exam_id>/', views.add_questions, name='add_questions'),
    path('teacher/edit-question/<int:question_id>/', views.edit_question, name='edit_question'),
    path('teacher/delete-exam/<int:exam_id>/', views.delete_exam, name='delete_exam'),
    path('teacher/mark-attendance/', views.mark_attendance, name='mark_attendance'),
    path('teacher/view-attendance/', views.view_attendance, name='view_attendance'),
    path('teacher/exam/<int:exam_id>/delete-question/<int:question_number>/', views.delete_single_question, name='delete_single_question'),
    path('teacher/exam/<int:exam_id>/toggle-publish/', views.toggle_exam_publish, name='toggle_exam_publish'),
    path('teacher/export-results/<int:exam_id>/', views.export_results, name='export_results'),
    
    # Student URLs
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/profile/', views.student_profile, name='student_profile'),
    path('student/take-exam/<str:exam_id>/', views.take_exam, name='take_exam'),
    path('student/result/<int:submission_id>/', views.view_result, name='view_result'),
    
    # ========================================
    # RESULT SYSTEM URLs - PROPERLY INCLUDED
    # ========================================
    
    # Make Result Portal (Entry point)
    path('make-result/', views.make_result_portal, name='make_result_portal'),
    
    # Teacher Role Selection
    path('make-result/teacher-role-selection/', views.teacher_role_selection, name='teacher_role_selection'),
    
    # Subject Teacher Entry
    path('make-result/subject-teacher/', views.subject_teacher_entry, name='subject_teacher_entry'),
    
    # Class Teacher Collation
    path('make-result/class-teacher/', views.class_teacher_collate, name='class_teacher_collate'),
    path('make-result/class-teacher/edit/<int:result_id>/', views.class_teacher_edit_result, name='class_teacher_edit_result'),
    path('make-result/class-teacher/send/<int:result_id>/', views.send_result_to_principal, name='send_result_to_principal'),
    path('make-result/class-teacher/send-batch/', views.send_batch_to_principal, name='send_batch_to_principal'),
    # In the Result System URLs section, add this line:
    path('make-result/class-teacher/start/', views.class_teacher_start_result, name='class_teacher_start_result'),
    
    # Principal Result Review
    path('make-result/principal/', views.principal_result_review, name='principal_result_review'),
    path('make-result/principal/comment/<int:result_id>/', views.principal_add_comment, name='principal_add_comment'),
    path('make-result/principal/send/<int:result_id>/', views.send_result_to_admin, name='send_result_to_admin'),
    path('make-result/principal/send-batch/', views.send_batch_to_admin, name='send_batch_to_admin'),
    
    # Admin Result Management
    path('make-result/admin/', views.admin_result_management, name='admin_result_management'),
    path('make-result/admin/edit/<int:result_id>/', views.admin_edit_result, name='admin_edit_result'),
    path('make-result/admin/stamp/<int:result_id>/', views.admin_add_stamp, name='admin_add_stamp'),
    path('make-result/admin/publish/<int:result_id>/', views.admin_publish_result, name='admin_publish_result'),
    path('make-result/admin/publish-batch/', views.admin_publish_batch, name='admin_publish_batch'),
    path('make-result/admin/published/', views.admin_view_published, name='admin_view_published'),
    
    # Check Result Portal
    path('check-result/', views.check_result_portal, name='check_result_portal'),
    path('check-result/view/', views.view_student_result, name='view_student_result'),
    path('test-subject/', views.test_subject_teacher, name='test_subject'),
    
    # Result PDF/Print
    path('result/print/<int:result_id>/', views.print_result, name='print_result'),

    path('notification/mark-read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
    path('notification/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
     # ✅ ADD THIS NEW LINE:
    path('admin/edit-student/<int:student_id>/', views.edit_student, name='edit_student'),
]