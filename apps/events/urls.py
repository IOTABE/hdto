from django.urls import path

from .views import checkin, evento_ics, inscricao_qr

urlpatterns = [
    path("<int:pk>/ical/", evento_ics, name="evento-ics"),
    path("inscricoes/<int:pk>/qr/", inscricao_qr, name="inscricao-qr"),
    path("checkin/<uuid:token>/", checkin, name="evento-checkin"),
]
