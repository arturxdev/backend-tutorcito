import uuid
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.parsers import MultiPartParser, FormParser
from drf_spectacular.utils import extend_schema
from apps.documents.models import Document
from apps.documents import serializers
from apps.documents.utils import R2Storage, get_pdf_metadata
from apps.documents.tasks import process_pdf
import logging

logger = logging.getLogger(__name__)


class DocumentUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request={
            "multipart/form-data": serializers.DocumentUploadSerializer,
        },
        responses={201: serializers.DocumentSerializer},
        description="Upload a PDF document. Only the 'file' field is required.",
    )
    def post(self, request, *args, **kwargs):
        logger.info("=" * 60)
        logger.info("📤 [UPLOAD] Document upload request received")
        logger.info(f"📤 [UPLOAD] User authenticated: {request.user.is_authenticated}")

        if request.user.is_authenticated:
            logger.info(f"📤 [UPLOAD] User ID: {request.user.id}")
            logger.info(f"📤 [UPLOAD] User email: {request.user.email}")
            logger.info(f"📤 [UPLOAD] User Clerk ID: {request.user.clerk_id}")
        else:
            logger.warning("⚠️  [UPLOAD] User not authenticated!")

        serializer = serializers.DocumentUploadSerializer(data=request.data)
        if not serializer.is_valid():
            logger.error(
                f"❌ [UPLOAD] Serializer validation failed: {serializer.errors}"
            )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        file_obj = serializer.validated_data["file"]
        user = request.user

        logger.info(f"📤 [UPLOAD] File received - Name: {file_obj.name}")
        logger.info(
            f"📤 [UPLOAD] File size: {file_obj.size} bytes ({file_obj.size / 1024:.2f} KB)"
        )
        logger.info(f"📤 [UPLOAD] File content type: {file_obj.content_type}")

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
            logger.info("📤 [UPLOAD] Reading file content...")
            file_content = file_obj.read()
            logger.info(
                f"📤 [UPLOAD] File content read successfully ({len(file_content)} bytes)"
            )

            # 2. Metadata Extraction
            logger.info("📤 [UPLOAD] Extracting PDF metadata...")
            metadata = get_pdf_metadata(file_content)
            logger.info(f"📤 [UPLOAD] PDF has {metadata['num_pages']} pages")
            logger.info(f"📤 [UPLOAD] PDF MD5 hash: {metadata['hash_md5']}")

            # 3. R2 Upload
            logger.info("📤 [UPLOAD] Uploading to R2 storage...")
            storage = R2Storage()
            storage_filename = f"{uuid.uuid4()}_{file_obj.name}"
            public_url = storage.upload_file(
                file_content, storage_filename, file_obj.content_type
            )
            logger.info(f"✅ [UPLOAD] File uploaded to R2: {public_url}")

            # 4. Save to Database
            logger.info("📤 [UPLOAD] Creating document record in database...")
            document = Document.objects.create(
                url=public_url,
                name=file_obj.name,
                size=file_obj.size,
                content_type=file_obj.content_type,
                r2_key=f"pdfs/{storage_filename}",
                hash_md5=metadata["hash_md5"],
                num_pages=metadata["num_pages"],
                user=user,
            )
            logger.info(f"✅ [UPLOAD] Document created with ID: {document.id}")

            logger.info("📤 [UPLOAD] Queuing PDF processing task...")
            process_pdf(document.id)
            logger.info("✅ [UPLOAD] PDF processing task queued successfully")

            logger.info("✅ [UPLOAD] Document upload completed successfully!")
            logger.info("=" * 60)
            return Response(
                {
                    "data": serializers.DocumentSerializer(document).data,
                    "message": "Archivo recibido y procesado exitosamente.",
                    "status": "success",
                },
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            logger.error("❌ [UPLOAD] Upload failed with exception")
            logger.error(f"❌ [UPLOAD] Error type: {type(e).__name__}")
            logger.error(f"❌ [UPLOAD] Error message: {str(e)}")
            logger.error(f"❌ [UPLOAD] Full error: {repr(e)}")
            logger.info("=" * 60)
            return Response(
                {"error": f"An error occurred during processing: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
