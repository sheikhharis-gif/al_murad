from django.urls import path
from . import views

urlpatterns = [

    # DRIVERS
    path("drivers/", views.driver_list, name="driver_list"),
    path("drivers/add/", views.driver_add, name="driver_add"),
    path("drivers/edit/<int:driver_id>/", views.driver_edit, name="driver_edit"),
    path("drivers/delete/<int:driver_id>/", views.driver_delete, name="driver_delete"),

    # VEHICLES
    path("vehicles/", views.vehicle_list, name="vehicle_list"),
    path("vehicles/add/", views.vehicle_add, name="vehicle_add"),
    path("vehicles/edit/<int:vehicle_id>/", views.vehicle_edit, name="vehicle_edit"),
    path("vehicles/delete/<int:vehicle_id>/", views.vehicle_delete, name="vehicle_delete"),

    # VEHICLE TYRES (separate page - pick a Vehicle #, rest auto-fills)
    path("vehicles/tyres/", views.vehicle_tyres_select, name="vehicle_tyres_select"),
    path("vehicles/<int:vehicle_id>/tyres/", views.vehicle_tyres, name="vehicle_tyres"),
    path("vehicles/<int:vehicle_id>/tyres/<int:tyre_id>/edit/", views.vehicle_tyre_edit, name="vehicle_tyre_edit"),
    path("vehicles/<int:vehicle_id>/tyres/<int:tyre_id>/delete/", views.vehicle_tyre_delete, name="vehicle_tyre_delete"),

    # VEHICLE PERMITS & COMPLIANCE (separate page - pick a Vehicle #, rest auto-fills)
    path("vehicles/permits/", views.vehicle_permits_select, name="vehicle_permits_select"),
    path("vehicles/<int:vehicle_id>/permits/", views.vehicle_permits, name="vehicle_permits"),

    # VEHICLE TYPE + WHEELER (admin-extensible registries, one shared page)
    path("vehicles/types-wheelers/", views.vehicle_type_wheeler_config, name="vehicle_type_wheeler_config"),
    path("vehicles/types/<int:type_id>/edit/", views.vehicle_type_edit, name="vehicle_type_edit"),
    path("vehicles/types/<int:type_id>/delete/", views.vehicle_type_delete, name="vehicle_type_delete"),
    path("vehicles/wheelers/<int:wheeler_id>/edit/", views.wheeler_edit, name="wheeler_edit"),
    path("vehicles/wheelers/<int:wheeler_id>/delete/", views.wheeler_delete, name="wheeler_delete"),

    # SUPPLIERS (Vendor model)
    path("vendors/", views.vendor_list, name="vendor_list"),
    path("vendors/add/", views.vendor_add, name="vendor_add"),
    path("vendors/edit/<int:vendor_id>/", views.vendor_edit, name="vendor_edit"),
    path("vendors/delete/<int:vendor_id>/", views.vendor_delete, name="vendor_delete"),
    path("vendors/types/", views.supplier_type_config, name="supplier_type_config"),
    path("vendors/types/<int:type_id>/edit/", views.supplier_type_edit, name="supplier_type_edit"),
    path("vendors/types/<int:type_id>/delete/", views.supplier_type_delete, name="supplier_type_delete"),
    # CLIENTS
    path("clients/", views.client_list, name="client_list"),
    path("clients/add/", views.client_add, name="client_add"),
    path("clients/<int:client_id>/rates/", views.client_rates, name="client_rates"),
    # ✅ Client Edit aur Delete ke missing paths yahan add kar diye hain
    path("clients/edit/<int:client_id>/", views.client_edit, name="client_edit"),
    path("clients/delete/<int:client_id>/", views.client_delete, name="client_delete"),
    path("clients/types/", views.client_type_config, name="client_type_config"),
    path("clients/types/<int:type_id>/edit/", views.client_type_edit, name="client_type_edit"),
    path("clients/types/<int:type_id>/delete/", views.client_type_delete, name="client_type_delete"),

    # ================= EXPENSES =================
    path('', views.expense_sheet, name='expense_sheet'),          # /expenses/
    path('list/', views.expense_list, name='expense_list'),       # /expenses/list/
    path("expenses/edit/<int:expense_id>/", views.expense_edit, name="expense_edit"),
    path("expenses/delete/<int:expense_id>/", views.expense_delete, name="expense_delete"),
    
    path("locations/", views.locations_master, name="locations_master"),
    path("locations/city/<int:city_id>/edit/", views.city_edit, name="city_edit"),
    path("locations/city/<int:city_id>/delete/", views.city_delete, name="city_delete"),
    path("locations/route/<int:route_id>/edit/", views.route_edit, name="route_edit"),
    path("locations/route/<int:route_id>/delete/", views.route_delete, name="route_delete"),

    # SALARY
    path("salary/", views.salary_list, name="salary_list"),
    path("salary/add/", views.salary_add, name="salary_add"),
    path("salary/edit/<int:salary_id>/", views.salary_edit, name="salary_edit"),
    path("salary/delete/<int:salary_id>/", views.salary_delete, name="salary_delete"),
    path("salary/slip/<int:salary_id>/", views.salary_slip_pdf, name="salary_slip_pdf"),

]