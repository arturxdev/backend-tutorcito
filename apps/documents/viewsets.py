from rest_framework import viewsets, mixins, permissions
from apps.documents.models import Document
from apps.documents import serializers


class DocumentViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet for viewing, updating, and deleting documents.
    Creation is handled separately via DocumentUploadView.
    """

    serializer_class = serializers.DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Solo documentos del usuario autenticado"""
        return Document.objects.filter(user=self.request.user)
