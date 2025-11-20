from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Avg
from .models import Course, StudentRequest, StudentProfile, Resource, Notification, Progress
from .forms import ResourceForm, ProgressForm, ProgressUpdateForm
# views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.models import User

from .models import Course, StudentRequest, StudentProfile, Resource, Notification, Progress, Assignment, StudentAssignment, Lesson, StudentLessonProgress

from core.models import StudentRequest, StudentProfile, Course  # Correct import

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.utils import timezone
from django.utils import timezone
from datetime import timedelta

# ==================== PUBLIC PAGES ====================

def home(request):
    return render(request, 'home.html')

def about(request):
    return render(request, 'about.html')

def contact(request):
    return render(request, 'contact.html')

# ==================== STUDENT AUTHENTICATION ====================

def student_register(request):
    courses = Course.objects.all()
    
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        mobile = request.POST.get('mobile')
        age = request.POST.get('age')
        selected_courses_ids = request.POST.getlist('courses')
        
        # Validation
        if password != confirm_password:
            messages.error(request, "Passwords do not match!")
            return render(request, 'register/student_register.html', {'courses': courses})
        
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists!")
            return render(request, 'register/student_register.html', {'courses': courses})
        
        if StudentRequest.objects.filter(username=username).exists():
            messages.error(request, "Username already exists in pending requests!")
            return render(request, 'register/student_register.html', {'courses': courses})
        
        if not selected_courses_ids:
            messages.error(request, "Please select at least one course!")
            return render(request, 'register/student_register.html', {'courses': courses})
        
        try:
            # Create StudentRequest with hashed password
            student_request = StudentRequest.objects.create(
                first_name=first_name,
                last_name=last_name,
                username=username,
                email=email,
                mobile=mobile,
                age=age,
                is_approved=False
            )
            student_request.set_password(password)
            student_request.save()
            
            # Add selected courses
            selected_courses = Course.objects.filter(id__in=selected_courses_ids)
            student_request.courses.set(selected_courses)
            
            messages.success(request, "Registration submitted! Waiting for admin approval.")
            return redirect('student_login')
            
        except Exception as e:
            messages.error(request, f"Registration failed: {str(e)}")
            return render(request, 'register/student_register.html', {'courses': courses})
    
    return render(request, 'register/student_register.html', {'courses': courses})

def student_login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            # Check if student has a profile (is approved)
            try:
                student_profile = StudentProfile.objects.get(user=user)
                login(request, user)
                return redirect('student_dashboard')
            except StudentProfile.DoesNotExist:
                messages.error(request, "Your account is pending admin approval!")
        else:
            messages.error(request, "Invalid student credentials!")
    
    return render(request, 'login/student_login.html')

def student_logout(request):
    logout(request)
    messages.success(request, "Logged out successfully!")
    return redirect('home')

# ==================== ADMIN AUTHENTICATION ====================

def admin_login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None and (user.is_staff or user.is_superuser):
            login(request, user)
            return redirect('admin_dashboard')
        else:
            messages.error(request, "Invalid admin credentials!")
    
    return render(request, 'login/admin_login.html')

def admin_logout(request):
    logout(request)
    messages.success(request, "Admin logged out successfully!")
    return redirect('home')

# ==================== STUDENT DASHBOARD ====================
@login_required
def student_dashboard(request):
    try:
        student_profile = StudentProfile.objects.get(user=request.user)
        courses = student_profile.courses.all()
        
        # FIX: Use filter().first() to avoid MultipleObjectsReturned
        overall_progress = Progress.objects.filter(
            student=student_profile,
            course__isnull=True
        ).order_by('-last_activity').first()  # Get the most recent one
        
        # If no overall progress exists, create one
        if not overall_progress:
            overall_progress = Progress.objects.create(
                student=student_profile,
                percentage=0,
                total_lessons=10
            )
        
        # Calculate completed courses properly
        completed_courses = 0
        for course in courses:
            # FIX: Use filter().first() here too
            course_progress = Progress.objects.filter(
                student=student_profile,
                course=course
            ).first()
            if course_progress and course_progress.percentage >= 100:
                completed_courses += 1
        
        context = {
            'student': student_profile,
            'courses': courses,
            'progress': overall_progress,
            'completed_courses': completed_courses,
        }
        return render(request, 'student/dashboard.html', context)
    
    except StudentProfile.DoesNotExist:
        messages.error(request, "Student profile not found!")
        return redirect('student_login')
# ==================== ADMIN DASHBOARD ====================

@login_required
def admin_dashboard(request):
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "Access denied!")
        return redirect('home')
    
    pending_requests_count = StudentRequest.objects.filter(is_approved=False).count()
    total_students = StudentProfile.objects.count()
    total_courses = Course.objects.count()
    total_resources = Resource.objects.count()
    
    # Calculate average progress
    all_progress = Progress.objects.all()
    if all_progress.exists():
        avg_progress = round(all_progress.aggregate(Avg('percentage'))['percentage__avg'], 1)
    else:
        avg_progress = 0
    
    # Get recent progress for activity
    recent_progress = Progress.objects.select_related('student__user', 'course').order_by('-last_activity')[:5]
    
    context = {
        'pending_requests': pending_requests_count,
        'total_students': total_students,
        'total_courses': total_courses,
        'total_resources': total_resources,
        'avg_progress': avg_progress,
        'active_courses': total_courses,  # Assuming all courses are active
        'completed_progress': Progress.objects.filter(percentage=100).count(),
        'recent_progress': recent_progress,
    }
    return render(request, 'admin_panel/admin_dashboard.html', context)

# ==================== ADMIN STUDENT REQUESTS ====================

@login_required
def admin_student_requests(request):
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "Access denied!")
        return redirect('home')
    
    pending_requests = StudentRequest.objects.filter(is_approved=False)
    approved_students = StudentProfile.objects.count()
    total_courses = Course.objects.count()
    
    context = {
        'pending_requests': pending_requests,
        'approved_students': approved_students,
        'total_courses': total_courses,
    }
    return render(request, 'admin_panel/student_requests.html', context)

@login_required
def approve_student_request(request, req_id):
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "Access denied!")
        return redirect('home')
    
    if request.method == 'POST':
        try:
            student_request = StudentRequest.objects.get(id=req_id)
            
            # Create User - Use a temporary password first, then set the actual hashed password
            # We need to use a default password and then update it with the correct hash
            temp_password = "temp_password_123"  # Temporary password
            
            user = User.objects.create_user(
                username=student_request.username,
                email=student_request.email,
                password=temp_password,  # Use temporary password
                first_name=student_request.first_name,
                last_name=student_request.last_name
            )
            
            # Now set the actual password hash from StudentRequest
            user.password = student_request.password
            user.save()
            
            # Create StudentProfile
            student_profile = StudentProfile.objects.create(
                user=user,
                age=student_request.age,
                mobile=student_request.mobile
            )
            
            # Add courses
            student_profile.courses.set(student_request.courses.all())
            
            # Create initial progress
            Progress.objects.create(student=student_profile, percentage=0)
            
            # Mark as approved
            student_request.is_approved = True
            student_request.save()
            
            messages.success(request, f"Student {user.username} approved successfully!")
            
        except Exception as e:
            messages.error(request, f"Error approving student: {str(e)}")
    
    return redirect('student_requests')

@login_required
def delete_student_request(request, req_id):
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "Access denied!")
        return redirect('home')
    
    if request.method == 'POST':
        try:
            student_request = StudentRequest.objects.get(id=req_id)
            student_request.delete()
            messages.success(request, "Student request deleted successfully!")
        except Exception as e:
            messages.error(request, f"Error deleting student request: {str(e)}")
    
    return redirect('student_requests')

