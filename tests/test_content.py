from datetime import timedelta

import pytest
from django.contrib import admin
from django.core import mail
from django.urls import reverse
from django.utils import timezone

from apps.content.models import (
    Contato,
    Galeria,
    Historia,
    MembroDiretoria,
    Noticia,
    PaginaInstitucional,
)
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


@pytest.fixture
def institucional(db):
    historia = Historia.objects.create(
        titulo="Raízes do trabalho masculino",
        resumo="Como o movimento chegou ao Tocantins.",
        conteudo="Conteúdo histórico.",
    )
    Historia.objects.create(titulo="Rascunho histórico", conteudo="Oculto", publicada=False)
    atual = MembroDiretoria.objects.create(
        nome="Carlos Andrade",
        cargo="Presidente",
        bienio_inicio=2024,
        bienio_fim=2025,
        email="carlos@example.com",
    )
    anterior = MembroDiretoria.objects.create(
        nome="João Batista",
        cargo="Presidente",
        bienio_inicio=2022,
        bienio_fim=2023,
    )
    return {"historia": historia, "atual": atual, "anterior": anterior}


@pytest.mark.django_db
def test_paginas_institucionais_exibem_conteudo(client, institucional):
    resposta = client.get(reverse("historia"))
    assert resposta.status_code == 200
    conteudo = resposta.content.decode()
    assert "Raízes do trabalho masculino" in conteudo
    assert "Rascunho histórico" not in conteudo

    resposta = client.get(reverse("diretoria"))
    assert resposta.status_code == 200
    conteudo = resposta.content.decode()
    assert "Gestão 2024–2025" in conteudo
    assert "Gestão 2022–2023" in conteudo
    assert "Gestão atual" in conteudo
    assert "Carlos Andrade" in conteudo
    assert "João Batista" in conteudo

    assert client.get(reverse("contato")).status_code == 200


@pytest.mark.django_db
def test_menu_superior_tem_institucional(client):
    conteudo = client.get(reverse("home")).content.decode()
    assert "Institucional" in conteudo
    for nome in ["historia", "diretoria", "contato"]:
        assert reverse(nome) in conteudo


@pytest.mark.django_db
def test_contato_registro_local(client, captcha_data):
    resposta = client.post(
        reverse("contato"),
        {
            "nome": "Maria Souza",
            "email": "",
            "telefone": "",
            "assunto": "Dúvida",
            "mensagem": "Olá, gostaria de mais informações.",
            "canal": Contato.Canal.LOCAL,
            **captcha_data,
        },
    )
    assert resposta.status_code == 302
    assert resposta.url == reverse("contato")
    contato = Contato.objects.get()
    assert contato.status == Contato.Status.REGISTRADO
    assert contato.canal == Contato.Canal.LOCAL
    assert contato.ip == "127.0.0.1"


@pytest.mark.django_db
def test_contato_por_email_envia(client, captcha_data, settings):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.CONTACT_EMAIL = "equipe@example.com"
    mail.outbox.clear()

    resposta = client.post(
        reverse("contato"),
        {
            "nome": "Maria Souza",
            "email": "maria@example.com",
            "telefone": "",
            "assunto": "Pedido de informação",
            "mensagem": "Mensagem por e-mail.",
            "canal": Contato.Canal.EMAIL,
            **captcha_data,
        },
    )
    assert resposta.status_code == 302
    contato = Contato.objects.get()
    assert contato.status == Contato.Status.ENVIADO
    assert contato.enviado_em is not None
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["equipe@example.com"]


@pytest.mark.django_db
def test_contato_email_com_falha_fica_registrado(client, captcha_data, settings, monkeypatch):
    settings.CONTACT_EMAIL = "equipe@example.com"

    def falhar(*args, **kwargs):
        raise OSError("SMTP indisponível")

    monkeypatch.setattr("apps.content.views.send_mail", falhar)
    resposta = client.post(
        reverse("contato"),
        {
            "nome": "Maria Souza",
            "email": "maria@example.com",
            "telefone": "",
            "assunto": "Pedido de informação",
            "mensagem": "Mensagem por e-mail.",
            "canal": Contato.Canal.EMAIL,
            **captcha_data,
        },
    )
    assert resposta.status_code == 302
    contato = Contato.objects.get()
    assert contato.status == Contato.Status.FALHA_ENVIO


@pytest.mark.django_db
def test_contato_por_whatsapp_redireciona(client, captcha_data, settings):
    settings.CONTACT_WHATSAPP = "+55 (63) 99999-9999"
    resposta = client.post(
        reverse("contato"),
        {
            "nome": "Maria Souza",
            "email": "",
            "telefone": "63999999999",
            "assunto": "WhatsApp",
            "mensagem": "Mensagem por WhatsApp.",
            "canal": Contato.Canal.WHATSAPP,
            **captcha_data,
        },
    )
    assert resposta.status_code == 302
    assert resposta.url.startswith("https://wa.me/5563999999999?text=")
    contato = Contato.objects.get()
    assert contato.canal == Contato.Canal.WHATSAPP


@pytest.mark.django_db
def test_contato_valida_campos_por_canal(client, captcha_data):
    resposta = client.post(
        reverse("contato"),
        {
            "nome": "Maria",
            "email": "",
            "telefone": "",
            "assunto": "Teste",
            "mensagem": "Mensagem",
            "canal": Contato.Canal.EMAIL,
            **captcha_data,
        },
    )
    assert resposta.status_code == 200
    assert "email" in resposta.context["form"].errors
    assert Contato.objects.count() == 0


@pytest.mark.django_db
def test_contato_exige_captcha(client):
    resposta = client.post(
        reverse("contato"),
        {
            "nome": "Maria",
            "email": "maria@example.com",
            "telefone": "",
            "assunto": "Teste",
            "mensagem": "Mensagem",
            "canal": Contato.Canal.LOCAL,
        },
    )
    assert resposta.status_code == 200
    assert "captcha" in resposta.context["form"].errors
    assert Contato.objects.count() == 0


def test_modelos_institucionais_no_admin():
    assert admin.site.is_registered(Historia)
    assert admin.site.is_registered(MembroDiretoria)
    assert admin.site.is_registered(Contato)
