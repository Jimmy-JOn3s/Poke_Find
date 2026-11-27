from django.test import TestCase
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView
from django.urls import resolve


class EchoVersionView(APIView):
    authentication_classes = ()
    permission_classes = ()
    throttle_classes = ()

    def get(self, request):
        return Response({"version": request.version})


class ApiVersioningTests(TestCase):
    def version_seen_at(self, path: str) -> str:
        request = APIRequestFactory().get(path)
        request.resolver_match = resolve(path)
        return EchoVersionView.as_view()(request).data["version"]

    def test_versioned_path_serves_the_api(self):
        self.assertEqual(self.client.get("/api/v1/health/").json(), {"status": "ok"})
        self.assertEqual(self.client.get("/api/v1/listings/").status_code, 200)

    def test_unversioned_path_still_works_for_existing_clients(self):
        self.assertEqual(self.client.get("/api/health/").json(), {"status": "ok"})
        self.assertEqual(self.client.get("/api/listings/").status_code, 200)

    def test_both_paths_resolve_to_the_same_view(self):
        for suffix in ("listings/", "auth/login/", "deals/", "admin/overview/", "market/variant/"):
            with self.subTest(suffix=suffix):
                self.assertIs(resolve(f"/api/v1/{suffix}").func.cls, resolve(f"/api/{suffix}").func.cls)

    def test_request_version_is_v1_on_both_paths(self):
        self.assertEqual(self.version_seen_at("/api/v1/listings/"), "v1")
        self.assertEqual(self.version_seen_at("/api/listings/"), "v1")

    def test_unknown_version_is_not_found(self):
        self.assertEqual(self.client.get("/api/v2/listings/").status_code, 404)