# ==================== ADMIN STUDENTS MANAGEMENT ====================
@login_required
def admin_students(request):
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "Access denied!")
        return redirect('home')
    
    students = StudentProfile.objects.all()
    pending_requests_count = StudentRequest.objects.filter(is_approved=False).count()
    total_courses = Course.objects.count()
    
    # Calculate average progress - FIXED: Use filter().first() instead of get()
    total_progress = 0
    student_count = students.count()
    
    for student in students:
        # FIX: Use filter().first() to avoid MultipleObjectsReturned
        progress = Progress.objects.filter(
            student=student,
            course__isnull=True  # Get only overall progress
        ).first()  # This returns first object or None
        
        if progress:
            total_progress += progress.percentage
        else:
            # If no progress exists, use 0
            total_progress += 0
    
    average_progress = round(total_progress / student_count, 1) if student_count > 0 else 0
    
    context = {
        'students': students,
        'pending_requests_count': pending_requests_count,
        'total_courses': total_courses,
        'average_progress': average_progress,
    }
    return render(request, 'admin_panel/students.html', context)

@login_required
def edit_student(request, student_id):
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "Access denied!")
        return redirect('home')
    
    student_profile = get_object_or_404(StudentProfile, id=student_id)
    
    if request.method == 'POST':
        try:
            user = student_profile.user
            user.first_name = request.POST.get('first_name')
            user.last_name = request.POST.get('last_name')
            user.email = request.POST.get('email')
            user.save()
            
            student_profile.age = request.POST.get('age')
            student_profile.mobile = request.POST.get('mobile')
            student_profile.save()
            
            # Update courses
            selected_courses_ids = request.POST.getlist('courses')
            selected_courses = Course.objects.filter(id__in=selected_courses_ids)
            student_profile.courses.set(selected_courses)
            
            messages.success(request, "Student updated successfully!")
            return redirect('students')
            
        except Exception as e:
            messages.error(request, f"Error updating student: {str(e)}")
    
    courses = Course.objects.all()
    return render(request, 'admin_panel/edit_student.html', {
        'student': student_profile,
        'courses': courses
    })

@login_required
def delete_student(request, student_id):
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "Access denied!")
        return redirect('home')
    
    if request.method == 'POST':
        try:
            student_profile = get_object_or_404(StudentProfile, id=student_id)
            user = student_profile.user
            student_profile.delete()
            user.delete()
            messages.success(request, "Student deleted successfully!")
        except Exception as e:
            messages.error(request, f"Error deleting student: {str(e)}")
    
    return redirect('students')

# ==================== ADMIN COURSES MANAGEMENT ====================

@login_required
def admin_courses(request):
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "Access denied!")
        return redirect('home')
    
    courses = Course.objects.all()
    
    context = {
        'courses': courses,
        'total_students': StudentProfile.objects.count(),
        'active_courses': courses.count(),
    }
    return render(request, 'admin_panel/courses.html', context)

@login_required
def edit_course(request, course_id):
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "Access denied!")
        return redirect('home')
    
    course = get_object_or_404(Course, id=course_id)
    
    if request.method == 'POST':
        try:
            course.name = request.POST.get('name')
            course.description = request.POST.get('description')
            course.save()
            messages.success(request, "Course updated successfully!")
            return redirect('admin_courses')
        except Exception as e:
            messages.error(request, f"Error updating course: {str(e)}")
    
    return render(request, 'admin_panel/edit_course.html', {'course': course})

@login_required
def delete_course(request, course_id):
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "Access denied!")
        return redirect('home')
    
    if request.method == 'POST':
        try:
            course = get_object_or_404(Course, id=course_id)
            course.delete()
            messages.success(request, "Course deleted successfully!")
        except Exception as e:
            messages.error(request, f"Error deleting course: {str(e)}")
    
    return redirect('admin_courses')

# ==================== ADMIN RESOURCES MANAGEMENT ====================

@login_required
def admin_resources(request):
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "Access denied!")
        return redirect('home')
    
    resources = Resource.objects.all().order_by('-created_at')
    
    # Count resource types
    pdf_count = resources.filter(resource_type='pdf').count()
    youtube_count = resources.filter(resource_type='youtube').count()
    link_count = resources.filter(resource_type='link').count()
    video_count = resources.filter(resource_type='video').count()
    
    context = {
        'resources': resources,
        'pdf_count': pdf_count,
        'youtube_count': youtube_count,
        'link_count': link_count,
        'video_count': video_count,
        'total_resources': resources.count(),
    }
    return render(request, 'admin_panel/resources.html', context)

@login_required
def add_resource(request):
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "Access denied!")
        return redirect('home')
    
    if request.method == 'POST':
        form = ResourceForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                resource = form.save(commit=False)
                resource.created_by = request.user
                resource.save()
                messages.success(request, 'Resource added successfully!')
                return redirect('resources')
            except Exception as e:
                messages.error(request, f"Error adding resource: {str(e)}")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ResourceForm()
    
    return render(request, 'admin_panel/add_resource.html', {'form': form})

@login_required
def edit_resource(request, resource_id):
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "Access denied!")
        return redirect('home')
    
    resource = get_object_or_404(Resource, id=resource_id)
    
    if request.method == 'POST':
        form = ResourceForm(request.POST, request.FILES, instance=resource)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Resource updated successfully!")
                return redirect('resources')
            except Exception as e:
                messages.error(request, f"Error updating resource: {str(e)}")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ResourceForm(instance=resource)
    
    return render(request, 'admin_panel/edit_resource.html', {
        'form': form,
        'resource': resource
    })

@login_required
def delete_resource(request, resource_id):
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "Access denied!")
        return redirect('home')
    
    if request.method == 'POST':
        try:
            resource = get_object_or_404(Resource, id=resource_id)
            resource.delete()
            messages.success(request, "Resource deleted successfully!")
        except Exception as e:
            messages.error(request, f"Error deleting resource: {str(e)}")
    
    return redirect('resources')

# ==================== STUDENT RESOURCES VIEW ====================

@login_required
def student_resources(request):
    try:
        student_profile = StudentProfile.objects.get(user=request.user)
        resources = Resource.objects.all().order_by('-created_at')
        
        context = {
            'resources': resources,
            'student': student_profile,
        }
        return render(request, 'student/resources.html', context)
    
    except StudentProfile.DoesNotExist:
        messages.error(request, "Student profile not found!")
        return redirect('student_login')

# ==================== ADMIN NOTIFICATIONS MANAGEMENT ====================

@login_required
def admin_notifications(request):
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "Access denied!")
        return redirect('home')
    
    notifications = Notification.objects.all().order_by('-created_at')
    return render(request, 'admin_panel/notifications.html', {'notifications': notifications})

@login_required
def add_notification(request):
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "Access denied!")
        return redirect('home')
    
    if request.method == 'POST':
        try:
            user_id = request.POST.get('user')
            message = request.POST.get('message')
            
            if user_id == 'all':
                # Send to all users
                users = User.objects.all()
                for user in users:
                    Notification.objects.create(user=user, message=message)
            else:
                user = get_object_or_404(User, id=user_id)
                Notification.objects.create(user=user, message=message)
            
            messages.success(request, "Notification sent successfully!")
            return redirect('admin_notifications')
        except Exception as e:
            messages.error(request, f"Error sending notification: {str(e)}")
    
    users = User.objects.all()
    return render(request, 'admin_panel/add_notification.html', {'users': users})

@login_required
def edit_notification(request, notification_id):
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "Access denied!")
        return redirect('home')
    
    notification = get_object_or_404(Notification, id=notification_id)
    
    if request.method == 'POST':
        try:
            notification.message = request.POST.get('message')
            notification.save()
            messages.success(request, "Notification updated successfully!")
            return redirect('admin_notifications')
        except Exception as e:
            messages.error(request, f"Error updating notification: {str(e)}")
    
    return render(request, 'admin_panel/edit_notification.html', {'notification': notification})

