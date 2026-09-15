from pathlib import Path
from runpy import run_path
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock, patch


HELPER_PATH = Path(__file__).resolve().parents[2] / "docker-canteen"


class DeploymentHelperTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.helper = run_path(str(HELPER_PATH))

    def test_deploy_defaults_to_the_compose_ingress_network_name(self):
        self.assertEqual(self.helper["DEFAULT_INGRESS_NETWORK"], "ingress_default")

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
