from datetime import date, timedelta
from masters.models import Driver, VehicleMaintenance

def license_expiry_alerts():
    today = date.today()
    warning_date = today + timedelta(days=30)

    return Driver.objects.filter(license_expiry__lte=warning_date)

def oil_change_alerts():
    today = date.today()
    return VehicleMaintenance.objects.filter(
        maintenance_type="OIL",
        next_due_date__lte=today
    )
