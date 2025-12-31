from django.urls import path

from apps.documents.viewsets import DocumentViewSet

urlpatterns = [
    path("documents", DocumentViewSet.as_view()),
]
