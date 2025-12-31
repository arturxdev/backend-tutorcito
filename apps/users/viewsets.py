from rest_framework import viewsets

from apps.users.models import User
from apps.users import serializers


class UserViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.UserSerializer
    queryset = User.objects.all()
