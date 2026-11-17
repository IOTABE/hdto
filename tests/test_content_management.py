import io

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image

from apps.accounts.roles import Role
from apps.content.models import Foto, Galeria, Historia, MembroDiretoria, Noticia
from apps.events.models import Evento

User = get_user_model()


def make_user(email, role):
    user = User.objects.create_user(email=email, password="x", full_name=email)
    user.groups.add(Group.objects.get(name=role.value))
    return user


@pytest.fixture
def admin_estadual(db):
    return make_user("admin@example.com", Role.ADMIN_ESTADUAL)


@pytest.fixture
def membro_comum(db):
    return make_user("membro@example.com", Role.MEMBRO)


@pytest.fixture
def imagem_png():
    buffer = io.BytesIO()
    Image.new("RGB", (8, 8), color="navy").save(buffer, format="PNG")
    return SimpleUploadedFile(
        "foto.png", buffer.getvalue(), content_type="image/png"
    )


@pytest.mark.django_db
def test_gestao_de_conteudo_exige_login(client):
    response = client.get(reverse("conteudo-painel"))
    assert response.status_code == 302
    assert "/contas/login/" in response["Location"]


@pytest.mark.django_db
def test_gestao_de_conteudo_restrita_ao_perfil_autorizado(client, membro_comum):
    client.force_login(membro_comum)
    assert client.get(reverse("conteudo-painel")).status_code == 403
    assert client.get(reverse("noticia-nova")).status_code == 403
    assert client.get(reverse("evento-novo")).status_code == 403


@pytest.mark.django_db
def test_administrador_acessa_tela_de_gestao(client, admin_estadual):
    client.force_login(admin_estadual)
    response = client.get(reverse("conteudo-painel"))
    assert response.status_code == 200
    conteudo = response.content.decode()
    for nome in [
        "noticia-nova",
        "evento-novo",
        "galeria-nova",
        "historia-nova",
        "diretor-novo",
    ]:
        assert reverse(nome) in conteudo


@pytest.mark.django_db
def test_botoes_aparecem_conforme_perfil(client, admin_estadual):
    visitante = client.get(reverse("noticia-lista")).content.decode()
    assert reverse("noticia-nova") not in visitante

    client.force_login(admin_estadual)
    administrador = client.get(reverse("noticia-lista")).content.decode()
    assert reverse("noticia-nova") in administrador


@pytest.mark.django_db
def test_admin_inclui_noticia_com_slug_automatico(client, admin_estadual):
    client.force_login(admin_estadual)
    response = client.post(
        reverse("noticia-nova"),
        {
            "titulo": "Encontro Estadual 2026",
            "slug": "",
            "resumo": "Resumo",
            "conteudo": "Conteúdo",
            "autor": "Equipe",
            "publicada": "on",
            "publicada_em": "",
        },
    )
    assert response.status_code == 302
    noticia = Noticia.objects.get()
    assert noticia.slug == "encontro-estadual-2026"
    assert noticia.publicada is True
    assert noticia.publicada_em is not None


@pytest.mark.django_db
def test_admin_inclui_evento(client, admin_estadual):
    client.force_login(admin_estadual)
    response = client.post(
        reverse("evento-novo"),
        {
            "titulo": "Congresso 2026",
            "tipo": Evento.Tipo.CONGRESSO,
            "abrangencia": Evento.Abrangencia.ESTADUAL,
            "inicio": "2026-12-01T19:00",
            "fim": "2026-12-03T18:00",
            "local_nome": "Palmas",
            "descricao": "Programação",
            "capacidade": "200",
            "inscricoes_abertas": "on",
        },
    )
    assert response.status_code == 302
    evento = Evento.objects.get()
    assert evento.titulo == "Congresso 2026"
    assert response.url == reverse("evento-detalhe", args=[evento.pk])


@pytest.mark.django_db
def test_admin_inclui_galeria_e_foto(client, admin_estadual, imagem_png):
    client.force_login(admin_estadual)
    response = client.post(
        reverse("galeria-nova"),
        {
            "titulo": "Acampamento 2026",
            "slug": "",
            "descricao": "Registros",
            "publicada": "on",
        },
    )
    assert response.status_code == 302
    galeria = Galeria.objects.get()
    assert galeria.slug == "acampamento-2026"

    response = client.post(
        reverse("foto-nova", args=[galeria.slug]),
        {
            "galeria": galeria.pk,
            "imagem": imagem_png,
            "legenda": "Equipe reunida",
            "ordem": "1",
        },
    )
    assert response.status_code == 302
    assert Foto.objects.filter(galeria=galeria, legenda="Equipe reunida").exists()


@pytest.mark.django_db
def test_admin_inclui_historia_e_diretor(client, admin_estadual):
    client.force_login(admin_estadual)
    response = client.post(
        reverse("historia-nova"),
        {
            "titulo": "Primeiros anos",
            "resumo": "Origem do trabalho",
            "conteudo": "Conteúdo histórico",
            "publicada": "on",
            "ordem": "1",
        },
    )
    assert response.status_code == 302
    assert Historia.objects.filter(titulo="Primeiros anos").exists()

    response = client.post(
        reverse("diretor-novo"),
        {
            "nome": "Carlos Andrade",
            "cargo": "Presidente",
            "bienio_inicio": "2026",
            "bienio_fim": "2027",
            "bio": "Biografia",
            "email": "carlos@example.com",
            "telefone": "63999999999",
            "publicada": "on",
            "ordem": "1",
        },
    )
    assert response.status_code == 302
    assert MembroDiretoria.objects.filter(nome="Carlos Andrade").exists()


@pytest.mark.django_db
def test_superusuario_pode_gerir_conteudo(client):
    superuser = User.objects.create_superuser(
        email="super@example.com", password="x", full_name="Super"
    )
    client.force_login(superuser)
    assert client.get(reverse("conteudo-painel")).status_code == 200
