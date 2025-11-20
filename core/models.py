from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone

# ---------------- Courses ----------------
class Course(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

# ---------------- Student Profile ----------------
class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    age = models.PositiveIntegerField()
    mobile = models.CharField(max_length=10)
    courses = models.ManyToManyField(Course, blank=True)

    def __str__(self):
        return self.user.username

# ---------------- Student Request ----------------
class StudentRequest(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    mobile = models.CharField(max_length=10)
    age = models.PositiveIntegerField()
    courses = models.ManyToManyField(Course)
    is_approved = models.BooleanField(default=False)
    
    # ADD THIS FIELD
    password_plain = models.CharField(max_length=128, blank=True)  # Store plain password temporarily
    
    def set_password(self, raw_password):
        self.password = make_password(raw_password)
        self.password_plain = raw_password  # Store plain version
    
    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def __str__(self):
        return self.username

# ---------------- Lesson/Lecture Model ----------------
class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    content = models.TextField(help_text="HTML content for the lesson")
    video_url = models.URLField(blank=True, null=True)
    duration = models.CharField(max_length=50, default='30 minutes')
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['course', 'order']
    
    def __str__(self):
        return f"{self.course.name} - {self.title}"

# ---------------- Student Lesson Progress ----------------
class StudentLessonProgress(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    time_spent = models.PositiveIntegerField(default=0, help_text="Time spent in seconds")
    notes = models.TextField(blank=True)
    last_accessed = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['student', 'lesson']

    def __str__(self):
        status = "Completed" if self.is_completed else "In Progress"
        return f"{self.student.user.username} - {self.lesson.title} ({status})"

# ---------------- Quiz/Assignment Model ----------------
class Quiz(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    total_questions = models.PositiveIntegerField(default=5)
    passing_score = models.PositiveIntegerField(default=60)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.course.name} - {self.title}"

# ---------------- Student Quiz Attempt ----------------
class StudentQuizAttempt(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    score = models.PositiveIntegerField(default=0)
    total_questions = models.PositiveIntegerField(default=5)
    passed = models.BooleanField(default=False)
    attempted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.user.username} - {self.quiz.title} - {self.score}%"

# ---------------- Resources ----------------
class Resource(models.Model):
    RESOURCE_TYPES = [
        ('pdf', 'PDF File'),
        ('youtube', 'YouTube Video'),
        ('link', 'External Link'),
        ('video', 'Video File'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    resource_type = models.CharField(max_length=10, choices=RESOURCE_TYPES)
    
    # For PDF files
    pdf_file = models.FileField(upload_to='resources/pdfs/', blank=True, null=True)
    
    # For video files
    video_file = models.FileField(upload_to='resources/videos/', blank=True, null=True)
    
    # For links (YouTube URLs, external links)
    url = models.URLField(blank=True)
    
    subject = models.CharField(max_length=100)
    
    # Make these nullable and with defaults initially
    grade_level = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        if self.resource_type == 'pdf' and self.pdf_file:
            return self.pdf_file.url
        elif self.resource_type == 'youtube' and self.url:
            return self.url
        elif self.resource_type == 'link' and self.url:
            return self.url
        elif self.resource_type == 'video' and self.video_file:
            return self.video_file.url
        return '#'

# ---------------- Notifications ----------------
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Notification for {self.user.username}"

# ---------------- Progress ----------------
class Progress(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True, blank=True)
    percentage = models.IntegerField(default=0)
    completed_lessons = models.IntegerField(default=0)
    total_lessons = models.IntegerField(default=10)
    last_activity = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ['student', 'course']
    
    def __str__(self):
        if self.course:
            return f"{self.student.user.username} - {self.course.name}: {self.percentage}%"
        else:
            return f"{self.student.user.username} - Overall: {self.percentage}%"
    
    def save(self, *args, **kwargs):
        # Handle the case where course is None (overall progress)
        if self.course is None:
            # Delete any existing overall progress for this student
            Progress.objects.filter(
                student=self.student, 
                course__isnull=True
            ).exclude(pk=self.pk).delete()
        super().save(*args, **kwargs)

    def calculate_real_progress(self):
        """Calculate progress based on actual student activities"""
        if self.course:  # Course-specific progress
            # Get total lessons for this course
            total_lessons = Lesson.objects.filter(course=self.course, is_active=True).count()
            
            # Get completed lessons for this student in this course
            completed_lessons = StudentLessonProgress.objects.filter(
                student=self.student,
                lesson__course=self.course,
                is_completed=True
            ).count()
            
            # Get quiz performance for this course
            quiz_attempts = StudentQuizAttempt.objects.filter(
                student=self.student,
                quiz__course=self.course
            )
            
            if total_lessons > 0:
                lesson_progress = (completed_lessons / total_lessons) * 100
                
                # Calculate quiz progress (average of all quiz scores)
                quiz_progress = 0
                if quiz_attempts.exists():
                    total_quiz_score = sum(attempt.score for attempt in quiz_attempts)
                    quiz_progress = total_quiz_score / quiz_attempts.count()
                
                # Combined progress (70% lessons + 30% quizzes)
                self.percentage = min(100, int((lesson_progress * 0.7) + (quiz_progress * 0.3)))
                self.completed_lessons = completed_lessons
                self.total_lessons = total_lessons
                
        else:  # Overall progress across all courses
            total_courses = self.student.courses.count()
            if total_courses > 0:
                course_progresses = Progress.objects.filter(
                    student=self.student
                ).exclude(course=None)
                
                if course_progresses.exists():
                    total_progress = sum(progress.percentage for progress in course_progresses)
                    self.percentage = min(100, int(total_progress / course_progresses.count()))
        
        self.save()
        return self.percentage

    def update_progress(self, completed_lessons=None):
        """Keep the old method for backward compatibility"""
        if completed_lessons is not None:
            self.completed_lessons = completed_lessons
        if self.total_lessons > 0:
            self.percentage = min(100, int((self.completed_lessons / self.total_lessons) * 100))
        self.save()

# ---------------- Assignment Models ----------------
class Assignment(models.Model):
    ASSIGNMENT_TYPES = [
        ('project', 'Project'),
        ('quiz', 'Quiz'),
        ('homework', 'Homework'),
        ('exam', 'Exam'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('completed', 'Completed'),
    ]
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    assignment_type = models.CharField(max_length=20, choices=ASSIGNMENT_TYPES, default='homework')
    due_date = models.DateTimeField()
    max_points = models.IntegerField(default=100)
    instructions = models.TextField(blank=True)
    resources = models.TextField(blank=True, help_text="Additional resources or links")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-due_date']
    
    def __str__(self):
        return f"{self.title} - {self.course.name}"
    
    def is_overdue(self):
        return timezone.now() > self.due_date
    
    def days_until_due(self):
        delta = self.due_date - timezone.now()
        return delta.days
    
    def get_status_badge(self):
        if self.is_overdue():
            return 'danger'
        elif self.days_until_due() <= 2:
            return 'warning'
        elif self.days_until_due() <= 7:
            return 'info'
        else:
            return 'success'

class StudentAssignment(models.Model):
    SUBMISSION_STATUS = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('submitted', 'Submitted'),
        ('graded', 'Graded'),
    ]
    
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=SUBMISSION_STATUS, default='not_started')
    submitted_file = models.FileField(upload_to='assignments/submissions/', null=True, blank=True)
    submission_text = models.TextField(blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    grade = models.IntegerField(null=True, blank=True)
    feedback = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['student', 'assignment']
    
    def __str__(self):
        return f"{self.student.user.username} - {self.assignment.title}"
    
    def is_submitted(self):
        return self.status in ['submitted', 'graded']
    
    def is_graded(self):
        return self.status == 'graded'


# Add these to your existing models.py

class DiscussionRoom(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_pinned = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.course.name} - {self.title}"

class DiscussionPost(models.Model):
    POST_TYPES = [
        ('question', '❓ Question'),
        ('discussion', '💬 Discussion'),
        ('announcement', '📢 Announcement'),
        ('resource', '📚 Resource Share'),
    ]
    
    room = models.ForeignKey(DiscussionRoom, on_delete=models.CASCADE)
    author = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    content = models.TextField()
    post_type = models.CharField(max_length=20, choices=POST_TYPES, default='discussion')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_pinned = models.BooleanField(default=False)
    is_resolved = models.BooleanField(default=False)
    views = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-is_pinned', '-created_at']

    def __str__(self):
        return f"{self.title} - {self.author.user.username}"

class DiscussionReply(models.Model):
    post = models.ForeignKey(DiscussionPost, on_delete=models.CASCADE)
    author = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_instructor_reply = models.BooleanField(default=False)
    likes = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Reply by {self.author.user.username}"