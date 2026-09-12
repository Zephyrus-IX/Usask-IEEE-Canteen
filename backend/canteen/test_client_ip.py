from importlib import import_module

from django.test import RequestFactory, SimpleTestCase, override_settings


class ClientIpTests(SimpleTestCase):
    def setUp(self):
        self.get_client_ip = import_module("canteen.client_ip").get_client_ip
        self.request_factory = RequestFactory()

    @override_settings(CANTEEN_TRUST_CLOUDFLARE_IP=False)
    def test_direct_lan_mode_uses_socket_source_ip(self):
        request = self.request_factory.get(
            "/accounts/login/",
            HTTP_CF_CONNECTING_IP="203.0.113.10",
            REMOTE_ADDR="192.0.2.20",
        )

        self.assertEqual(self.get_client_ip(request), "192.0.2.20")

    @override_settings(CANTEEN_TRUST_CLOUDFLARE_IP=True)
    def test_tunnel_mode_uses_cloudflare_connecting_ip(self):
        request = self.request_factory.get(
            "/accounts/login/",
            HTTP_CF_CONNECTING_IP="203.0.113.10",
            REMOTE_ADDR="172.18.0.4",
        )

        self.assertEqual(self.get_client_ip(request), "203.0.113.10")
