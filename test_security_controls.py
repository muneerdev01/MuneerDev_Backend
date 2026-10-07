"""Focused tests for file validation and API authentication boundaries."""

import unittest
import time
import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

from main import app
from models.download_token import DownloadToken, default_expiry
from routers.v1 import products, projects, webhooks
from utils.upload_validation import validate_upload


class UploadValidationTests(unittest.TestCase):
    def test_accepts_matching_allowed_signatures(self):
        samples = [
            ("photo.png", "image/png", b"\x89PNG\r\n\x1a\npayload", "image"),
            ("photo.jpg", "image/jpeg", b"\xff\xd8\xffpayload", "image"),
            ("photo.webp", "image/webp", b"RIFFxxxxWEBPpayload", "image"),
            ("product.pdf", "application/pdf", b"%PDF-1.7 payload", "product_file"),
            ("product.zip", "application/zip", b"PK\x03\x04payload", "product_file"),
        ]
        for filename, mime_type, content, kind in samples:
            with self.subTest(filename=filename):
                self.assertTrue(validate_upload(filename, mime_type, content, kind))

    def test_rejects_executable_and_mismatched_content(self):
        invalid = [
            ("malware.exe", "application/octet-stream", b"MZ\x00payload", "product_file"),
            ("image.png", "image/png", b"MZ\x00payload", "image"),
            ("image.png", "application/pdf", b"\x89PNG\r\n\x1a\npayload", "image"),
        ]
        for filename, mime_type, content, kind in invalid:
            with self.subTest(filename=filename, mime_type=mime_type):
                with self.assertRaises(HTTPException):
                    validate_upload(filename, mime_type, content, kind)


class AdminAuthorizationTests(unittest.TestCase):
    def test_product_write_requires_admin_bearer(self):
        client = TestClient(app)
        response = client.post("/api/products", json={})
        self.assertEqual(response.status_code, 401)

    def test_content_and_upload_mutations_require_admin_bearer(self):
        client = TestClient(app)
        checks = [
            client.post("/admin/articles/", json={}),
            client.put("/admin/articles/example", json={}),
            client.delete("/admin/articles/example"),
            client.put("/api/products/example", json={}),
            client.delete("/api/products/example"),
            client.post("/api/projects", json={}),
            client.put("/api/projects/example", json={}),
            client.delete("/api/projects/example"),
            client.post(
                "/api/upload",
                data={"file_type": "product_file"},
                files={"file": ("malware.exe", b"MZ", "application/octet-stream")},
            ),
            client.post(
                "/admin/media/upload",
                files={"file": ("malware.exe", b"MZ", "application/octet-stream")},
            ),
        ]
        self.assertTrue(all(response.status_code == 401 for response in checks))

    def test_article_admin_api_requires_admin_bearer(self):
        client = TestClient(app)
        response = client.get("/admin/articles/")
        self.assertEqual(response.status_code, 401)

    def test_security_headers_are_present(self):
        response = TestClient(app).get("/")
        self.assertEqual(response.headers["x-frame-options"], "DENY")
        self.assertEqual(response.headers["x-content-type-options"], "nosniff")
        self.assertEqual(
            response.headers["referrer-policy"],
            "strict-origin-when-cross-origin",
        )

    def test_unlisted_origin_is_not_granted_cors_access(self):
        response = TestClient(app).options(
            "/",
            headers={
                "Origin": "https://untrusted.example",
                "Access-Control-Request-Method": "GET",
            },
        )
        self.assertNotIn("access-control-allow-origin", response.headers)


class StripeWebhookSignatureTests(unittest.TestCase):
    def test_invalid_signature_is_rejected(self):
        with patch.object(webhooks, "STRIPE_WEBHOOK_SECRET", "whsec_test_placeholder"):
            response = TestClient(app).post(
                "/api/webhooks/stripe",
                content=b'{"type":"checkout.session.completed","data":{"object":{}}}',
                headers={"stripe-signature": f"t={int(time.time())},v1=invalid"},
            )
        self.assertEqual(response.status_code, 400)

    def test_missing_signature_is_rejected(self):
        with patch.object(webhooks, "STRIPE_WEBHOOK_SECRET", "whsec_test_placeholder"):
            response = TestClient(app).post("/api/webhooks/stripe", content=b"{}")
        self.assertEqual(response.status_code, 400)


class DownloadTokenTests(unittest.TestCase):
    def test_default_token_is_a_random_v4_uuid_with_24_hour_expiry(self):
        token = uuid.uuid4()
        self.assertEqual(token.version, 4)
        expiry = default_expiry()
        self.assertAlmostEqual(
            (expiry - datetime.now(timezone.utc)).total_seconds(),
            24 * 60 * 60,
            delta=2,
        )

    def test_expired_token_is_rejected_by_model(self):
        record = DownloadToken(
            order_id=1,
            token=uuid.uuid4(),
            expires_at=datetime.now(timezone.utc) - timedelta(seconds=1),
        )
        self.assertTrue(record.is_expired)


class PublicCatalogTests(unittest.TestCase):
    def test_missing_product_and_project_slugs_return_404(self):
        class EmptyResult:
            def scalar_one_or_none(self):
                return None

        class EmptyDatabase:
            async def execute(self, statement):
                return EmptyResult()

        async def override_db():
            yield EmptyDatabase()

        app.dependency_overrides[products.get_db] = override_db
        app.dependency_overrides[projects.get_db] = override_db
        client = TestClient(app)
        try:
            self.assertEqual(client.get("/api/products/missing").status_code, 404)
            self.assertEqual(client.get("/api/projects/missing").status_code, 404)
        finally:
            app.dependency_overrides.pop(products.get_db, None)
            app.dependency_overrides.pop(projects.get_db, None)

    def test_public_product_detail_does_not_expose_private_file_path(self):
        product = SimpleNamespace(
            id=12,
            title="Pattern",
            slug="pattern",
            description="A digital pattern product.",
            price="12.00",
            category="PATTERNS",
            preview_images=[],
            sales_count=0,
            file_path="patterns/private.zip",
            is_active=True,
        )

        class ProductResult:
            def scalar_one_or_none(self):
                return product

        class ProductDatabase:
            async def execute(self, statement):
                return ProductResult()

        async def override_db():
            yield ProductDatabase()

        app.dependency_overrides[products.get_db] = override_db
        try:
            response = TestClient(app).get("/api/products/pattern")
            self.assertEqual(response.status_code, 200)
            self.assertNotIn("file_path", response.json())
        finally:
            app.dependency_overrides.pop(products.get_db, None)


if __name__ == "__main__":
    unittest.main()