@login_required
def delete_notification(request, notification_id):
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "Access denied!")
        return redirect('home')
    
    if request.method == 'POST':
        try:
            notification = get_object_or_404(Notification, id=notification_id)
            notification.delete()
            messages.success(request, "Notification deleted successfully!")
        except Exception as e:
            messages.error(request, f"Error deleting notification: {str(e)}")
    
    return redirect('admin_notifications')

# ==================== ADMIN PROGRESS MANAGEMENT ====================
# ==================== ADMIN PROGRESS MANAGEMENT ====================

@login_required
def student_progress(request):
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "Access denied!")
        return redirect('home')
    
    # Get all students with their progress
    students = StudentProfile.objects.all()
    
    # Get filter parameters
    course_filter = request.GET.get('course', '')
    progress_filter = request.GET.get('progress', '')
    
    progress_data = []
    
    for student in students:
        # Get overall progress
        overall_progress, created = Progress.objects.get_or_create(
            student=student,
            course=None,
            defaults={'percentage': 0, 'total_lessons': 0}
        )
        
        # Get course-specific progress
        course_progress = []
        for course in student.courses.all():
            course_prog, created = Progress.objects.get_or_create(
                student=student,
                course=course,
                defaults={'percentage': 0, 'total_lessons': 0}
            )
            course_progress.append(course_prog)
        
        # Apply course filter
        if course_filter:
            course_progress = [p for p in course_progress if str(p.course.id) == course_filter]
        
        progress_data.append({
            'student': student,
            'overall_progress': overall_progress,
            'course_progress': course_progress,
        })
    
    # Apply progress percentage filter
    if progress_filter:
        if progress_filter == 'high':
            progress_data = [p for p in progress_data if p['overall_progress'].percentage >= 80]
        elif progress_filter == 'medium':
            progress_data = [p for p in progress_data if 50 <= p['overall_progress'].percentage < 80]
        elif progress_filter == 'low':
            progress_data = [p for p in progress_data if p['overall_progress'].percentage < 50]
    
    courses = Course.objects.all()
    
    return render(request, 'admin_panel/progress.html', {
        'progress_data': progress_data,
        'courses': courses,
        'selected_course': course_filter,
        'selected_progress': progress_filter,
    })

@login_required
def add_progress(request, student_id):
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "Access denied!")
        return redirect('home')
    
    student = get_object_or_404(StudentProfile, id=student_id)
    
    if request.method == 'POST':
        form = ProgressForm(request.POST)
        if form.is_valid():
            try:
                progress = form.save(commit=False)
                progress.student = student
                
                # Auto-calculate percentage if not provided
                if not progress.percentage and progress.total_lessons > 0:
                    progress.percentage = min(100, int((progress.completed_lessons / progress.total_lessons) * 100))
                
                progress.save()
                messages.success(request, f"Progress added for {student.user.username}!")
                return redirect('student_progress')
            except Exception as e:
                messages.error(request, f"Error adding progress: {str(e)}")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ProgressForm()
    
    return render(request, 'admin_panel/add_progress.html', {
        'form': form,
        'student': student
    })

@login_required
def edit_progress(request, progress_id):
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "Access denied!")
        return redirect('home')
    
    progress = get_object_or_404(Progress, id=progress_id)
    
    if request.method == 'POST':
        form = ProgressUpdateForm(request.POST, instance=progress)
        if form.is_valid():
            try:
                progress = form.save(commit=False)
                
                # Auto-update percentage based on completed lessons
                if progress.total_lessons > 0:
                    progress.percentage = min(100, int((progress.completed_lessons / progress.total_lessons) * 100))
                
                progress.save()
                messages.success(request, "Progress updated successfully!")
                return redirect('student_progress')
            except Exception as e:
                messages.error(request, f"Error updating progress: {str(e)}")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ProgressUpdateForm(instance=progress)
    
    return render(request, 'admin_panel/edit_progress.html', {
        'form': form,
        'progress': progress
    })

@login_required
def delete_progress(request, progress_id):
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "Access denied!")
        return redirect('home')
    
    if request.method == 'POST':
        try:
            progress = get_object_or_404(Progress, id=progress_id)
            student_name = progress.student.user.username
            progress.delete()
            messages.success(request, f"Progress record for {student_name} deleted successfully!")
        except Exception as e:
            messages.error(request, f"Error deleting progress: {str(e)}")
    
    return redirect('student_progress')
    # ==================== STUDENT PROGRESS VIEW ====================
@login_required
def view_my_progress(request):
    try:
        student_profile = StudentProfile.objects.get(user=request.user)
        
        # Get overall progress
        overall_progress, created = Progress.objects.get_or_create(
            student=student_profile,
            course=None,
            defaults={'percentage': 0, 'total_lessons': 10}
        )
        
        # Get course-specific progress
        course_progress = Progress.objects.filter(student=student_profile).exclude(course=None)
        
        # Calculate statistics
        total_courses = student_profile.courses.count()
        completed_courses = course_progress.filter(percentage=100).count()
        average_progress = course_progress.aggregate(avg=Avg('percentage'))['avg'] or 0
        
        # Get real recent activities
        recent_activities = []
        
        # 1. Get recently completed lessons
        recent_lessons = StudentLessonProgress.objects.filter(
            student=student_profile,
            is_completed=True
        ).select_related('lesson', 'lesson__course').order_by('-completed_at')[:5]
        
        for lesson_progress in recent_lessons:
            if lesson_progress.completed_at:  # Check if completed_at is not None
                recent_activities.append({
                    'title': f'Completed {lesson_progress.lesson.course.name}',
                    'description': f'Finished "{lesson_progress.lesson.title}" lesson',
                    'timestamp': lesson_progress.completed_at
                })
        
        # 2. Get recent quiz attempts (if StudentQuizAttempt exists)
        try:
            recent_quizzes = StudentQuizAttempt.objects.filter(
                student=student_profile
            ).select_related('quiz', 'quiz__course').order_by('-attempted_at')[:3]
            
            for quiz_attempt in recent_quizzes:
                status = "Passed" if quiz_attempt.passed else "Attempted"
                recent_activities.append({
                    'title': f'{status} {quiz_attempt.quiz.course.name} Quiz',
                    'description': f'Scored {quiz_attempt.score}% on "{quiz_attempt.quiz.title}"',
                    'timestamp': quiz_attempt.attempted_at
                })
        except NameError:
            # StudentQuizAttempt model doesn't exist, skip this part
            pass
        
        # 3. Get recent assignment submissions
        recent_assignments = StudentAssignment.objects.filter(
            student=student_profile,
            submitted_at__isnull=False
        ).select_related('assignment', 'assignment__course').order_by('-submitted_at')[:3]
        
        for assignment in recent_assignments:
            recent_activities.append({
                'title': f'Submitted {assignment.assignment.course.name} Assignment',
                'description': f'Submitted "{assignment.assignment.title}"',
                'timestamp': assignment.submitted_at
            })
        
        # Sort activities by timestamp (newest first) and take top 5
        recent_activities.sort(key=lambda x: x['timestamp'], reverse=True)
        recent_activities = recent_activities[:5]
        
        # Calculate learning streak (simplified version)
        today = timezone.now().date()
        streak = 0
        
        # Check last 7 days for any activity
        for i in range(7):
            check_date = today - timedelta(days=i)
            has_activity = False
            
            # Check lesson completions
            if StudentLessonProgress.objects.filter(
                student=student_profile,
                completed_at__date=check_date
            ).exists():
                has_activity = True
            
            # Check assignment submissions
            elif StudentAssignment.objects.filter(
                student=student_profile,
                submitted_at__date=check_date
            ).exists():
                has_activity = True
            
            # Check quiz attempts (if model exists)
            try:
                if StudentQuizAttempt.objects.filter(
                    student=student_profile,
                    attempted_at__date=check_date
                ).exists():
                    has_activity = True
            except NameError:
                pass
            
            if has_activity:
                streak += 1
            else:
                break
        
        context = {
            'student': student_profile,
            'overall_progress': overall_progress,
            'course_progress': course_progress,
            'total_courses': total_courses,
            'completed_courses': completed_courses,
            'average_progress': round(average_progress, 1),
            'recent_activities': recent_activities,
            'learning_streak': streak,
        }
        return render(request, 'student/my_progress.html', context)
    
    except StudentProfile.DoesNotExist:
        messages.error(request, "Student profile not found!")
        return redirect('student_login')        
