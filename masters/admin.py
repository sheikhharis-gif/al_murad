from django.contrib import admin
from .models import (
    Driver,
    Vehicle,
    Client,
    VehicleMaintenance,
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


# ================= VEHICLE MAINTENANCE =================
@admin.register(VehicleMaintenance)
class VehicleMaintenanceAdmin(admin.ModelAdmin):
    list_display = (
        "vehicle",
        "maintenance_type",
        "change_km",
        "next_due_km",
        "change_date",
    )
    list_filter = ("maintenance_type",)
    search_fields = ("vehicle__vehicle_number",)
