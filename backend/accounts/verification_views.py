from rest_framework import permissions, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .verification_models import VerificationSubmission
from .verification_serializers import (
    VerificationSubmissionCreateSerializer,
    VerificationSubmissionStatusSerializer,
)


class VerificationSubmissionView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    parser_classes = (MultiPartParser, FormParser)

    def get(self, request):
        latest = VerificationSubmission.objects.filter(user=request.user).order_by("-created_at").first()
        if latest is None:
            return Response(status=200, data=None)
        return Response(VerificationSubmissionStatusSerializer(latest).data)

    def post(self, request):
        serializer = VerificationSubmissionCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        submission = serializer.save()
        return Response(
            VerificationSubmissionStatusSerializer(submission).data,
            status=status.HTTP_201_CREATED,
        )