# ==================== ADMIN SETTINGS ====================

@login_required
def admin_settings(request):
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "Access denied!")
        return redirect('home')
    
    total_students = StudentProfile.objects.count()
    total_courses = Course.objects.count()
    total_resources = Resource.objects.count()
    pending_requests = StudentRequest.objects.filter(is_approved=False).count()
    
    context = {
        'total_students': total_students,
        'total_courses': total_courses,
        'total_resources': total_resources,
        'pending_requests': pending_requests,
    }
    return render(request, 'admin_panel/settings.html', context)

# ==================== ADD COURSE FUNCTION ====================

@login_required
def add_course(request):
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "Access denied!")
        return redirect('home')
    
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            description = request.POST.get('description')
            
            # Create new course
            course = Course.objects.create(
                name=name,
                description=description
            )
            
            messages.success(request, f"Course '{name}' added successfully!")
            return redirect('admin_courses')
            
        except Exception as e:
            messages.error(request, f"Error adding course: {str(e)}")
    
    return render(request, 'admin_panel/add_course.html')

@login_required
def edit_course_form(request, course_id):
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "Access denied!")
        return redirect('home')
    
    course = get_object_or_404(Course, id=course_id)
    
    if request.method == 'POST':
        try:
            course.name = request.POST.get('name')
            course.description = request.POST.get('description')
            course.save()
            messages.success(request, "Course updated successfully!")
            return redirect('admin_courses')
        except Exception as e:
            messages.error(request, f"Error updating course: {str(e)}")
    
    return render(request, 'admin_panel/edit_course_form.html', {'course': course})

# ==================== REMOVED DUPLICATE FUNCTIONS ====================

def student_requests(request):
    """View to display pending student requests"""
    try:
        pending_requests = StudentRequest.objects.filter(is_approved=False)
        approved_students = User.objects.filter(studentprofile__isnull=False).count()
        total_courses = Course.objects.count()
        
        context = {
            'pending_requests': pending_requests,
            'approved_students': approved_students,
            'total_courses': total_courses,
        }
        return render(request, 'admin_panel/student_requests.html', context)
    except Exception as e:
        messages.error(request, f'Error loading student requests: {str(e)}')
        return render(request, 'admin_panel/student_requests.html', {
            'pending_requests': [],
            'approved_students': 0,
            'total_courses': 0,
        })

@login_required
def approve_student_request(request, student_id):
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "Access denied!")
        return redirect('home')
    
    try:
        student_request = get_object_or_404(StudentRequest, id=student_id, is_approved=False)
        
        # Check if user already exists
        if User.objects.filter(username=student_request.username).exists():
            messages.error(request, f'Username {student_request.username} already exists!')
            return redirect('student_requests')  # CHANGE HERE
        
        # Create User with the ORIGINAL plain password
        user = User.objects.create_user(
            username=student_request.username,
            email=student_request.email,
            password=student_request.password_plain,
            first_name=student_request.first_name,
            last_name=student_request.last_name
        )
        
        # Create StudentProfile
        student_profile = StudentProfile.objects.create(
            user=user,
            age=student_request.age,
            mobile=student_request.mobile
        )
        
        # Add courses
        student_profile.courses.set(student_request.courses.all())
        
        # Create initial progress
        Progress.objects.create(student=student_profile, percentage=0)
        
        # Mark request as approved
        student_request.is_approved = True
        student_request.save()
        
        messages.success(request, f"Student {user.username} approved successfully!")
        
    except Exception as e:
        messages.error(request, f"Error approving student: {str(e)}")
    
    return redirect('student_requests')  # CHANGE HERE

@login_required
def delete_student_request(request, student_id):
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "Access denied!")
        return redirect('home')
    
    try:
        student_request = get_object_or_404(StudentRequest, id=student_id)
        student_request.delete()
        messages.success(request, "Student request deleted successfully!")
    except Exception as e:
        messages.error(request, f"Error deleting student request: {str(e)}")
    
    return redirect('student_requests')  # CHANGE HERE

@login_required
def mark_lesson_complete(request, lesson_id):
    try:
        student_profile = StudentProfile.objects.get(user=request.user)
        lesson = Lesson.objects.get(id=lesson_id)
        
        # Mark lesson as completed
        progress, created = StudentLessonProgress.objects.get_or_create(
            student=student_profile,
            lesson=lesson,
            defaults={'is_completed': True, 'completed_at': timezone.now()}
        )
        
        if not created:
            progress.is_completed = True
            progress.completed_at = timezone.now()
            progress.save()
        
        # Update overall progress
        overall_progress = Progress.objects.filter(
            student=student_profile,
            course__isnull=True
        ).first()
        if overall_progress:
            overall_progress.calculate_real_progress()
        
        messages.success(request, f"Lesson '{lesson.title}' marked as completed!")
        
    except (StudentProfile.DoesNotExist, Lesson.DoesNotExist):
        messages.error(request, "Lesson not found!")
    
    return redirect('student_dashboard')

