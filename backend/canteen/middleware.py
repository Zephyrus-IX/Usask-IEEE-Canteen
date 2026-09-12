from django.shortcuts import redirect


class RequireCustomerPasswordChangeMiddleware:
    """Keep customers with temporary credentials inside password setup."""

    exempt_url_names = {"login", "logout", "set-password"}

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        user = request.user
        if not user.is_authenticated or user.is_staff:
            return None
        resolver_match = request.resolver_match
        if resolver_match and resolver_match.url_name in self.exempt_url_names:
            return None
        try:
            account = user.canteen_account
        except AttributeError:
            return None
        if account.must_change_password:
            return redirect("set-password")
        return None
