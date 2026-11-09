from django.utils import timezone
from django.core.validators import validate_image_file_extension
from rest_framework import serializers

from common.validators import validate_upload_size

from .models import User
from .verification_models import VerificationSubmission


class VerificationSubmissionStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = VerificationSubmission
        fields = ("id", "document_type", "status", "rejection_reason", "created_at", "reviewed_at")
        read_only_fields = fields


class VerificationSubmissionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = VerificationSubmission
        fields = ("document_type", "id_document", "selfie")

    def validate_id_document(self, file):
        validate_image_file_extension(file)
        validate_upload_size(file)
        return file

    def validate_selfie(self, file):
        if file is None:
            return file
        validate_image_file_extension(file)
        validate_upload_size(file)
        return file

    def validate(self, attrs):
        user = self.context["request"].user
        if not user.is_email_verified:
            raise serializers.ValidationError("Verify your email before submitting identity documents.")
        if user.is_verified_seller:
            raise serializers.ValidationError("Your seller identity is already verified.")
        if VerificationSubmission.objects.filter(user=user, status=VerificationSubmission.Status.PENDING).exists():
            raise serializers.ValidationError("You already have a submission under review.")
        doc_type = attrs.get("document_type")
        if doc_type not in {VerificationSubmission.DocumentType.ID, VerificationSubmission.DocumentType.PASSPORT}:
            raise serializers.ValidationError({"document_type": "Choose id or passport."})
        return attrs

    def create(self, validated_data):
        return VerificationSubmission.objects.create(user=self.context["request"].user, **validated_data)


class AdminVerificationSerializer(serializers.ModelSerializer):
    user_display_name = serializers.CharField(source="user.display_name", read_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)
    has_selfie = serializers.SerializerMethodField()

    class Meta:
        model = VerificationSubmission
        fields = (
            "id", "document_type", "status", "user_display_name", "user_email",
            "admin_notes", "rejection_reason", "has_selfie",
            "reviewed_at", "created_at", "updated_at",
        )
        read_only_fields = (
            "id", "document_type", "status", "user_display_name", "user_email",
            "has_selfie", "reviewed_at", "created_at", "updated_at",
        )

    def get_has_selfie(self, obj):
        return bool(obj.selfie)


class AdminVerificationReviewSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=("approve", "reject"))
    admin_notes = serializers.CharField(required=False, allow_blank=True, max_length=2000)
    rejection_reason = serializers.CharField(required=False, allow_blank=True, max_length=1000)

    def validate(self, attrs):
        if attrs["action"] == "reject" and not (attrs.get("rejection_reason") or "").strip():
            raise serializers.ValidationError({"rejection_reason": "Tell the user why the submission was rejected."})
        return attrs

    def save(self, *, submission: VerificationSubmission, reviewer: User):
        action = self.validated_data["action"]
        notes = (self.validated_data.get("admin_notes") or "").strip()
        submission.admin_notes = notes
        submission.reviewed_by = reviewer
        submission.reviewed_at = timezone.now()

        if action == "approve":
            submission.status = VerificationSubmission.Status.APPROVED
            submission.rejection_reason = ""
            submission.save()
            user = submission.user
            user.is_verified_seller = True
            user.seller_verification_type = submission.document_type
            user.save(update_fields=["is_verified_seller", "seller_verification_type"])
        else:
            submission.status = VerificationSubmission.Status.REJECTED
            submission.rejection_reason = self.validated_data["rejection_reason"].strip()
            submission.save()
        return submission
