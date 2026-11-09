from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User

from .analytics import business_analytics


class BusinessAnalyticsView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        if request.user.role != User.Role.BUSINESS:
            return Response({"detail": "Business accounts only."}, status=status.HTTP_403_FORBIDDEN)
        return Response(business_analytics(request.user))
