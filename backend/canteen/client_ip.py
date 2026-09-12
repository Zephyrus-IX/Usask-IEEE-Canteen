from ipaddress import ip_address

from django.conf import settings


def get_client_ip(request):
    """Return a lockout key IP, trusting Cloudflare only in tunnel mode."""
    socket_ip = request.META.get("REMOTE_ADDR")
    if not settings.CANTEEN_TRUST_CLOUDFLARE_IP:
        return socket_ip

    connecting_ip = request.META.get("HTTP_CF_CONNECTING_IP", "").strip()
    try:
        return str(ip_address(connecting_ip))
    except ValueError:
        return socket_ip
