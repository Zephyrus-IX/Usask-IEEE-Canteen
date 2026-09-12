from django.core.exceptions import ImproperlyConfigured

INSECURE_SECRET_KEYS = {
    "",
    "change-me",
    "dev-only-insecure-secret-key",
}


def validate_secret_key(secret_key: str, debug: bool) -> None:
    """Fail closed when production would start with a weak application secret."""
    if debug:
        return
    if (
        secret_key in INSECURE_SECRET_KEYS
        or secret_key.startswith("replace-with-")
        or len(secret_key) < 50
    ):
        raise ImproperlyConfigured(
            "DJANGO_SECRET_KEY must be a random value containing at least 50 characters "
            "when DJANGO_DEBUG=0."
        )
