from django.utils import timezone
from rest_framework.exceptions import ValidationError

from accounts.models import User
from marketplace.models import Listing

from .models import ContentReport

REMOVED_MESSAGE_BODY = "[Message removed by moderation]"


def _listing_for_report(report: ContentReport) -> Listing | None:
    if report.listing_id:
        return report.listing
    if report.message_id:
        return report.message.conversation.listing
    return None


def _user_for_deactivation(report: ContentReport) -> User | None:
    if report.reported_user_id:
        return report.reported_user
    if report.listing_id:
        return report.listing.seller
    if report.message_id:
        return report.message.author
    return None


def apply_report_action(report: ContentReport, action: str, staff_user: User) -> dict:
    if action == "hide_listing":
        listing = _listing_for_report(report)
        if listing is None:
            raise ValidationError({"action": "This report has no listing to hide."})
        if listing.status == Listing.Status.HIDDEN:
            return {"action": action, "detail": "Listing was already hidden.", "listing_id": listing.id, "listing_status": listing.status}
        Listing.objects.filter(pk=listing.pk).update(status=Listing.Status.HIDDEN, updated_at=timezone.now())
        return {"action": action, "detail": "Listing hidden from discovery.", "listing_id": listing.id, "listing_status": Listing.Status.HIDDEN}

    if action == "deactivate_user":
        target = _user_for_deactivation(report)
        if target is None:
            raise ValidationError({"action": "This report has no user account to deactivate."})
        if target.id == staff_user.id:
            raise ValidationError({"action": "You cannot deactivate your own account."})
        if target.is_staff:
            raise ValidationError({"action": "Staff accounts cannot be deactivated from a report action."})
        if not target.is_active:
            return {"action": action, "detail": "User was already inactive.", "user_id": target.id, "is_active": False}
        User.objects.filter(pk=target.pk).update(is_active=False)
        return {"action": action, "detail": "User account deactivated.", "user_id": target.id, "is_active": False}

    if action == "remove_message":
        if report.message_id is None:
            raise ValidationError({"action": "This report has no message to remove."})
        message = report.message
        if message.body == REMOVED_MESSAGE_BODY:
            return {"action": action, "detail": "Message was already removed.", "message_id": message.id}
        message.body = REMOVED_MESSAGE_BODY
        message.save(update_fields=("body",))
        return {"action": action, "detail": "Message content removed.", "message_id": message.id}

    raise ValidationError({"action": "Unknown action."})