@csrf_exempt
def ai_chatbot(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '').lower()
            
            # Get student info for personalized responses
            student_courses = []
            if hasattr(request.user, 'studentprofile'):
                student_profile = request.user.studentprofile
                student_courses = [course.name.lower() for course in student_profile.courses.all()]
            
            # Enhanced AI responses with better keyword matching
            if any(word in user_message for word in ['hello', 'hi', 'hey', 'hola']):
                response = "Hello! 👋 How can I assist with your learning journey today?"
            
            elif any(word in user_message for word in ['progress', 'how am i doing', 'my progress']):
                response = "📊 Your progress is looking great! Based on your current pace, you're on track to complete your courses ahead of schedule. Keep up the excellent work! 🚀"
            
            elif any(word in user_message for word in ['python', 'python advanced', 'advanced python']):
                response = "🐍 **Python Advanced Topics:**\n• Decorators and generators\n• Context managers\n• Metaclasses\n• Concurrency (async/await)\n• Advanced OOP patterns\n\nWant specific examples or practice exercises?"
            
            elif any(word in user_message for word in ['web', 'web development', 'html', 'css']):
                response = "🌐 **Web Development Focus Areas:**\n• Responsive design with CSS Grid/Flexbox\n• JavaScript ES6+ features\n• React/Vue.js frameworks\n• REST APIs\n• Deployment strategies\n\nWhich area interests you most?"
            
            elif any(word in user_message for word in ['database', 'sql', 'mongodb']):
                response = "🗄️ **Database Concepts:**\n• SQL queries and optimization\n• Database normalization\n• Indexing strategies\n• NoSQL vs SQL\n• ACID properties\n\nNeed help with specific database problems?"
            
            elif any(word in user_message for word in ['help', 'what can you do']):
                response = "🆘 **I can help with:**\n• Course explanations\n• Study techniques\n• Project ideas\n• Code debugging\n• Learning roadmap\n• Motivation tips\n\nWhat specific help do you need?"
            
            elif any(word in user_message for word in ['study', 'how to study', 'learning tips']):
                response = "📖 **Effective Study Techniques:**\n• Pomodoro (25min study + 5min break)\n• Active recall practice\n• Spaced repetition\n• Teach what you learn\n• Build projects\n\nTry the Pomodoro technique today! ⏰"
            
            elif any(word in user_message for word in ['project', 'project ideas']):
                response = "💡 **Project Ideas:**\n• Personal portfolio website\n• Todo app with database\n• Weather app with API\n• Blog with user authentication\n• E-commerce site\n\nWhich project excites you?"
            
            elif any(word in user_message for word in ['thank', 'thanks']):
                response = "You're welcome! 😊 Remember: Consistent practice beats talent when talent doesn't practice. Keep coding! 💪"
            
            elif any(word in user_message for word in ['motivation', 'stuck', 'frustrated']):
                response = "💪 **Motivation Boost:**\nEvery expert was once a beginner. Your struggles today are building your expertise tomorrow. Take a break, then try again! 🌟"
            
            elif any(word in user_message for word in ['deadline', 'due', 'assignment']):
                response = "⏰ **Deadline Strategy:**\n1. Break task into smaller parts\n2. Set mini-deadlines\n3. Focus on one thing at a time\n4. Ask for help if stuck\n5. Review and submit early\n\nYou've got this! 🚀"
            
            else:
                # Check if message contains any course names
                course_keywords = ['python', 'web', 'database', 'javascript', 'html', 'css', 'react']
                found_course = None
                for keyword in course_keywords:
                    if keyword in user_message:
                        found_course = keyword
                        break
                
                if found_course:
                    if found_course == 'python':
                        response = f"🐍 Great question about Python! I recommend focusing on: functions, classes, error handling, and working with APIs. Want me to explain any specific Python concept?"
                    elif found_course == 'web':
                        response = f"🌐 Web development question! Key areas: HTML structure, CSS styling, JavaScript interactivity. Need help with frontend or backend?"
                    elif found_course == 'database':
                        response = f"🗄️ Database topic! Important concepts: SQL queries, relationships, normalization. Working with MySQL or MongoDB?"
                    else:
                        response = f"Interesting question about {found_course}! I'd love to help you with that. Could you be more specific about what you're trying to learn or build?"
                else:
                    response = "🤔 That's an interesting question! I'm here to help with your learning journey. Could you rephrase or ask about:\n• Specific courses\n• Study techniques\n• Project guidance\n• Code problems\n\nWhat would you like to explore?"
            
            return JsonResponse({'response': response})
            
        except Exception as e:
            return JsonResponse({'response': 'Sorry, I encountered an error. Please try again with a different question.'})
    
    return JsonResponse({'response': 'Please send a POST request with your message.'})

@login_required
def course_detail(request, course_id):
    try:
        course = get_object_or_404(Course, id=course_id)
        student_profile = StudentProfile.objects.get(user=request.user)
        
        # Check if student is enrolled
        if not student_profile.courses.filter(id=course_id).exists():
            messages.error(request, "You are not enrolled in this course!")
            return redirect('student_dashboard')
        
        # Get or create course progress
        progress = Progress.objects.filter(
            student=student_profile,
            course=course
        ).first()
        
        if not progress:
            progress = Progress.objects.create(
                student=student_profile,
                course=course,
                percentage=0,
                total_lessons=0
            )
        
        # Get real lessons from database
        lessons = Lesson.objects.filter(course=course, is_active=True).order_by('order')
        
        # Update total lessons in progress
        if progress.total_lessons != lessons.count():
            progress.total_lessons = lessons.count()
            progress.save()
        
        # Get student progress for each lesson
        lesson_data = []
        completed_lessons = 0
        
        for lesson in lessons:
            lesson_progress = StudentLessonProgress.objects.filter(
                student=student_profile,
                lesson=lesson
            ).first()
            
            is_completed = lesson_progress.is_completed if lesson_progress else False
            if is_completed:
                completed_lessons += 1
            
            lesson_data.append({
                'id': lesson.id,
                'title': lesson.title,
                'description': lesson.description,
                'duration': lesson.duration,
                'completed': is_completed,
                'content': lesson.content
            })
        
        # Update progress percentage
        if lessons.count() > 0:
            new_percentage = int((completed_lessons / lessons.count()) * 100)
            if progress.percentage != new_percentage:
                progress.percentage = new_percentage
                progress.save()
        
        context = {
            'course': course,
            'progress': progress,
            'lessons': lesson_data,
            'student': student_profile,
        }
        return render(request, 'student/course_detail.html', context)
        
    except StudentProfile.DoesNotExist:
        messages.error(request, "Student profile not found!")
        return redirect('student_login')@login_required
def student_resources(request):
    try:
        student_profile = StudentProfile.objects.get(user=request.user)
        resources = Resource.objects.all()
        
        context = {
            'student': student_profile,
            'resources': resources,
        }
        return render(request, 'student/resources.html', context)
    except StudentProfile.DoesNotExist:
        return redirect('student_login')

@login_required
def student_assignments(request):
    try:
        student_profile = StudentProfile.objects.get(user=request.user)
        context = {'student': student_profile}
        return render(request, 'student/assignments.html', context)
    except StudentProfile.DoesNotExist:
        return redirect('student_login')
    
@login_required
def student_resources(request):
    try:
        student_profile = StudentProfile.objects.get(user=request.user)
        resources = Resource.objects.all().order_by('-created_at')
        
        context = {
            'student': student_profile,
            'resources': resources,
        }
        return render(request, 'student/resources.html', context)
    
    except StudentProfile.DoesNotExist:
        messages.error(request, "Student profile not found!")
        return redirect('student_login')
# ==================== ADMIN ASSIGNMENTS MANAGEMENT ====================

@login_required
def admin_assignments(request):
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "Access denied!")
        return redirect('home')
    
    assignments = Assignment.objects.all().order_by('-created_at')
    
    # Count assignments by type
    project_count = assignments.filter(assignment_type='project').count()
    quiz_count = assignments.filter(assignment_type='quiz').count()
    homework_count = assignments.filter(assignment_type='homework').count()
    exam_count = assignments.filter(assignment_type='exam').count()
    
    # Count overdue assignments
    overdue_count = sum(1 for assignment in assignments if assignment.is_overdue())
    
    context = {
        'assignments': assignments,
        'project_count': project_count,
        'quiz_count': quiz_count,
        'homework_count': homework_count,
        'exam_count': exam_count,
        'overdue_count': overdue_count,
        'total_assignments': assignments.count(),
    }
    return render(request, 'admin_panel/assignments.html', context)

@login_required
def add_assignment(request):
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "Access denied!")
        return redirect('home')
    
    if request.method == 'POST':
        form = AssignmentForm(request.POST)
        if form.is_valid():
            try:
                assignment = form.save(commit=False)
                assignment.created_by = request.user
                assignment.save()
                
                # Create StudentAssignment entries for all students in the course
                students = StudentProfile.objects.filter(courses=assignment.course)
                for student in students:
                    StudentAssignment.objects.create(
                        student=student,
                        assignment=assignment
                    )
                
                messages.success(request, 'Assignment created successfully!')
                return redirect('admin_assignments')
            except Exception as e:
                messages.error(request, f"Error creating assignment: {str(e)}")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = AssignmentForm()
    
    return render(request, 'admin_panel/add_assignment.html', {'form': form})

@login_required
def edit_assignment(request, assignment_id):
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "Access denied!")
        return redirect('home')
    
    assignment = get_object_or_404(Assignment, id=assignment_id)
    
    if request.method == 'POST':
        form = AssignmentForm(request.POST, instance=assignment)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Assignment updated successfully!")
                return redirect('admin_assignments')
            except Exception as e:
                messages.error(request, f"Error updating assignment: {str(e)}")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = AssignmentForm(instance=assignment)
    
    return render(request, 'admin_panel/edit_assignment.html', {
        'form': form,
        'assignment': assignment
    })

