from django.urls import path

from .verification_views import (
    AdminVerificationDetailView,
    AdminVerificationFileView,
    AdminVerificationListView,
    AdminVerificationReviewView,
)
from .deal_views import AdminExpireStaleDealsView, AdminForceCancelDealView, AdminOpenDealListView
from .views import (
    AdminMarketIntelligenceView,
    AdminOverviewView,
    AdminReportActionView,
    AdminReportDetailView,
    AdminReportListView,
    AdminUserListView,
    ReportCreateView,
)


urlpatterns = [
    path("reports/", ReportCreateView.as_view(), name="report-create"),
    path("admin/overview/", AdminOverviewView.as_view(), name="admin-overview"),
    path("admin/market-intelligence/", AdminMarketIntelligenceView.as_view(), name="admin-market-intelligence"),
    path("admin/deals/open/", AdminOpenDealListView.as_view(), name="admin-open-deals"),
    path("admin/deals/<int:pk>/force-cancel/", AdminForceCancelDealView.as_view(), name="admin-force-cancel-deal"),
    path("admin/deals/expire-stale/", AdminExpireStaleDealsView.as_view(), name="admin-expire-stale-deals"),
    path("admin/users/", AdminUserListView.as_view(), name="admin-users"),
    path("admin/reports/", AdminReportListView.as_view(), name="admin-reports"),
    path("admin/reports/<int:pk>/", AdminReportDetailView.as_view(), name="admin-report-detail"),
    path("admin/reports/<int:pk>/action/", AdminReportActionView.as_view(), name="admin-report-action"),
    path("admin/verifications/", AdminVerificationListView.as_view(), name="admin-verifications"),
    path("admin/verifications/<int:pk>/", AdminVerificationDetailView.as_view(), name="admin-verification-detail"),
    path("admin/verifications/<int:pk>/review/", AdminVerificationReviewView.as_view(), name="admin-verification-review"),
    path(
        "admin/verifications/<int:pk>/file/<str:field>/",
        AdminVerificationFileView.as_view(),
        name="admin-verification-file",
    ),
]
