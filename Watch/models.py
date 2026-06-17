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
    duration_seconds = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.category} - {self.score}/10"
