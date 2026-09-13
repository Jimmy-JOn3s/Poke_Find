from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        PERSONAL = "personal", "Personal"
        BUSINESS = "business", "Business"

    class Language(models.TextChoices):
        THAI = "th", "Thai"
        ENGLISH = "en", "English"

    class Currency(models.TextChoices):
        THB = "THB", "Thai baht"
        USD = "USD", "US dollar"

    email = models.EmailField(unique=True)
    display_name = models.CharField(max_length=120)
    role = models.CharField(max_length=16, choices=Role.choices, default=Role.PERSONAL)
    preferred_language = models.CharField(max_length=2, choices=Language.choices, default=Language.THAI)
    preferred_currency = models.CharField(max_length=3, choices=Currency.choices, default=Currency.THB)
    avatar = models.ImageField(upload_to="avatars/", blank=True)
    location = models.CharField(max_length=120, blank=True)
    bio = models.TextField(blank=True)
    is_verified_seller = models.BooleanField(default=False)

    def __str__(self):
        return self.display_name or self.username

