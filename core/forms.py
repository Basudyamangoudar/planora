from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from .models import StudentProfile, Resource, Progress, Course, Assignment, StudentAssignment

class StudentRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match!")

class StudentLoginForm(AuthenticationForm):
    username = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'placeholder':'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder':'Password'}))

class ResourceForm(forms.ModelForm):
    class Meta:
        model = Resource
        fields = ['title', 'description', 'resource_type', 'pdf_file', 'video_file', 'url', 'subject', 'grade_level']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'resource_type': forms.Select(attrs={'class': 'form-control'}),
            'pdf_file': forms.FileInput(attrs={'class': 'form-control'}),
            'video_file': forms.FileInput(attrs={'class': 'form-control'}),
            'url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://...'}),
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'grade_level': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        resource_type = cleaned_data.get('resource_type')
        
        if resource_type == 'pdf' and not cleaned_data.get('pdf_file'):
            raise forms.ValidationError("Please upload a PDF file for PDF resources.")
        elif resource_type == 'video' and not cleaned_data.get('video_file'):
            raise forms.ValidationError("Please upload a video file for video resources.")
        elif resource_type in ['youtube', 'link'] and not cleaned_data.get('url'):
            raise forms.ValidationError("Please provide a URL for link resources.")
        
        return cleaned_data

class ProgressForm(forms.ModelForm):
    class Meta:
        model = Progress
        # Only include fields that actually exist in your Progress model
        fields = ['percentage']  # Basic field that should exist
        widgets = {
            'percentage': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
        }

class ProgressUpdateForm(forms.ModelForm):
    class Meta:
        model = Progress
        # Only include fields that actually exist in your Progress model
        fields = ['percentage']  # Basic field that should exist
        widgets = {
            'percentage': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
        }

class AssignmentForm(forms.ModelForm):
    due_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        input_formats=['%Y-%m-%dT%H:%M']
    )
    
    class Meta:
        model = Assignment
        fields = ['course', 'title', 'description', 'assignment_type', 'due_date', 'max_points', 'instructions', 'resources', 'status']
        widgets = {
            'course': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'assignment_type': forms.Select(attrs={'class': 'form-control'}),
            'max_points': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'instructions': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'resources': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

class StudentAssignmentForm(forms.ModelForm):
    class Meta:
        model = StudentAssignment
        fields = ['submission_text', 'submitted_file']
        widgets = {
            'submission_text': forms.Textarea(attrs={
                'rows': 6, 
                'class': 'form-control',
                'placeholder': 'Enter your assignment submission here...'
            }),
            'submitted_file': forms.FileInput(attrs={'class': 'form-control'}),
        }