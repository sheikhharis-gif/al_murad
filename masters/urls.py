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

    # VENDORS 
    path("vendors/", views.vendor_list, name="vendor_list"),
    path("vendors/add/", views.vendor_add, name="vendor_add"),
    path("vendors/edit/<int:vendor_id>/", views.vendor_edit, name="vendor_edit"),
    path("vendors/delete/<int:vendor_id>/", views.vendor_delete, name="vendor_delete"),
    # CLIENTS
    path("clients/", views.client_list, name="client_list"),
    path("clients/add/", views.client_add, name="client_add"),
    path("clients/<int:client_id>/rates/", views.client_rates, name="client_rates"),
    # ✅ Client Edit aur Delete ke missing paths yahan add kar diye hain
    path("clients/edit/<int:client_id>/", views.client_edit, name="client_edit"),
    path("clients/delete/<int:client_id>/", views.client_delete, name="client_delete"),

    # ================= EXPENSES =================
    path('', views.expense_sheet, name='expense_sheet'),          # /expenses/
    path('list/', views.expense_list, name='expense_list'),       # /expenses/list/
    path("expenses/edit/<int:expense_id>/", views.expense_edit, name="expense_edit"),
    path("expenses/delete/<int:expense_id>/", views.expense_delete, name="expense_delete"),
    
    path("locations/", views.locations_master, name="locations_master"),

    # SALARY
    path("salary/", views.salary_list, name="salary_list"),
    path("salary/add/", views.salary_add, name="salary_add"),
    path("salary/edit/<int:salary_id>/", views.salary_edit, name="salary_edit"),
    path("salary/delete/<int:salary_id>/", views.salary_delete, name="salary_delete"),
    path("salary/slip/<int:salary_id>/", views.salary_slip_pdf, name="salary_slip_pdf"),

]