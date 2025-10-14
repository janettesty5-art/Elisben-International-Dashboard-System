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
    path('admin/delete-student/<int:student_id>/', views.delete_student, name='delete_student'),
    path('admin/delete-teacher/<int:teacher_id>/', views.delete_teacher, name='delete_teacher'),
    path('admin/finance/', views.manage_finance, name='manage_finance'),
    
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
    path('teacher/enter-grades/', views.enter_grades, name='enter_grades'),
    path('teacher/export-results/<int:exam_id>/', views.export_results, name='export_results'),
    
    # Student URLs
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/profile/', views.student_profile, name='student_profile'),
    path('student/take-exam/<str:exam_id>/', views.take_exam, name='take_exam'),
    path('student/result/<int:submission_id>/', views.view_result, name='view_result'),
]