from django.db import models
from django.utils import timezone


class User(models.Model):
    clerk_id = models.CharField(
        max_length=255, unique=True, db_index=True, null=True, blank=True
    )
    email = models.EmailField(blank=True, default="")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.email or self.clerk_id}"

    @property
    def is_authenticated(self):
        """
        Always return True. This is a way to tell if the user has been authenticated.
        """
        return True

    @property
    def is_anonymous(self):
        """
        Always return False. This is a way to tell if the user is anonymous.
        """
        return False
