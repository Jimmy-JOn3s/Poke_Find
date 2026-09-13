from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class PokeFindUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("PokeFind", {"fields": (
        "display_name", "role", "preferred_language", "preferred_currency",
        "avatar", "location", "bio", "is_verified_seller",
    )}),)
