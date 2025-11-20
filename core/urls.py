from django.urls import path
from . import views

urlpatterns = [
    # ---------------- Home / About / Contact ----------------
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),

    # ---------------- Student Registration & Login ----------------
    path('student_register/', views.student_register, name='student_register'),
    path('student_login/', views.student_login_view, name='student_login'),
    path('student_logout/', views.student_logout, name='student_logout'),

    # ---------------- Student Dashboard & Features ----------------
    path('student_dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/course/<int:course_id>/', views.course_detail, name='course_detail'),
    path('student/resources/', views.student_resources, name='student_resources'),
    path('student/assignments/', views.student_assignments, name='student_assignments'),
    path('student/progress/', views.view_my_progress, name='view_my_progress'),
    path('my_progress/', views.view_my_progress, name='my_progress'),

    # ---------------- Admin Login / Logout ----------------
    path('admin_login/', views.admin_login_view, name='admin_login'),
    path('admin_logout/', views.admin_logout, name='admin_logout'),

    # ---------------- Admin Dashboard & Sections ----------------
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('students/', views.admin_students, name='students'),
    path('progress/', views.student_progress, name='student_progress'),
    path('admin_settings/', views.admin_settings, name='admin_settings'),

    # ---------------- Admin Student Requests ----------------
    path('student_requests/', views.admin_student_requests, name='student_requests'),
    path('approve-student/<int:student_id>/', views.approve_student_request, name='approve_student'),
    path('delete_student_request/<int:req_id>/', views.delete_student_request, name='delete_student_request'),

    # ---------------- Admin Students Management ----------------
    path('edit_student/<int:student_id>/', views.edit_student, name='edit_student'),
    path('delete_student/<int:student_id>/', views.delete_student, name='delete_student'),

    # ---------------- Admin Courses Management ----------------
    path('admin_courses/', views.admin_courses, name='admin_courses'),
    path('add_course/', views.add_course, name='add_course'),
    path('edit_course_form/<int:course_id>/', views.edit_course_form, name='edit_course_form'),
    path('edit_course/<int:course_id>/', views.edit_course, name='edit_course'),
    path('delete_course/<int:course_id>/', views.delete_course, name='delete_course'),

    # ---------------- Admin Resources Management ----------------
    path('resources/', views.admin_resources, name='resources'),
    path('add_resource/', views.add_resource, name='add_resource'),
    path('edit_resource/<int:resource_id>/', views.edit_resource, name='edit_resource'),
    path('delete_resource/<int:resource_id>/', views.delete_resource, name='delete_resource'),

    # ---------------- Admin Progress Management ----------------
    path('add_progress/<int:student_id>/', views.add_progress, name='add_progress'),
    path('edit_progress/<int:progress_id>/', views.edit_progress, name='edit_progress'),
    path('delete_progress/<int:progress_id>/', views.delete_progress, name='delete_progress'),

    # ---------------- AI Chatbot ----------------
    path('ai-chatbot/', views.ai_chatbot, name='ai_chatbot'),

    # ---------------- Admin Notifications Management ----------------
    path('admin_notifications/', views.admin_notifications, name='admin_notifications'),
    path('add_notification/', views.add_notification, name='add_notification'),
    path('edit_notification/<int:notification_id>/', views.edit_notification, name='edit_notification'),
    path('delete_notification/<int:notification_id>/', views.delete_notification, name='delete_notification'),
    
    # Admin Assignment URLs
path('admin_assignments/', views.admin_assignments, name='admin_assignments'),
path('add_assignment/', views.add_assignment, name='add_assignment'),
path('edit_assignment/<int:assignment_id>/', views.edit_assignment, name='edit_assignment'),
path('delete_assignment/<int:assignment_id>/', views.delete_assignment, name='delete_assignment'),
path('assignment_submissions/<int:assignment_id>/', views.assignment_submissions, name='assignment_submissions'),

# Student Assignment URLs
path('submit_assignment/<int:assignment_id>/', views.submit_assignment, name='submit_assignment'),

# Admin Assignment URLs
path('admin_assignments/', views.admin_assignments, name='admin_assignments'),
path('add_assignment/', views.add_assignment, name='add_assignment'),
path('edit_assignment/<int:assignment_id>/', views.edit_assignment, name='edit_assignment'),
path('delete_assignment/<int:assignment_id>/', views.delete_assignment, name='delete_assignment'),
path('assignment_submissions/<int:assignment_id>/', views.assignment_submissions, name='assignment_submissions'),


path('course/<int:course_id>/lesson/<int:lesson_id>/', views.lesson_detail, name='lesson_detail'),

# Add these URLs
path('course/<int:course_id>/lesson/<int:lesson_id>/', views.lesson_detail, name='lesson_detail'),
path('course/<int:course_id>/lesson/<int:lesson_id>/complete/', views.mark_lesson_complete, name='mark_lesson_complete'),

# Admin Lesson URLs
path('admin_lessons/', views.admin_lessons, name='admin_lessons'),
path('add_lesson/', views.add_lesson, name='add_lesson'),
path('edit_lesson/<int:lesson_id>/', views.edit_lesson, name='edit_lesson'),
path('delete_lesson/<int:lesson_id>/', views.delete_lesson, name='delete_lesson'),

# Add these to your urlpatterns in core/urls.py

# Admin Discussion URLs
path('admin_discussions/', views.admin_discussions, name='admin_discussions'),
path('create_discussion_room/', views.create_discussion_room, name='create_discussion_room'),
path('admin_discussion_posts/<int:room_id>/', views.admin_discussion_posts, name='admin_discussion_posts'),
path('delete_discussion_post/<int:post_id>/', views.delete_discussion_post, name='delete_discussion_post'),

# Student Discussion URLs
path('student_discussions/', views.student_discussions, name='student_discussions'),
path('discussion_room/<int:room_id>/', views.discussion_room, name='discussion_room'),
]