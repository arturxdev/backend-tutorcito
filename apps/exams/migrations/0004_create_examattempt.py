import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("exams", "0003_remove_exam_result"),
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ExamAttempt",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("answers", models.JSONField()),
                ("score", models.IntegerField()),
                ("total_questions", models.IntegerField()),
                ("started_at", models.DateTimeField()),
                ("completed_at", models.DateTimeField()),
                ("created_at", models.DateField(auto_now_add=True)),
                (
                    "exam",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="attempts",
                        to="exams.exam",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="exam_attempts",
                        to="users.user",
                    ),
                ),
            ],
            options={
                "indexes": [
                    models.Index(
                        fields=["user", "completed_at"],
                        name="exams_exama_user_comp_idx",
                    ),
                    models.Index(fields=["exam"], name="exams_exama_exam_id_idx"),
                ],
            },
        ),
    ]
