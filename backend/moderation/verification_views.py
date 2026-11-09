import mimetypes

from django.http import FileResponse, Http404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.verification_models import VerificationSubmission
from accounts.verification_serializers import AdminVerificationReviewSerializer, AdminVerificationSerializer

from .permissions import IsStaffUser


class AdminVerificationListView(generics.ListAPIView):
    permission_classes = (IsStaffUser,)
    serializer_class = AdminVerificationSerializer

    def get_queryset(self):
        queryset = VerificationSubmission.objects.select_related("user")
        status_filter = self.request.query_params.get("status", "").strip()
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset


class AdminVerificationDetailView(generics.RetrieveAPIView):
    permission_classes = (IsStaffUser,)
    queryset = VerificationSubmission.objects.select_related("user")
    serializer_class = AdminVerificationSerializer


class AdminVerificationReviewView(APIView):
    permission_classes = (IsStaffUser,)

    def post(self, request, pk):
        submission = VerificationSubmission.objects.select_related("user").filter(pk=pk).first()
        if submission is None:
            raise Http404
        if submission.status != VerificationSubmission.Status.PENDING:
            return Response({"detail": "Only pending submissions can be reviewed."}, status=status.HTTP_400_BAD_REQUEST)
        serializer = AdminVerificationReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(submission=submission, reviewer=request.user)
        return Response(AdminVerificationSerializer(submission).data)


class AdminVerificationFileView(APIView):
    permission_classes = (IsStaffUser,)

    def get(self, request, pk, field):
        if field not in {"id_document", "selfie"}:
            raise Http404
        submission = VerificationSubmission.objects.filter(pk=pk).first()
        if submission is None:
            raise Http404
        file_field = getattr(submission, field)
        if not file_field:
            raise Http404
        content_type = mimetypes.guess_type(file_field.name)[0] or "application/octet-stream"
        return FileResponse(file_field.open("rb"), content_type=content_type)
