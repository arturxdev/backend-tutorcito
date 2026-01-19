from rest_framework import serializers
from apps.exams.models import Exam, Question, ExamAttempt


class ExamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exam
        fields = "__all__"
        read_only_fields = ["user"]


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = "__all__"


class ExamResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exam
        fields = ["result"]


class ExamAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExamAttempt
        fields = "__all__"


class CreateExamAttemptSerializer(serializers.Serializer):
    answers = serializers.DictField()
    started_at = serializers.DateTimeField()
    completed_at = serializers.DateTimeField()


class CreateFailureExamSerializer(serializers.Serializer):
    start_date = serializers.DateTimeField()
    end_date = serializers.DateTimeField()
    num_questions = serializers.IntegerField(max_value=20, default=10)


class QuestionOptionSerializer(serializers.Serializer):
    """Serializer for question answer options"""
    id = serializers.UUIDField()
    text = serializers.CharField()
    isCorrect = serializers.BooleanField()


class GeneratedQuestionSerializer(serializers.Serializer):
    """Serializer for AI-generated questions"""
    question = serializers.CharField()
    options = QuestionOptionSerializer(many=True)
    difficulty = serializers.ChoiceField(choices=["easy", "medium", "hard"])


class ExamCreationResponseSerializer(serializers.Serializer):
    """Response when creating a new exam with generated questions"""
    exam = ExamSerializer(read_only=True)
    questions = GeneratedQuestionSerializer(many=True, read_only=True)
