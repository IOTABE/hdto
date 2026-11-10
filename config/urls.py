from django.contrib import admin
from django.urls import include, path

from apps.core.views import health

urlpatterns = [
    path("admin/", admin.site.urls),
    path("contas/", include("apps.accounts.urls")),
    path("health/", health, name="health"),
]
