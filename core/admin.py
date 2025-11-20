from django.contrib import admin
from .models import Course, StudentProfile, StudentRequest, Resource, Notification, Progress

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'age', 'mobile']
    list_filter = ['courses']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']

@admin.register(StudentRequest)
class StudentRequestAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'mobile', 'age', 'is_approved']
    list_filter = ['is_approved', 'courses']
    search_fields = ['username', 'first_name', 'last_name']

@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ['title', 'resource_type', 'subject', 'created_at']
    list_filter = ['resource_type', 'subject']
    search_fields = ['title', 'description']

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'message', 'created_at', 'is_read']
    list_filter = ['is_read', 'created_at']
    search_fields = ['user__username', 'message']

@admin.register(Progress)
class ProgressAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'percentage', 'last_activity']
    list_filter = ['course', 'last_activity']
    search_fields = ['student__user__username']

from .models import Lesson, StudentLessonProgress

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'order', 'duration', 'is_active']
    list_filter = ['course', 'is_active']
    search_fields = ['title', 'description']
    ordering = ['course', 'order']

@admin.register(StudentLessonProgress)
class StudentLessonProgressAdmin(admin.ModelAdmin):
    list_display = ['student', 'lesson', 'is_completed', 'completed_at']
    list_filter = ['is_completed', 'lesson__course']
    search_fields = ['student__user__username', 'lesson__title']