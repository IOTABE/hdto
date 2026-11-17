from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from apps.core.views import health
from apps.geo.views import mapa
from apps.members.views import membro_novo

urlpatterns = [
    path("admin/", admin.site.urls),
    path("captcha/", include("captcha.urls")),
    path("contas/", include("apps.accounts.urls")),
    path("conta/", include("apps.members.urls")),
    path("cadastro/membro/", membro_novo, name="membro-novo"),
    path("cadastros/", include("apps.institutions.urls")),
    path("api/", include("apps.dashboard.urls")),
    path("api/mapa/", include("apps.geo.urls")),
    path("eventos/", include("apps.events.urls")),
    path("mapa/", mapa, name="mapa"),
    path("health/", health, name="health"),
    path("", include("apps.content.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
