from django.db import models

from apps.users.models import User


class Document(models.Model):
    url = models.TextField(max_length=250)
    name = models.TextField(max_length=250)
    size = models.IntegerField()
    content_type = models.TextField(max_length=12)
    r2_key = models.TextField(max_length=250)
    hash_md5 = models.TextField(max_length=32)
    num_pages = models.IntegerField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.name}"


class Block(models.Model):
    content = models.TextField()
    page = models.IntegerField(default=1)
    document = models.ForeignKey(
        Document, on_delete=models.CASCADE, related_name="blocks"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="blocks")
    created_at = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Page {self.page} - {self.document.name}"
