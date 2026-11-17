from django.urls import path

from .views import (
    checkin,
    evento_detalhe,
    evento_editar,
    evento_excluir,
    evento_ics,
    evento_lista,
    evento_novo,
    inscricao_nova,
    inscricao_qr,
)

urlpatterns = [
    path("", evento_lista, name="evento-lista"),
    path("novo/", evento_novo, name="evento-novo"),
    path("<int:pk>/", evento_detalhe, name="evento-detalhe"),
    path("<int:pk>/editar/", evento_editar, name="evento-editar"),
    path("<int:pk>/excluir/", evento_excluir, name="evento-excluir"),
    path("<int:pk>/inscrever/", inscricao_nova, name="evento-inscricao"),
    path("<int:pk>/ical/", evento_ics, name="evento-ics"),
    path("inscricoes/<int:pk>/qr/", inscricao_qr, name="inscricao-qr"),
    path("checkin/<uuid:token>/", checkin, name="evento-checkin"),
]
