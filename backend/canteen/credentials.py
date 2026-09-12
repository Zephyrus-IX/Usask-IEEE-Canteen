import secrets

TEMPORARY_PASSWORD_LENGTH = 20
TEMPORARY_PASSWORD_ALPHABET = (
    "ABCDEFGHJKLMNPQRSTUVWXYZ"
    "abcdefghijkmnopqrstuvwxyz"
    "23456789"
    "!@#$%"
)


def generate_temporary_password() -> str:
    """Generate a high-entropy password without ambiguous characters."""
    return "".join(
        secrets.choice(TEMPORARY_PASSWORD_ALPHABET)
        for _ in range(TEMPORARY_PASSWORD_LENGTH)
    )
