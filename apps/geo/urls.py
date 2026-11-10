from django.urls import path

from .views import municipios, pontos

urlpatterns = [
    path("pontos/", pontos, name="mapa-pontos"),
    path("municipios/", municipios, name="mapa-municipios"),
]
