from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class UserIdentifierPasswordValidator:
    """Reject passwords containing the user's NSID or profile names."""

    def validate(self, password, user=None):
        if user is None:
            return

        normalized_password = password.casefold()
        identifiers = (
            getattr(user, "username", ""),
            getattr(user, "first_name", ""),
            getattr(user, "last_name", ""),
        )
        if any(value and len(value) >= 3 and value.casefold() in normalized_password for value in identifiers):
            raise ValidationError(
                _("This password is too similar to or contains your personal information."),
                code="password_contains_identifier",
            )

    def get_help_text(self):
        return _("Your password cannot contain your NSID or name.")
