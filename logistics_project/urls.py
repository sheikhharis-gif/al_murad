from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),

    path("", include("operations.urls")),      # dashboard + trips
    path("expenses/", include("masters.urls")),  # 👈 EXPENSES PREFIX
]
