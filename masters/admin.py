from django.contrib import admin
from .models import (
    Driver,
    Vehicle,
    Client,
    MaintenanceJob,
    MaintenancePart,
    Vendor,
    Expense,
    City,
    Route,
)

# ================= DRIVER =================
admin.site.register(Driver)

# ================= CLIENT =================
admin.site.register(Client)

# ================= VENDOR =================
admin.site.register(Vendor)

# ================= EXPENSE =================
admin.site.register(Expense)

# ================= CITY =================
admin.site.register(City)

# ================= ROUTE =================
admin.site.register(Route)


# ================= VEHICLE =================
@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = (
        "vehicle_number",
        "vehicle_type",
        "vehicle_mode",
        "current_km",
        "is_active",
    )
    search_fields = ("vehicle_number",)
    list_filter = ("vehicle_type", "vehicle_mode", "is_active")


# ================= WORKSHOP: MAINTENANCE JOB =================
class MaintenancePartInline(admin.TabularInline):
    model = MaintenancePart
    extra = 1


@admin.register(MaintenanceJob)
class MaintenanceJobAdmin(admin.ModelAdmin):
    list_display = (
        "job_id",
        "vehicle",
        "maintenance_type",
        "date",
        "status",
        "total_cost",
        "vendor_payment_status",
    )
    list_filter = ("status", "maintenance_type", "vendor_payment_status")
    search_fields = ("job_id", "vehicle__vehicle_number")
    inlines = [MaintenancePartInline]
