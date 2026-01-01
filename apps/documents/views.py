import uuid
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from drf_spectacular.utils import extend_schema
from apps.documents.models import Document
from apps.documents import serializers
from apps.documents.utils import SupabaseStorage, get_pdf_metadata
from apps.documents.tasks import process_pdf
from apps.users.models import User
import logging

logger = logging.getLogger(__name__)


class DocumentUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    @extend_schema(
        request={
            "multipart/form-data": serializers.DocumentUploadSerializer,
        },
        responses={201: serializers.DocumentSerializer},
        description="Upload a PDF document. Only the 'file' field is required.",
    )
    def post(self, request, *args, **kwargs):
        logger.info("File upload")
        serializer = serializers.DocumentUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        file_obj = serializer.validated_data["file"]

        user_id = serializer.validated_data["user_id"]
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            # Opción A: Error de validación (400 Bad Request)
            return Response(
                {"user_id": "El usuario con este ID no existe."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 1. Validation (already partially done by serializer, but keeping explicit checks)
        if file_obj.size > 50 * 1024 * 1024:
            return Response(
                {"error": "File size exceeds 50MB limit."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if (
            not file_obj.name.lower().endswith(".pdf")
            and file_obj.content_type != "application/pdf"
        ):
            return Response(
                {"error": "Only PDF files are allowed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            file_content = file_obj.read()

            # 2. Metadata Extraction
            metadata = get_pdf_metadata(file_content)

            # 3. Supabase Upload
            storage = SupabaseStorage()
            storage_filename = f"{uuid.uuid4()}_{file_obj.name}"
            public_url = storage.upload_file(
                file_content, storage_filename, file_obj.content_type
            )
            logger.info(f"File uploaded to Supabase: {public_url}")
            # 4. Save to Database
            document = Document.objects.create(
                url=public_url,
                name=file_obj.name,
                size=file_obj.size,
                content_type=file_obj.content_type,
                r2_key=f"documents/{storage_filename}",
                hash_md5=metadata["hash_md5"],
                num_pages=metadata["num_pages"],
                user=user,
            )
            process_pdf(document.id)

            return Response(
                {
                    "data": serializers.DocumentSerializer(document).data,
                    "message": "Archivo recibido y procesado exitosamente.",
                    "status": "success",
                },
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response(
                {"error": f"An error occurred during processing: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