@login_required
def delete_assignment(request, assignment_id):
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "Access denied!")
        return redirect('home')
    
    if request.method == 'POST':
        try:
            assignment = get_object_or_404(Assignment, id=assignment_id)
            assignment.delete()
            messages.success(request, "Assignment deleted successfully!")
        except Exception as e:
            messages.error(request, f"Error deleting assignment: {str(e)}")
    
    return redirect('admin_assignments')

@login_required
def assignment_submissions(request, assignment_id):
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "Access denied!")
        return redirect('home')
    
    assignment = get_object_or_404(Assignment, id=assignment_id)
    submissions = StudentAssignment.objects.filter(assignment=assignment).select_related('student__user')
    
    context = {
        'assignment': assignment,
        'submissions': submissions,
    }
    return render(request, 'admin_panel/assignment_submissions.html', context)

# ==================== STUDENT ASSIGNMENTS ====================

@login_required
def student_assignments(request):
    try:
        student_profile = StudentProfile.objects.get(user=request.user)
        
        # Get all assignments for student's courses
        student_assignments = StudentAssignment.objects.filter(
            student=student_profile
        ).select_related('assignment', 'assignment__course').order_by('assignment__due_date')
        
        # Count assignments by status
        not_started_count = student_assignments.filter(status='not_started').count()
        in_progress_count = student_assignments.filter(status='in_progress').count()
        submitted_count = student_assignments.filter(status='submitted').count()
        graded_count = student_assignments.filter(status='graded').count()
        
        # Get upcoming deadlines (assignments due in next 7 days)
        upcoming_deadlines = student_assignments.filter(
            assignment__due_date__lte=timezone.now() + timezone.timedelta(days=7),
            status__in=['not_started', 'in_progress']
        )
        
        context = {
            'student': student_profile,
            'student_assignments': student_assignments,
            'not_started_count': not_started_count,
            'in_progress_count': in_progress_count,
            'submitted_count': submitted_count,
            'graded_count': graded_count,
            'upcoming_deadlines': upcoming_deadlines,
        }
        return render(request, 'student/assignments.html', context)
    
    except StudentProfile.DoesNotExist:
        messages.error(request, "Student profile not found!")
        return redirect('student_login')

@login_required
def submit_assignment(request, assignment_id):
    try:
        student_profile = StudentProfile.objects.get(user=request.user)
        student_assignment = get_object_or_404(
            StudentAssignment, 
            assignment_id=assignment_id, 
            student=student_profile
        )
        
        if request.method == 'POST':
            form = StudentAssignmentForm(request.POST, request.FILES, instance=student_assignment)
            if form.is_valid():
                try:
                    student_assignment = form.save(commit=False)
                    student_assignment.status = 'submitted'
                    student_assignment.submitted_at = timezone.now()
                    student_assignment.save()
                    
                    messages.success(request, "Assignment submitted successfully!")
                    return redirect('student_assignments')
                except Exception as e:
                    messages.error(request, f"Error submitting assignment: {str(e)}")
            else:
                messages.error(request, "Please correct the errors below.")
        else:
            form = StudentAssignmentForm(instance=student_assignment)
        
        context = {
            'student': student_profile,
            'student_assignment': student_assignment,
            'form': form,
        }
        return render(request, 'student/submit_assignment.html', context)
    
    except StudentProfile.DoesNotExist:
        messages.error(request, "Student profile not found!")
        return redirect('student_login')
from .models import Assignment, StudentAssignment  # Add these imports
from .forms import AssignmentForm, StudentAssignmentForm  # Add these imports

# ==================== ADMIN ASSIGNMENTS MANAGEMENT ====================

@login_required
def admin_assignments(request):
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "Access denied!")
        return redirect('home')
    
    assignments = Assignment.objects.all().order_by('-created_at')
    
    # Count assignments by type
    project_count = assignments.filter(assignment_type='project').count()
    quiz_count = assignments.filter(assignment_type='quiz').count()
    homework_count = assignments.filter(assignment_type='homework').count()
    exam_count = assignments.filter(assignment_type='exam').count()
    
    # Count overdue assignments
    overdue_count = sum(1 for assignment in assignments if assignment.is_overdue())
    
    context = {
        'assignments': assignments,
        'project_count': project_count,
        'quiz_count': quiz_count,
        'homework_count': homework_count,
        'exam_count': exam_count,
        'overdue_count': overdue_count,
        'total_assignments': assignments.count(),
    }
    return render(request, 'admin_panel/assignments.html', context)

@login_required
def add_assignment(request):
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "Access denied!")
        return redirect('home')
    
    if request.method == 'POST':
        form = AssignmentForm(request.POST)
        if form.is_valid():
            try:
                assignment = form.save(commit=False)
                assignment.created_by = request.user
                assignment.save()
                
                # Create StudentAssignment entries for all students in the course
                students = StudentProfile.objects.filter(courses=assignment.course)
                for student in students:
                    StudentAssignment.objects.create(
                        student=student,
                        assignment=assignment
                    )
                
                messages.success(request, 'Assignment created successfully!')
                return redirect('admin_assignments')
            except Exception as e:
                messages.error(request, f"Error creating assignment: {str(e)}")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = AssignmentForm()
    
    return render(request, 'admin_panel/add_assignment.html', {'form': form})

@login_required
def edit_assignment(request, assignment_id):
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "Access denied!")
        return redirect('home')
    
    assignment = get_object_or_404(Assignment, id=assignment_id)
    
    if request.method == 'POST':
        form = AssignmentForm(request.POST, instance=assignment)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Assignment updated successfully!")
                return redirect('admin_assignments')
            except Exception as e:
                messages.error(request, f"Error updating assignment: {str(e)}")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = AssignmentForm(instance=assignment)
    
    return render(request, 'admin_panel/edit_assignment.html', {
        'form': form,
        'assignment': assignment
    })

@login_required
def delete_assignment(request, assignment_id):
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "Access denied!")
        return redirect('home')
    
    if request.method == 'POST':
        try:
            assignment = get_object_or_404(Assignment, id=assignment_id)
            assignment.delete()
            messages.success(request, "Assignment deleted successfully!")
        except Exception as e:
            messages.error(request, f"Error deleting assignment: {str(e)}")
    
    return redirect('admin_assignments')

@login_required
def assignment_submissions(request, assignment_id):
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "Access denied!")
        return redirect('home')
    
    assignment = get_object_or_404(Assignment, id=assignment_id)
    submissions = StudentAssignment.objects.filter(assignment=assignment).select_related('student__user')
    
    context = {
        'assignment': assignment,
        'submissions': submissions,
    }
    return render(request, 'admin_panel/assignment_submissions.html', context)

# ==================== STUDENT ASSIGNMENTS ====================

@login_required
def student_assignments(request):
    try:
        student_profile = StudentProfile.objects.get(user=request.user)
        
        # Get all assignments for student's courses
        student_assignments = StudentAssignment.objects.filter(
            student=student_profile
        ).select_related('assignment', 'assignment__course').order_by('assignment__due_date')
        
        # Calculate statistics
        total_count = student_assignments.count()
        completed_count = student_assignments.filter(status__in=['submitted', 'graded']).count()
        pending_count = student_assignments.filter(status__in=['not_started', 'in_progress']).count()
        overdue_count = student_assignments.filter(
            status__in=['not_started', 'in_progress'],
            assignment__due_date__lt=timezone.now()
        ).count()
        
        context = {
            'student': student_profile,
            'student_assignments': student_assignments,
            'completed_count': completed_count,
            'pending_count': pending_count,
            'overdue_count': overdue_count,
        }
        return render(request, 'student/assignments.html', context)
    
    except StudentProfile.DoesNotExist:
        messages.error(request, "Student profile not found!")
        return redirect('student_login')

