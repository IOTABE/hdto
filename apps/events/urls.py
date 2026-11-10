from django.urls import path

from .views import checkin, evento_detalhe, evento_ics, evento_lista, inscricao_qr

urlpatterns = [
    path("", evento_lista, name="evento-lista"),
    path("<int:pk>/", evento_detalhe, name="evento-detalhe"),
    path("<int:pk>/ical/", evento_ics, name="evento-ics"),
    path("inscricoes/<int:pk>/qr/", inscricao_qr, name="inscricao-qr"),
    path("checkin/<uuid:token>/", checkin, name="evento-checkin"),
]
