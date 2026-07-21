import datetime as dt

from django.db.models import Q

from masters.models import Vehicle


def fleet_alerts(request):
    """Provide fleet alert data globally for header notifications."""
    if not request.user.is_authenticated:
        return {"critical_vehicles": []}

    today = dt.date.today()
    warning_limit = today + dt.timedelta(days=15)

    critical_vehicles = Vehicle.objects.filter(
        Q(sindh_permit_expiry__lte=warning_limit)
        | Q(punjab_permit_expiry__lte=warning_limit)
        | Q(kpk_permit_expiry__lte=warning_limit)
        | Q(balochistan_permit_expiry__lte=warning_limit)
        | Q(fitness_expiry_sindh__lte=warning_limit)
        | Q(fitness_expiry_punjab__lte=warning_limit)
        | Q(fitness_expiry_kpk__lte=warning_limit)
        | Q(fitness_expiry_balochistan__lte=warning_limit)
    ).distinct()[:10]

    return {"critical_vehicles": critical_vehicles}


def access_flags(request):
    """Expose role flags to templates, e.g. to hide nav links for restricted users."""
    if not request.user.is_authenticated or request.user.is_superuser:
        return {"is_expense_only": False, "is_workshop_only": False}

    user_groups = set(request.user.groups.values_list("name", flat=True))
    return {
        "is_expense_only": "Expense Only" in user_groups,
        "is_workshop_only": "Workshop Only" in user_groups,
    }
