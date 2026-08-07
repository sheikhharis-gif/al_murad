from datetime import date, timedelta
from masters.models import Staff, MaintenanceJob

def license_expiry_alerts():
    today = date.today()
    warning_date = today + timedelta(days=30)

    return Staff.objects.filter(license_expiry__lte=warning_date)

def oil_change_alerts():
    return MaintenanceJob.objects.filter(
        maintenance_type="OIL"
    ).exclude(status="COMPLETED")
