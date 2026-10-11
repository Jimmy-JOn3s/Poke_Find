from django.conf import settings
from rest_framework import serializers


def validate_upload_size(file):
    limit = settings.MAX_UPLOAD_BYTES
    if file.size > limit:
        raise serializers.ValidationError(f"File is too large; the limit is {limit // (1024 * 1024)} MB.")
