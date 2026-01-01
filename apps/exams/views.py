from rest_framework.generics import ListAPIView, RetrieveUpdateDestroyAPIView
from apps.exams.models import Exam
from apps.exams import serializers
from rest_framework.response import Response
from rest_framework import status
from apps.exams.tasks import create_exam


class ListExamView(ListAPIView):
    allowed_methods = ["GET", "POST"]
    serializer_class = serializers.ExamSerializer
    queryset = Exam.objects.all()

    def post(self, request, *args, **kwargs):
        serializer = serializers.ExamSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        exam = serializer.save()

        # In ModelSerializer, the field is 'document' and returns the ID or object
        document_id = serializer.validated_data["document"].id

        create_exam(
            document_id,
            exam.page_start,
            exam.page_end,
            exam.id,
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class DetailExamView(RetrieveUpdateDestroyAPIView):
    allowed_methods = ["GET", "PUT", "DELETE"]
    serializer_class = serializers.ExamSerializer
    queryset = Exam.objects.all()
