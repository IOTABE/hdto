from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("institucional/historia/", views.historia, name="historia"),
    path("institucional/diretoria/", views.diretoria, name="diretoria"),
    path("institucional/contato/", views.contato, name="contato"),
    path("institucional/<slug:slug>/", views.pagina, name="pagina"),
    path("noticias/", views.noticia_lista, name="noticia-lista"),
    path("noticias/<slug:slug>/", views.noticia_detalhe, name="noticia-detalhe"),
    path("galerias/", views.galeria_lista, name="galeria-lista"),
    path("galerias/<slug:slug>/", views.galeria_detalhe, name="galeria-detalhe"),
    path("gestao/conteudo/", views.gestao_conteudo, name="conteudo-painel"),
    path("gestao/conteudo/noticias/nova/", views.noticia_nova, name="noticia-nova"),
    path(
        "gestao/conteudo/noticias/<int:pk>/editar/",
        views.noticia_editar,
        name="noticia-editar",
    ),
    path(
        "gestao/conteudo/noticias/<int:pk>/excluir/",
        views.noticia_excluir,
        name="noticia-excluir",
    ),
    path("gestao/conteudo/galerias/nova/", views.galeria_nova, name="galeria-nova"),
    path(
        "gestao/conteudo/galerias/<slug:slug>/editar/",
        views.galeria_editar,
        name="galeria-editar",
    ),
    path(
        "gestao/conteudo/galerias/<slug:slug>/excluir/",
        views.galeria_excluir,
        name="galeria-excluir",
    ),
    path(
        "gestao/conteudo/galerias/<slug:slug>/fotos/nova/",
        views.foto_nova,
        name="foto-nova",
    ),
    path(
        "gestao/conteudo/fotos/<int:pk>/editar/",
        views.foto_editar,
        name="foto-editar",
    ),
    path(
        "gestao/conteudo/fotos/<int:pk>/excluir/",
        views.foto_excluir,
        name="foto-excluir",
    ),
    path("gestao/conteudo/historia/nova/", views.historia_nova, name="historia-nova"),
    path(
        "gestao/conteudo/historia/<int:pk>/editar/",
        views.historia_editar,
        name="historia-editar",
    ),
    path(
        "gestao/conteudo/historia/<int:pk>/excluir/",
        views.historia_excluir,
        name="historia-excluir",
    ),
    path("gestao/conteudo/diretoria/novo/", views.diretor_novo, name="diretor-novo"),
    path(
        "gestao/conteudo/diretoria/<int:pk>/editar/",
        views.diretor_editar,
        name="diretor-editar",
    ),
    path(
        "gestao/conteudo/diretoria/<int:pk>/excluir/",
        views.diretor_excluir,
        name="diretor-excluir",
    ),
]
