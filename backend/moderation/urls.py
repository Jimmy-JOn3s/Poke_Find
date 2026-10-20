from django.urls import path

from .views import AdminOverviewView, AdminReportDetailView, AdminReportListView, AdminUserListView, ReportCreateView


urlpatterns = [
    path("reports/", ReportCreateView.as_view(), name="report-create"),
    path("admin/overview/", AdminOverviewView.as_view(), name="admin-overview"),
    path("admin/users/", AdminUserListView.as_view(), name="admin-users"),
    path("admin/reports/", AdminReportListView.as_view(), name="admin-reports"),
    path("admin/reports/<int:pk>/", AdminReportDetailView.as_view(), name="admin-report-detail"),
]
