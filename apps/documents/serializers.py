from rest_framework import serializers

from apps.documents.models import Document, Block


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = "__all__"


class BlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Block
        fields = "__all__"


class DocumentUploadSerializer(serializers.Serializer):
    file = serializers.FileField(required=True)
