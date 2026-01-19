from django.db import models
from apps.documents.models import Document
from apps.users.models import User


class Exam(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    page_start = models.IntegerField()
    page_end = models.IntegerField()
    num_questions = models.IntegerField(default=10)
    created_at = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.document} - {self.user}"


class Question(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="questions")
    question = models.TextField()
    options = models.JSONField()
    difficulty = models.CharField(
        max_length=20,
        choices=[
            ("facil", "Fácil"),
            ("medio", "Medio"),
            ("dificil", "Difícil"),
        ],
        default="medio",
    )
    created_at = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.question[:50]}... - {self.exam}"


class ExamAttempt(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="attempts")
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="exam_attempts"
    )
    answers = models.JSONField()
    score = models.IntegerField()
    total_questions = models.IntegerField()
    started_at = models.DateTimeField()
    completed_at = models.DateTimeField()
    created_at = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.exam} - Score: {self.score}/{self.total_questions}"

    class Meta:
        indexes = [
            models.Index(fields=["user", "completed_at"]),
            models.Index(fields=["exam"]),
        ]
