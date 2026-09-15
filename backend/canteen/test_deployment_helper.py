from pathlib import Path
from runpy import run_path
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock, patch


HELPER_PATH = Path(__file__).resolve().parents[2] / "docker-canteen"
REPO_PATH = HELPER_PATH.parent


class DeploymentHelperTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.helper = run_path(str(HELPER_PATH))

    def test_deploy_defaults_to_the_compose_ingress_network_name(self):
        self.assertEqual(self.helper["DEFAULT_INGRESS_NETWORK"], "ingress_default")

    def test_deploy_exposes_a_separate_http_service_on_ipv4_loopback_only(self):
        compose = (REPO_PATH / "compose.deploy.yaml").read_text()

        self.assertIn("web-local:", compose)
        self.assertIn('127.0.0.1:8000:8000', compose)
        self.assertIn('DJANGO_ALLOWED_HOSTS: "localhost,127.0.0.1,[::1]"', compose)
        self.assertIn('DJANGO_SECURE_COOKIES: "0"', compose)
        self.assertIn('DJANGO_SECURE_SSL_REDIRECT: "0"', compose)
        self.assertIn('CANTEEN_SKIP_MIGRATIONS: "1"', compose)
        self.assertIn("condition: service_healthy", compose)
        entrypoint = (REPO_PATH / "backend" / "docker-entrypoint.sh").read_text()
        self.assertIn("CANTEEN_SKIP_MIGRATIONS", entrypoint)
        base_compose = (REPO_PATH / "compose.yaml").read_text()
        self.assertIn("healthcheck:", base_compose)

    def test_deploy_rejects_a_missing_shared_ingress_network(self):
        ensure_ingress_network = self.helper["ensure_ingress_network"]
        create_network = Mock()

        with (
            patch("subprocess.run", return_value=SimpleNamespace(returncode=1)),
            patch.dict(ensure_ingress_network.__globals__, {"run": create_network}),
            self.assertRaises(SystemExit),
        ):
            ensure_ingress_network(
                {"mode": "deploy", "ingress_network": "missing", "repo": "/tmp"},
                dry_run=False,
            )

        create_network.assert_not_called()
