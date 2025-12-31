from django.db import models
from apps.documents.models import Document
from apps.users.models import User


class Exam(models.Model):
    document_id = models.ForeignKey(Document, on_delete=models.CASCADE)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    page_start = models.IntegerField()
    page_end = models.IntegerField()
    status = models.CharField(
        max_length=20,
        choices=[
            ("process", "Processing"),
            ("done", "Completed"),
            ("fail", "Failed"),
        ],
        default="process",
    )
    num_questions = models.IntegerField(default=10)
    created_at = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.document} - {self.user} ({self.status})"


class Question(models.Model):
    exam_id = models.ForeignKey(
        Exam, on_delete=models.CASCADE, related_name="questions"
    )
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


class Result(models.Model):
    document_id = models.ForeignKey(Document, on_delete=models.CASCADE)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    feedback = models.TextField()
    created_at = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.feedback} - {self.document} - {self.user}"
