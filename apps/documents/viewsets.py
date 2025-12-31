from rest_framework import viewsets, mixins
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
    queryset = Document.objects.all()
