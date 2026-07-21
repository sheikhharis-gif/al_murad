from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import redirect
from django.urls import Resolver404, resolve

# Each restricted group maps to the url_names its members may reach and the
# url_name they get bounced back to when they stray outside that set.
RESTRICTED_GROUPS = {
    "Expense Only": {
        "allowed": {"expense_sheet", "expense_list", "expense_edit", "expense_delete", "logout"},
        "home": "expense_list",
    },
    "Workshop Only": {
        "allowed": {
            "maintenance_list", "maintenance_add", "maintenance_edit", "maintenance_delete",
            "logout",
        },
        "home": "maintenance_list",
    },
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


class RestrictedGroupMiddleware:
    """Users in one of RESTRICTED_GROUPS may only reach that group's allowed pages."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user
        if user.is_authenticated and not user.is_superuser and not _is_public_path(request.path_info):
            user_group_names = set(user.groups.values_list("name", flat=True))
            memberships = user_group_names & RESTRICTED_GROUPS.keys()
            if memberships:
                allowed = set()
                for name in memberships:
                    allowed |= RESTRICTED_GROUPS[name]["allowed"]
                try:
                    match = resolve(request.path_info)
                except Resolver404:
                    match = None
                if match is None or match.url_name not in allowed:
                    home = RESTRICTED_GROUPS[next(iter(memberships))]["home"]
                    return redirect(home)
        return self.get_response(request)
