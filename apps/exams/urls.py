from django.urls import path

from apps.exams.views import ListExamView, DetailExamView

urlpatterns = [
    path("exams/", ListExamView.as_view()),
    path("exams/<int:pk>", DetailExamView.as_view()),
]
