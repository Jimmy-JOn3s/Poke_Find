from django.contrib import admin

from .models import ContentReport


@admin.register(ContentReport)
class ContentReportAdmin(admin.ModelAdmin):
    list_display = ("id", "category", "reason", "status", "reporter", "created_at")
    list_filter = ("status", "category", "reason")
    search_fields = ("reporter__email", "reporter__display_name", "details", "admin_notes")
    readonly_fields = ("created_at", "updated_at", "resolved_at")
