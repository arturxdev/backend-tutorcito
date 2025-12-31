from django.urls import path

from rest_framework.routers import DefaultRouter

from apps.exams.views import ListExamView, DetailExamView
from apps.exams.viewsets import QuestionViewSet

router = DefaultRouter()
router.register("questions", QuestionViewSet)

urlpatterns = [
    path("exams/", ListExamView.as_view()),
    path("exams/<int:pk>", DetailExamView.as_view()),
] + router.urls
