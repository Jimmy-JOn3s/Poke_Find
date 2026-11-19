from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.verification_models import VerificationSubmission
from marketplace.models import Listing
from messaging.models import Conversation, Deal, Message, Offer, Review

from .actions import apply_report_action
from .market_intelligence import platform_market_intelligence
from .models import ContentReport
from .permissions import IsStaffUser
from .serializers import (
    AdminContentReportSerializer,
    AdminReportActionSerializer,
    AdminReportUpdateSerializer,
    AdminUserSerializer,
    ContentReportSerializer,
    ReportCreateSerializer,
)


User = get_user_model()

def admin_report_queryset():
    return ContentReport.objects.select_related(
        "reporter",
        "listing",
        "listing__seller",
        "reported_user",
        "message",
        "message__author",
        "message__conversation",
        "message__conversation__listing",
        "message__conversation__listing__seller",
        "resolved_by",
    )


class ReportCreateView(generics.CreateAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ReportCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        report = serializer.save()
        return Response(
            ContentReportSerializer(report).data,
            status=status.HTTP_201_CREATED,
        )


class AdminOverviewView(APIView):
    permission_classes = (IsStaffUser,)

    def get(self, request):
        users = User.objects.aggregate(
            total=Count("id"),
            personal=Count("id", filter=Q(role=User.Role.PERSONAL)),
            business=Count("id", filter=Q(role=User.Role.BUSINESS)),
            staff=Count("id", filter=Q(is_staff=True)),
        )
        listings = Listing.objects.aggregate(
            total=Count("id"),
            active=Count("id", filter=Q(status=Listing.Status.ACTIVE)),
            reserved=Count("id", filter=Q(status=Listing.Status.RESERVED)),
            sold=Count("id", filter=Q(status=Listing.Status.SOLD)),
        )
        messaging = {
            "conversations": Conversation.objects.count(),
            "messages": Message.objects.count(),
            "offers": Offer.objects.count(),
            "deals_completed": Deal.objects.filter(status=Deal.Status.COMPLETED).count(),
            "deals_active": Deal.objects.filter(status=Deal.Status.ACCEPTED).count(),
            "reviews": Review.objects.count(),
        }
        reports = ContentReport.objects.aggregate(
            total=Count("id"),
            pending=Count("id", filter=Q(status=ContentReport.Status.PENDING)),
            reviewing=Count("id", filter=Q(status=ContentReport.Status.REVIEWING)),
            resolved=Count("id", filter=Q(status=ContentReport.Status.RESOLVED)),
            dismissed=Count("id", filter=Q(status=ContentReport.Status.DISMISSED)),
        )
        verifications = VerificationSubmission.objects.aggregate(
            total=Count("id"),
            pending=Count("id", filter=Q(status=VerificationSubmission.Status.PENDING)),
        )
        by_reason = {
            row["reason"]: row["count"]
            for row in ContentReport.objects.values("reason").annotate(count=Count("id")).order_by("-count")
        }
        by_category = {
            row["category"]: row["count"]
            for row in ContentReport.objects.values("category").annotate(count=Count("id")).order_by("-count")
        }
        return Response({
            "users": users,
            "listings": listings,
            "messaging": messaging,
            "reports": reports,
            "verifications": verifications,
            "reports_by_reason": by_reason,
            "reports_by_category": by_category,
        })


class AdminUserListView(generics.ListAPIView):
    permission_classes = (IsStaffUser,)
    serializer_class = AdminUserSerializer

    def get_queryset(self):
        return User.objects.order_by("-date_joined")


class AdminMarketIntelligenceView(APIView):
    permission_classes = (IsStaffUser,)

    def get(self, request):
        return Response(platform_market_intelligence())


class AdminReportListView(generics.ListAPIView):
    permission_classes = (IsStaffUser,)
    serializer_class = AdminContentReportSerializer

    def get_queryset(self):
        queryset = admin_report_queryset()
        status_filter = self.request.query_params.get("status", "").strip()
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset


class AdminReportActionView(APIView):
    permission_classes = (IsStaffUser,)

    def post(self, request, pk):
        report = admin_report_queryset().filter(pk=pk).first()
        if report is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = AdminReportActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        action = serializer.validated_data["action"]
        mark_resolved = serializer.validated_data.get("mark_resolved", True)
        note_append = serializer.validated_data.get("admin_notes", "").strip()

        with transaction.atomic():
            report = admin_report_queryset().select_for_update().get(pk=pk)
            outcome = apply_report_action(report, action, request.user)
            if mark_resolved and report.status not in {
                ContentReport.Status.RESOLVED,
                ContentReport.Status.DISMISSED,
            }:
                report.status = ContentReport.Status.RESOLVED
                report.resolved_by = request.user
                report.resolved_at = timezone.now()
            if note_append:
                prefix = f"{report.admin_notes}\n\n" if report.admin_notes else ""
                report.admin_notes = f"{prefix}{note_append}"[:2000]
            elif mark_resolved and not report.admin_notes:
                report.admin_notes = outcome["detail"][:2000]
            report.save(update_fields=["status", "admin_notes", "resolved_by", "resolved_at", "updated_at"])

        report = admin_report_queryset().get(pk=pk)
        return Response({
            **outcome,
            "report": AdminContentReportSerializer(report).data,
        })


class AdminReportDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = (IsStaffUser,)
    queryset = admin_report_queryset()
    http_method_names = ("get", "patch", "head", "options")

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return AdminReportUpdateSerializer
        return AdminContentReportSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = AdminReportUpdateSerializer(instance, data=request.data, partial=partial, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        instance = admin_report_queryset().get(pk=instance.pk)
        return Response(AdminContentReportSerializer(instance).data)
