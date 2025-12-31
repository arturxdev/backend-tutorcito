from django.urls import path

from apps.users.viewsets import UserViewSet

urlpatterns = [
    path("users", UserViewSet.as_view()),
]
