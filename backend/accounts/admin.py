from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User
from .verification_models import VerificationSubmission


@admin.register(User)
class PokeFindUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("PokeFind", {"fields": (
        "display_name", "role", "preferred_language", "preferred_currency",
        "avatar", "location", "bio", "is_email_verified", "is_verified_seller", "seller_verification_type",
    )}),)


@admin.register(VerificationSubmission)
class VerificationSubmissionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "document_type", "status", "created_at", "reviewed_at")
    list_filter = ("status", "document_type")
    search_fields = ("user__email", "user__display_name")
    readonly_fields = ("user", "document_type", "id_document", "selfie", "created_at", "updated_at", "reviewed_by", "reviewed_at")
