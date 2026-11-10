from django.urls import path

from . import views

urlpatterns = [
    path("igrejas/nova/", views.igreja_nova, name="igreja-nova"),
    path("organizacoes/nova/", views.organizacao_nova, name="organizacao-nova"),
]
