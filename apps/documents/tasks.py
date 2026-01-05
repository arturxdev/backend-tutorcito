import io
import logging
from huey.contrib.djhuey import db_task
from pypdf import PdfReader
from apps.documents.models import Document, Block
from apps.documents.utils import R2Storage

logger = logging.getLogger(__name__)


@db_task()
def process_pdf(document_id):
    """
    Task to extract text from a PDF document and save it as Blocks.
    """
    print("Starting PDF text extraction for document: %s", document_id)
    logger.info("Starting PDF text extraction for document: %s", document_id)
    try:
        # 1. Fetch document from database
        try:
            document = Document.objects.get(id=document_id)
        except Document.DoesNotExist:
            logger.error("Document not found: %s", document_id)
            return {"status": "error", "message": "Document not found"}

        # 2. Download file from R2
        storage = R2Storage()
        # Use the r2_key which contains the path in the bucket
        pdf_data = storage.download_file(document.r2_key)

        # 3. Extract text using pypdf
        reader = PdfReader(io.BytesIO(pdf_data))
        total_pages = len(reader.pages)
        logger.info("Processing %d pages for document: %s", total_pages, document.name)

        blocks_to_create = []
        for i in range(total_pages):
            page_number = i + 1
            native_text = reader.pages[i].extract_text() or ""

            # Basic text cleaning: normalize whitespace
            content = " ".join(native_text.strip().split())

            blocks_to_create.append(
                Block(
                    content=content,
                    page=page_number,
                    document=document,
                    user=document.user,
                )
            )
            logger.debug("Page %d: Text extracted (native)", page_number)

        # 4. Save blocks to database in bulk
        if blocks_to_create:
            Block.objects.bulk_create(blocks_to_create)

        logger.info("PDF text extraction completed for document: %s", document_id)
        return {
            "status": "success",
            "document_id": str(document_id),
            "message": "Text extracted and saved successfully",
            "pages_processed": total_pages,
        }

    except Exception as exc:
        logger.error("Error extracting text from PDF %s: %s", document_id, exc)
        # Re-raise to let Celery handle retries if configured
        raise
