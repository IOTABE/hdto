from django.contrib import admin
from django.urls import include, path

from apps.core.views import health
from apps.geo.views import mapa

urlpatterns = [
    path("admin/", admin.site.urls),
    path("contas/", include("apps.accounts.urls")),
    path("api/", include("apps.dashboard.urls")),
    path("api/mapa/", include("apps.geo.urls")),
    path("eventos/", include("apps.events.urls")),
    path("mapa/", mapa, name="mapa"),
    path("health/", health, name="health"),
    path("", include("apps.content.urls")),
]
