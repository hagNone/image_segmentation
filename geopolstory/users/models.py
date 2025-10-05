from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user with minimal additions for digests.

    We keep Django's default username authentication for simplicity. Email is
    unique to avoid duplicates. Users can opt into daily digests and choose a
    timezone (default IST).
    """

    email = models.EmailField(unique=True, blank=False)
    is_subscribed = models.BooleanField(default=True)
    timezone = models.CharField(max_length=64, default="Asia/Kolkata")

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.username or self.email