@login_required
def submit_assignment(request, assignment_id):
    try:
        student_profile = StudentProfile.objects.get(user=request.user)
        student_assignment = get_object_or_404(
            StudentAssignment, 
            assignment_id=assignment_id, 
            student=student_profile
        )
        
        if request.method == 'POST':
            form = StudentAssignmentForm(request.POST, request.FILES, instance=student_assignment)
            if form.is_valid():
                try:
                    student_assignment = form.save(commit=False)
                    student_assignment.status = 'submitted'
                    student_assignment.submitted_at = timezone.now()
                    student_assignment.save()
                    
                    messages.success(request, "Assignment submitted successfully!")
                    return redirect('student_assignments')
                except Exception as e:
                    messages.error(request, f"Error submitting assignment: {str(e)}")
            else:
                messages.error(request, "Please correct the errors below.")
        else:
            form = StudentAssignmentForm(instance=student_assignment)
        
        context = {
            'student': student_profile,
            'student_assignment': student_assignment,
            'form': form,
        }
        return render(request, 'student/submit_assignment.html', context)
    
    except StudentProfile.DoesNotExist:
        messages.error(request, "Student profile not found!")
        return redirect('student_login')

@login_required
def student_resources(request):
    try:
        student_profile = StudentProfile.objects.get(user=request.user)
        resources = Resource.objects.all().order_by('-created_at')
        
        # Calculate resource counts
        pdf_count = resources.filter(resource_type='pdf').count()
        video_count = resources.filter(resource_type='video').count()
        link_count = resources.filter(resource_type__in=['youtube', 'link']).count()
        
        context = {
            'student': student_profile,
            'resources': resources,
            'pdf_count': pdf_count,
            'video_count': video_count,
            'link_count': link_count,
        }
        return render(request, 'student/resources.html', context)
    
    except StudentProfile.DoesNotExist:
        messages.error(request, "Student profile not found!")
        return redirect('student_login')
    
@login_required
def submit_assignment(request, assignment_id):
    try:
        student_profile = StudentProfile.objects.get(user=request.user)
        student_assignment = get_object_or_404(
            StudentAssignment, 
            assignment_id=assignment_id, 
            student=student_profile
        )
        
        if request.method == 'POST':
            form = StudentAssignmentForm(request.POST, request.FILES, instance=student_assignment)
            if form.is_valid():
                try:
                    student_assignment = form.save(commit=False)
                    student_assignment.status = 'submitted'
                    student_assignment.submitted_at = timezone.now()
                    student_assignment.save()
                    
                    messages.success(request, "Assignment submitted successfully!")
                    return redirect('student_assignments')
                except Exception as e:
                    messages.error(request, f"Error submitting assignment: {str(e)}")
            else:
                messages.error(request, "Please correct the errors below.")
        else:
            form = StudentAssignmentForm(instance=student_assignment)
        
        context = {
            'student': student_profile,
            'student_assignment': student_assignment,
            'form': form,
        }
        return render(request, 'student/submit_assignment.html', context)
    
    except StudentProfile.DoesNotExist:
        messages.error(request, "Student profile not found!")
        return redirect('student_login')
@login_required
def lesson_detail(request, course_id, lesson_id):
    try:
        course = get_object_or_404(Course, id=course_id)
        student_profile = StudentProfile.objects.get(user=request.user)
        lesson = get_object_or_404(Lesson, id=lesson_id, course=course)
        
        # Check if student is enrolled
        if not student_profile.courses.filter(id=course_id).exists():
            messages.error(request, "You are not enrolled in this course!")
            return redirect('student_dashboard')
        
        # Get or create lesson progress
        lesson_progress, created = StudentLessonProgress.objects.get_or_create(
            student=student_profile,
            lesson=lesson,
            defaults={'is_completed': False}
        )
        
        # Update last accessed time
        lesson_progress.save()
        
        # Get next and previous lessons
        all_lessons = Lesson.objects.filter(course=course, is_active=True).order_by('order')
        lesson_list = list(all_lessons)
        current_index = lesson_list.index(lesson)
        
        next_lesson = lesson_list[current_index + 1] if current_index + 1 < len(lesson_list) else None
        prev_lesson = lesson_list[current_index - 1] if current_index - 1 >= 0 else None
        
        context = {
            'course': course,
            'lesson': lesson,
            'lesson_progress': lesson_progress,
            'next_lesson': next_lesson,
            'prev_lesson': prev_lesson,
            'student': student_profile,
        }
        return render(request, 'student/lesson_detail.html', context)
        
    except StudentProfile.DoesNotExist:
        messages.error(request, "Student profile not found!")
        return redirect('student_login')

@login_required
def mark_lesson_complete(request, course_id, lesson_id):
    try:
        course = get_object_or_404(Course, id=course_id)
        student_profile = StudentProfile.objects.get(user=request.user)
        lesson = get_object_or_404(Lesson, id=lesson_id, course=course)
        
        # Check if student is enrolled
        if not student_profile.courses.filter(id=course_id).exists():
            messages.error(request, "You are not enrolled in this course!")
            return redirect('student_dashboard')
        
        # Update lesson progress
        lesson_progress, created = StudentLessonProgress.objects.get_or_create(
            student=student_profile,
            lesson=lesson
        )
        
        if not lesson_progress.is_completed:
            lesson_progress.is_completed = True
            lesson_progress.completed_at = timezone.now()
            lesson_progress.save()
            messages.success(request, f"Lesson '{lesson.title}' marked as completed!")
        else:
            messages.info(request, f"Lesson '{lesson.title}' was already completed.")
        
        return redirect('lesson_detail', course_id=course_id, lesson_id=lesson_id)
        
    except StudentProfile.DoesNotExist:
        messages.error(request, "Student profile not found!")
        return redirect('student_login')
# ==================== ADMIN LESSONS MANAGEMENT ====================

@login_required
def admin_lessons(request):
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "Access denied!")
        return redirect('home')
    
    course_id = request.GET.get('course_id')
    
    if course_id:
        lessons = Lesson.objects.filter(course_id=course_id).select_related('course').order_by('order')
        course = get_object_or_404(Course, id=course_id)
    else:
        lessons = Lesson.objects.all().select_related('course').order_by('course__name', 'order')
        course = None
    
    courses = Course.objects.all()
    
    context = {
        'lessons': lessons,
        'courses': courses,
        'selected_course': course,
        'total_lessons': lessons.count(),
    }
    return render(request, 'admin_panel/lessons.html', context)

@login_required
def add_lesson(request):
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "Access denied!")
        return redirect('home')
    
    if request.method == 'POST':
        try:
            course_id = request.POST.get('course')
            title = request.POST.get('title')
            description = request.POST.get('description')
            content = request.POST.get('content')
            video_url = request.POST.get('video_url')
            duration = request.POST.get('duration')
            order = request.POST.get('order', 0)
            
            course = get_object_or_404(Course, id=course_id)
            
            lesson = Lesson.objects.create(
                course=course,
                title=title,
                description=description,
                content=content,
                video_url=video_url,
                duration=duration,
                order=order
            )
            
            messages.success(request, f"Lesson '{title}' added successfully!")
            return redirect('admin_lessons')
            
        except Exception as e:
            messages.error(request, f"Error adding lesson: {str(e)}")
    
    courses = Course.objects.all()
    return render(request, 'admin_panel/add_lesson.html', {'courses': courses})

