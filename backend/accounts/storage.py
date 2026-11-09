from django.conf import settings
from django.core.files.storage import FileSystemStorage

# Not exposed via MEDIA_URL; staff-only download views serve these files.
private_media_storage = FileSystemStorage(location=settings.PRIVATE_MEDIA_ROOT)
