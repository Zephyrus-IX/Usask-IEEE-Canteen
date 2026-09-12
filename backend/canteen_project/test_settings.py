import os

os.environ.setdefault(
    "DJANGO_SECRET_KEY",
    "test-only-secret-key-0123456789-ABCDEFGHIJKLMNOPQRSTUVWXYZ-abcdefghijk",
)
os.environ.setdefault("DJANGO_DEBUG", "0")

from .settings import *  # noqa: F403
