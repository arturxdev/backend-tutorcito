from django.db import models


class User(models.Model):
    email = models.EmailField()

    def __str__(self):
        return f"{self.email}"
