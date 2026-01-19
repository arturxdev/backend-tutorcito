from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("exams", "0002_alter_exam_result"),
    ]

    operations = [
        migrations.RemoveField("exam", "result"),
    ]
