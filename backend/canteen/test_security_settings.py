from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from canteen.security import validate_secret_key


class ProductionSecuritySettingsTests(SimpleTestCase):
    def test_production_rejects_missing_placeholder_and_short_secret_keys(self):
        for secret_key in ("", "change-me", "dev-only-insecure-secret-key", "short-random-key"):
            with self.subTest(secret_key=secret_key):
                with self.assertRaises(ImproperlyConfigured):
                    validate_secret_key(secret_key, debug=False)

    def test_production_accepts_long_secret_key(self):
        validate_secret_key("a-long-random-production-key-0123456789-ABCDEFGHIJKLMNOPQRSTUVWXYZ", debug=False)

    def test_proxy_https_and_secure_cookie_switches_are_configured(self):
        self.assertIsNone(settings.SECURE_PROXY_SSL_HEADER)
        self.assertTrue(hasattr(settings, "SESSION_COOKIE_SECURE"))
        self.assertTrue(hasattr(settings, "CSRF_COOKIE_SECURE"))
        self.assertTrue(hasattr(settings, "SECURE_SSL_REDIRECT"))
        self.assertEqual(settings.AXES_CLIENT_IP_CALLABLE, "canteen.client_ip.get_client_ip")

    def test_whitenoise_serves_collected_static_files(self):
        self.assertIn(
            "whitenoise.middleware.WhiteNoiseMiddleware",
            settings.MIDDLEWARE,
        )
        self.assertEqual(
            settings.STORAGES["staticfiles"]["BACKEND"],
            "whitenoise.storage.CompressedStaticFilesStorage",
        )
