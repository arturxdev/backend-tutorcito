from django.urls import path

from rest_framework.routers import DefaultRouter

from apps.exams.views import (
    ListExamView,
    DetailExamView,
    UpdateExamResultView,
    CreateExamAttemptView,
    ListExamAttemptsView,
    CreateFailureExamView,
)

router = DefaultRouter()

urlpatterns = [
    path("exams/", ListExamView.as_view()),
    path("exams/<int:pk>", DetailExamView.as_view()),
    path("exams/<int:exam_id>/attempts/", CreateExamAttemptView.as_view()),
    path("exams/attempts/", ListExamAttemptsView.as_view()),
    path("exams/failures/", CreateFailureExamView.as_view()),
] + router.urls
