from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.content.models import Galeria, Noticia, PaginaInstitucional
from apps.events.models import Evento


@pytest.fixture
def conteudo(db):
    pagina = PaginaInstitucional.objects.create(
        slug="embaixadores-do-rei",
        titulo="Embaixadores do Rei",
        resumo="Construindo meninos para não remendar homens.",
        conteudo="História e compromisso dos Embaixadores do Rei.",
    )
    noticia = Noticia.objects.create(
        slug="congresso-2026",
        titulo="Congresso Estadual 2026",
        resumo="Inscrições abertas.",
        conteudo="Detalhes do congresso.",
        publicada=True,
        publicada_em=timezone.now(),
    )
    nao_publicada = Noticia.objects.create(
        slug="rascunho", titulo="Rascunho", publicada=False
    )
    galeria = Galeria.objects.create(slug="acampamento", titulo="Acampamento")
    evento = Evento.objects.create(
        titulo="Congresso Estadual",
        tipo=Evento.Tipo.CONGRESSO,
        inicio=timezone.now() + timedelta(days=5),
        fim=timezone.now() + timedelta(days=7),
        local_nome="Palmas",
    )
    return {
        "pagina": pagina,
        "noticia": noticia,
        "nao_publicada": nao_publicada,
        "galeria": galeria,
        "evento": evento,
    }


@pytest.mark.django_db
def test_home_exibe_noticias_e_eventos(client, conteudo):
    response = client.get(reverse("home"))
    assert response.status_code == 200
    assert "Congresso Estadual 2026" in response.content.decode()
    assert "Congresso Estadual" in response.content.decode()


@pytest.mark.django_db
def test_pagina_publicada_e_privada(client, conteudo):
    assert client.get(reverse("pagina", args=["embaixadores-do-rei"])).status_code == 200
    assert client.get(reverse("pagina", args=["inexistente"])).status_code == 404


@pytest.mark.django_db
def test_noticia_publicada_e_rascunho(client, conteudo):
    assert client.get(reverse("noticia-detalhe", args=["congresso-2026"])).status_code == 200
    assert client.get(reverse("noticia-detalhe", args=["rascunho"])).status_code == 404


@pytest.mark.django_db
def test_listagens_publicas(client, conteudo):
    for nome in ["noticia-lista", "galeria-lista", "evento-lista"]:
        assert client.get(reverse(nome)).status_code == 200
    assert client.get(reverse("galeria-detalhe", args=["acampamento"])).status_code == 200
    assert client.get(reverse("evento-detalhe", args=[conteudo["evento"].pk])).status_code == 200


@pytest.mark.django_db
def test_pagina_do_mapa(client):
    response = client.get(reverse("mapa"))
    assert response.status_code == 200
    assert b"leaflet" in response.content.lower()
