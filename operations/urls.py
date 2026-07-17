from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("dashboard/", views.dashboard, name="dashboard"),

    # --- TRIPS ---
    path("trips/", views.trip_list, name="trip_list"),
    path("trips/export/", views.trips_excel, name="trips_excel"),
    path("trips/export/pdf/", views.trips_pdf, name="trips_pdf"),
    path("trips/add/", views.trip_add, name="trip_add"),
    path("trips/edit/<int:trip_id>/", views.trip_edit, name="trip_edit"),
    path("trips/delete/<int:trip_id>/", views.trip_delete, name="trip_delete"),

    # --- JOBS ---
    path("jobs/", views.job_list, name="job_list"),
    path("jobs/completed/", views.completed_job_list, name="completed_job_list"),
    path("jobs/add/", views.job_add, name="job_add"),
    path("jobs/edit/<int:job_id>/", views.job_edit, name="job_edit"),
    path("jobs/delete/<int:job_id>/", views.job_delete, name="job_delete"),
    path("jobs/complete/<int:job_id>/", views.job_complete, name="job_complete"),
    # Job ke andar ki saari trips dekhne ke liye (Optional par behtar hai)
    path("jobs/<int:job_id>/view-trips/", views.job_view_trips, name="job_view_trips"),

    # --- MAINTENANCE ---
    path("maintenance/", views.maintenance_list, name="maintenance_list"),
    path("maintenance/add/", views.maintenance_add, name="maintenance_add"),

    # --- PDF GENERATION (UPDATED) ---
    # Purana Trip PDF band, ab Job-based Invoice chalayenge
    path("jobs/invoice/<int:job_id>/", views.job_invoice_pdf, name="job_invoice_pdf"),
]