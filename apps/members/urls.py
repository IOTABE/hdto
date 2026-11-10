from django.urls import path

from . import views

urlpatterns = [
    path("perfil/", views.meu_perfil, name="meu-perfil"),
    path("revogar-consentimento/", views.revogar, name="revogar-consentimento"),
]
