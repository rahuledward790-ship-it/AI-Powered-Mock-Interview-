from django.conf import settings
from django.db import models


class InterviewQuestion(models.Model):

    CATEGORY_CHOICES = [

        ('HR', 'HR'),

        ('Python', 'Python'),

        ('Java', 'Java'),

        ('Aptitude', 'Aptitude'),

    ]

    question = models.TextField()

    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES
    )

    difficulty = models.CharField(
        max_length=20
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.question


class InterviewAttempt(models.Model):
    CATEGORY_CHOICES = [
        ('HR', 'HR'),
        ('Technical', 'Technical'),
        ('Aptitude', 'Aptitude'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    question = models.ForeignKey(InterviewQuestion, on_delete=models.SET_NULL, null=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    answer = models.TextField()
    feedback = models.TextField(blank=True)
    score = models.FloatField(default=0)
    communication_score = models.FloatField(default=0)
    confidence_score = models.FloatField(default=0)
    body_language_score = models.FloatField(default=0.0)
    eye_contact_score = models.FloatField(default=0.0)
    fluency_score = models.FloatField(default=0.0)
    grammar_analysis = models.TextField(blank=True)
    duration_seconds = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.category} - {self.score}/10"


class Resume(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='resumes')
    phone_number = models.CharField(max_length=20, blank=True)
    resume_file = models.FileField(upload_to='resumes/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    hiring_status = models.CharField(max_length=50, default='Pending')  # 'Pending', 'Selected', 'Rejected'

    def __str__(self):
        return f"{self.user.username} - {self.resume_file.name}"


class AptitudeAttempt(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='aptitude_attempts')
    question = models.ForeignKey(InterviewQuestion, on_delete=models.SET_NULL, null=True)
    answer = models.TextField()
    score = models.IntegerField(default=0)  # Marks scored (e.g. 0 or 10)
    percentage = models.FloatField(default=0.0)  # Percentage (e.g. 0% or 100%)
    time_taken = models.IntegerField(default=0)  # in seconds
    is_correct = models.BooleanField(default=False)
    final_result = models.CharField(max_length=20, default='Fail')  # 'Pass' or 'Fail'
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - Aptitude - {self.score}"

