from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("institucional/<slug:slug>/", views.pagina, name="pagina"),
    path("noticias/", views.noticia_lista, name="noticia-lista"),
    path("noticias/<slug:slug>/", views.noticia_detalhe, name="noticia-detalhe"),
    path("galerias/", views.galeria_lista, name="galeria-lista"),
    path("galerias/<slug:slug>/", views.galeria_detalhe, name="galeria-detalhe"),
]
