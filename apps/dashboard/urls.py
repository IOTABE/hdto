from django.urls import path

from .views import indicadores

urlpatterns = [
    path("censo/indicadores/", indicadores, name="censo-indicadores"),
]
