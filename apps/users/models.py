from django.db import models
from django.utils import timezone


class User(models.Model):
    supabase_id = models.UUIDField(unique=True, db_index=True, null=True, blank=True)
    email = models.EmailField(blank=True, default="")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.email or self.supabase_id}"
