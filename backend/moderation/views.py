from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from marketplace.models import Listing
from messaging.models import Conversation, Deal, Message, Offer, Review

from .models import ContentReport
from .permissions import IsStaffUser
from .serializers import (
    AdminReportUpdateSerializer,
    AdminUserSerializer,
    ContentReportSerializer,
    ReportCreateSerializer,
)


User = get_user_model()


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
            "reports_by_reason": by_reason,
            "reports_by_category": by_category,
        })


class AdminUserListView(generics.ListAPIView):
    permission_classes = (IsStaffUser,)
    serializer_class = AdminUserSerializer

    def get_queryset(self):
        return User.objects.order_by("-date_joined")


class AdminReportListView(generics.ListAPIView):
    permission_classes = (IsStaffUser,)
    serializer_class = ContentReportSerializer

    def get_queryset(self):
        queryset = ContentReport.objects.select_related(
            "reporter", "listing", "reported_user", "message", "resolved_by",
        )
        status_filter = self.request.query_params.get("status", "").strip()
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset


class AdminReportDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = (IsStaffUser,)
    queryset = ContentReport.objects.select_related(
        "reporter", "listing", "reported_user", "message", "resolved_by",
    )
    http_method_names = ("get", "patch", "head", "options")

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return AdminReportUpdateSerializer
        return ContentReportSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = AdminReportUpdateSerializer(instance, data=request.data, partial=partial, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ContentReportSerializer(instance).data)
