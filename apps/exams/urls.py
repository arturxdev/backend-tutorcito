from django.urls import path

from rest_framework.routers import DefaultRouter

from apps.exams.views import ListExamView, DetailExamView

router = DefaultRouter()

urlpatterns = [
    path("exams/", ListExamView.as_view()),
    path("exams/<int:pk>", DetailExamView.as_view()),
] + router.urls
