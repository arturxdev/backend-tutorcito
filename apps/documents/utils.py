import hashlib
from typing import Dict, Any
from io import BytesIO
from django.conf import settings
from supabase import create_client, Client
from pypdf import PdfReader


class SupabaseStorage:
    def __init__(self):
        self.url = settings.SUPABASE_URL
        self.key = settings.SUPABASE_KEY
        self.bucket_name = settings.SUPABASE_BUCKET_NAME

        if not all([self.url, self.key, self.bucket_name]):
            raise ValueError(
                "Supabase configuration is incomplete. Check SUPABASE_URL, SUPABASE_KEY, and SUPABASE_BUCKET_NAME."
            )

        self.client: Client = create_client(self.url, self.key)

    def upload_file(
        self, file_content: bytes, file_name: str, content_type: str
    ) -> str:
        """
        Uploads a file to Supabase Storage and returns the public URL.
        """
        path = f"documents/{file_name}"

        # Upload using the storage client
        self.client.storage.from_(self.bucket_name).upload(
            path=path, file=file_content, file_options={"content-type": content_type}
        )

        # Check if we should use public URL or a signed one.
        # Assuming public for now if the bucket is public.
        return self.client.storage.from_(self.bucket_name).get_public_url(path)

    def download_file(self, path: str) -> bytes:
        """
        Downloads a file from Supabase Storage.
        """
        return self.client.storage.from_(self.bucket_name).download(path)


def get_pdf_metadata(file_content: bytes) -> Dict[str, Any]:
    """
    Extracts number of pages and MD5 hash from PDF content.
    """
    reader = PdfReader(BytesIO(file_content))
    num_pages = len(reader.pages)

    hash_md5 = hashlib.md5(file_content).hexdigest()

    return {"num_pages": num_pages, "hash_md5": hash_md5}
