from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import redirect
from django.urls import Resolver404, resolve

EXPENSE_ONLY_GROUP = "Expense Only"

# url_names an "Expense Only" user is allowed to reach.
EXPENSE_ONLY_ALLOWED_URL_NAMES = {
    "expense_sheet",
    "expense_list",
    "expense_edit",
    "expense_delete",
    "logout",
}


def _is_public_path(path):
    return (
        path.startswith(settings.STATIC_URL)
        or path.startswith("/accounts/")
        or path.startswith("/admin/")
    )


class LoginRequiredMiddleware:
    """Every page requires login except the auth/admin/static paths."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated and not _is_public_path(request.path_info):
            return redirect_to_login(request.get_full_path())
        return self.get_response(request)


class RestrictExpenseUserMiddleware:
    """Users in the 'Expense Only' group may only reach expense management pages."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user
        if (
            user.is_authenticated
            and not user.is_superuser
            and not _is_public_path(request.path_info)
            and user.groups.filter(name=EXPENSE_ONLY_GROUP).exists()
        ):
            try:
                match = resolve(request.path_info)
            except Resolver404:
                match = None
            if match is None or match.url_name not in EXPENSE_ONLY_ALLOWED_URL_NAMES:
                return redirect("expense_list")
        return self.get_response(request)
