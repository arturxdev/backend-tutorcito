import hashlib
from typing import Dict, Any
from io import BytesIO
from django.conf import settings
import boto3
from botocore.client import Config
from pypdf import PdfReader


class R2Storage:
    """
    Cloudflare R2 Storage client using S3-compatible API
    """

    def __init__(self):
        self.account_id = settings.R2_ACCOUNT_ID
        self.access_key_id = settings.R2_ACCESS_KEY_ID
        self.secret_access_key = settings.R2_SECRET_ACCESS_KEY
        self.bucket_name = settings.R2_BUCKET_NAME
        self.public_url = settings.R2_PUBLIC_URL  # Public R2.dev URL or custom domain

        if not all(
            [
                self.account_id,
                self.access_key_id,
                self.secret_access_key,
                self.bucket_name,
            ]
        ):
            raise ValueError(
                "R2 configuration is incomplete. Check R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, "
                "R2_SECRET_ACCESS_KEY, and R2_BUCKET_NAME."
            )

        # Create S3 client configured for R2
        self.client = boto3.client(
            "s3",
            endpoint_url=f"https://{self.account_id}.r2.cloudflarestorage.com",
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
            config=Config(signature_version="s3v4"),
            region_name="auto",
        )

    def upload_file(
        self, file_content: bytes, file_name: str, content_type: str
    ) -> str:
        """
        Uploads a file to R2 Storage and returns the public URL.
        """
        path = f"pdfs/{file_name}"

        # Upload to R2
        self.client.put_object(
            Bucket=self.bucket_name,
            Key=path,
            Body=file_content,
            ContentType=content_type,
        )

        # Return public URL
        if self.public_url:
            return f"{self.public_url}/{path}"
        else:
            # Fallback to R2.dev URL
            return f"https://{self.bucket_name}.{self.account_id}.r2.cloudflarestorage.com/{path}"

    def download_file(self, path: str) -> bytes:
        """
        Downloads a file from R2 Storage.
        """
        response = self.client.get_object(Bucket=self.bucket_name, Key=path)
        return response["Body"].read()


def get_pdf_metadata(file_content: bytes) -> Dict[str, Any]:
    """
    Extracts number of pages and MD5 hash from PDF content.
    """
    reader = PdfReader(BytesIO(file_content))
    num_pages = len(reader.pages)

    hash_md5 = hashlib.md5(file_content).hexdigest()

    return {"num_pages": num_pages, "hash_md5": hash_md5}