@login_required
def edit_lesson(request, lesson_id):
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "Access denied!")
        return redirect('home')
    
    lesson = get_object_or_404(Lesson, id=lesson_id)
    
    if request.method == 'POST':
        try:
            lesson.course_id = request.POST.get('course')
            lesson.title = request.POST.get('title')
            lesson.description = request.POST.get('description')
            lesson.content = request.POST.get('content')
            lesson.video_url = request.POST.get('video_url')
            lesson.duration = request.POST.get('duration')
            lesson.order = request.POST.get('order', 0)
            lesson.save()
            
            messages.success(request, f"Lesson '{lesson.title}' updated successfully!")
            return redirect('admin_lessons')
            
        except Exception as e:
            messages.error(request, f"Error updating lesson: {str(e)}")
    
    courses = Course.objects.all()
    return render(request, 'admin_panel/edit_lesson.html', {
        'lesson': lesson,
        'courses': courses
    })

@login_required
def delete_lesson(request, lesson_id):
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "Access denied!")
        return redirect('home')
    
    if request.method == 'POST':
        try:
            lesson = get_object_or_404(Lesson, id=lesson_id)
            lesson_title = lesson.title
            lesson.delete()
            
            messages.success(request, f"Lesson '{lesson_title}' deleted successfully!")
        except Exception as e:
            messages.error(request, f"Error deleting lesson: {str(e)}")
    
    return redirect('admin_lessons')

@login_required
def course_detail(request, course_id):
    try:
        course = get_object_or_404(Course, id=course_id)
        student_profile = StudentProfile.objects.get(user=request.user)
        
        # Check if student is enrolled
        if not student_profile.courses.filter(id=course_id).exists():
            messages.error(request, "You are not enrolled in this course!")
            return redirect('student_dashboard')
        
        # Get or create course progress
        progress = Progress.objects.filter(
            student=student_profile,
            course=course
        ).first()
        
        if not progress:
            progress = Progress.objects.create(
                student=student_profile,
                course=course,
                percentage=0,
                total_lessons=0
            )
        
        # Get real lessons from database - ADD DEBUGGING
        lessons = Lesson.objects.filter(course=course, is_active=True).order_by('order')
        
        print(f"DEBUG: Found {lessons.count()} lessons for course {course.name}")
        for lesson in lessons:
            print(f"DEBUG: Lesson - {lesson.title} (ID: {lesson.id})")
        
        # Update total lessons in progress
        if progress.total_lessons != lessons.count():
            progress.total_lessons = lessons.count()
            progress.save()
        
        # Get student progress for each lesson
        lesson_data = []
        completed_lessons = 0
        
        for lesson in lessons:
            lesson_progress = StudentLessonProgress.objects.filter(
                student=student_profile,
                lesson=lesson
            ).first()
            
            is_completed = lesson_progress.is_completed if lesson_progress else False
            if is_completed:
                completed_lessons += 1
            
            lesson_data.append({
                'id': lesson.id,
                'title': lesson.title,
                'description': lesson.description,
                'duration': lesson.duration,
                'completed': is_completed,
                'content': lesson.content
            })
        
        # Update progress percentage
        if lessons.count() > 0:
            new_percentage = int((completed_lessons / lessons.count()) * 100)
            if progress.percentage != new_percentage:
                progress.percentage = new_percentage
                progress.save()
        
        context = {
            'course': course,
            'progress': progress,
            'lessons': lesson_data,
            'student': student_profile,
        }
        return render(request, 'student/course_detail.html', context)
        
    except StudentProfile.DoesNotExist:
        messages.error(request, "Student profile not found!")
        return redirect('student_login')


# ==================== ADMIN DISCUSSION MANAGEMENT ====================

@login_required
def admin_discussions(request):
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "Access denied!")
        return redirect('home')
    
    discussion_rooms = DiscussionRoom.objects.all().select_related('course')
    total_posts = DiscussionPost.objects.count()
    total_replies = DiscussionReply.objects.count()
    recent_posts = DiscussionPost.objects.select_related('author__user', 'room__course').order_by('-created_at')[:10]
    
    context = {
        'discussion_rooms': discussion_rooms,
        'total_posts': total_posts,
        'total_replies': total_replies,
        'recent_posts': recent_posts,
    }
    return render(request, 'admin_panel/discussions.html', context)

@login_required
def create_discussion_room(request):
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "Access denied!")
        return redirect('home')
    
    if request.method == 'POST':
        course_id = request.POST.get('course')
        title = request.POST.get('title')
        description = request.POST.get('description')
        
        course = get_object_or_404(Course, id=course_id)
        
        discussion_room = DiscussionRoom.objects.create(
            course=course,
            title=title,
            description=description,
            created_by=request.user
        )
        
        messages.success(request, f"Discussion room '{title}' created successfully!")
        return redirect('admin_discussions')
    
    courses = Course.objects.all()
    return render(request, 'admin_panel/create_discussion_room.html', {'courses': courses})

@login_required
def admin_discussion_posts(request, room_id):
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "Access denied!")
        return redirect('home')
    
    room = get_object_or_404(DiscussionRoom, id=room_id)
    posts = DiscussionPost.objects.filter(room=room).select_related('author__user')
    
    context = {
        'room': room,
        'posts': posts,
    }
    return render(request, 'admin_panel/discussion_posts.html', context)

@login_required
def delete_discussion_post(request, post_id):
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "Access denied!")
        return redirect('home')
    
    if request.method == 'POST':
        post = get_object_or_404(DiscussionPost, id=post_id)
        post_title = post.title
        post.delete()
        
        messages.success(request, f"Post '{post_title}' deleted successfully!")
    
    return redirect('admin_discussions')

# ==================== STUDENT DISCUSSION FEATURES ====================
# Add these imports at the TOP of your views.py with other imports
from .models import DiscussionRoom, DiscussionPost, DiscussionReply
@login_required
def student_discussions(request):
    try:
        student_profile = StudentProfile.objects.get(user=request.user)
        
        # Get discussion rooms for student's enrolled courses
        enrolled_courses = student_profile.courses.all()
        discussion_rooms = DiscussionRoom.objects.filter(
            course__in=enrolled_courses, 
            is_active=True
        ).select_related('course')
        
        # Get recent posts from student's courses
        recent_posts = DiscussionPost.objects.filter(
            room__course__in=enrolled_courses
        ).select_related('author__user', 'room__course').order_by('-created_at')[:10]
        
        # Get student's own posts
        my_posts = DiscussionPost.objects.filter(
            author=student_profile
        ).select_related('room__course').order_by('-created_at')
        
        context = {
            'student': student_profile,
            'discussion_rooms': discussion_rooms,
            'recent_posts': recent_posts,
            'my_posts': my_posts,
        }
        return render(request, 'student/discussions.html', context)
    
    except StudentProfile.DoesNotExist:
        messages.error(request, "Student profile not found!")
        return redirect('student_login')

@login_required
def discussion_room(request, room_id):
    try:
        student_profile = StudentProfile.objects.get(user=request.user)
        room = get_object_or_404(DiscussionRoom, id=room_id)
        
        # Check if student is enrolled in the course
        if not student_profile.courses.filter(id=room.course.id).exists():
            messages.error(request, "You are not enrolled in this course!")
            return redirect('student_discussions')
        
        posts = DiscussionPost.objects.filter(room=room).select_related('author__user')
        
        if request.method == 'POST':
            title = request.POST.get('title')
            content = request.POST.get('content')
            post_type = request.POST.get('post_type', 'discussion')
            
            if title and content:
                post = DiscussionPost.objects.create(
                    room=room,
                    author=student_profile,
                    title=title,
                    content=content,
                    post_type=post_type
                )
                messages.success(request, "Post created successfully!")
                return redirect('discussion_room', room_id=room_id)
        
        context = {
            'student': student_profile,
            'room': room,
            'posts': posts,
        }
        return render(request, 'student/discussion_room.html', context)
    
    except StudentProfile.DoesNotExist:
        messages.error(request, "Student profile not found!")
        return redirect('student_login')