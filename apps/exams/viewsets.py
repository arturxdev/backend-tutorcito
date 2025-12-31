from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend

from apps.exams import serializers
from apps.exams.models import Question


class QuestionViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.QuestionSerializer
    queryset = Question.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["exam_id", "difficulty"]
