from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.accounts.roles import Role
from apps.events.models import Evento, Inscricao
from apps.geo.models import Municipio
from apps.institutions.models import AssociacaoRegional, Igreja, Organizacao
from apps.members.models import Membro


def make_user(email, role, **extra):
    from django.contrib.auth.models import Group

    user = User.objects.create_user(email=email, password="x", full_name=email, **extra)
    user.groups.add(Group.objects.get(name=role.value))
    return user


@pytest.fixture
def cenario(db):
    assoc = AssociacaoRegional.objects.create(nome="Associação Norte", sigla="NORTE")
    municipio = Municipio.objects.create(nome="Palmas", codigo_ibge="1721000")
    igreja = Igreja.objects.create(
        associacao=assoc,
        municipio=municipio,
        cnpj="11222333000181",
        razao_social="PIB Palmas",
        status=Igreja.Status.HOMOLOGADA,
        homologado_em=timezone.now(),
    )
    org = Organizacao.objects.create(igreja=igreja, tipo=Organizacao.Tipo.HD)
    user = User.objects.create_user(email="membro@example.com", password="x", full_name="Membro")
    membro = Membro.objects.create(
        user=user,
        nome_completo="Membro Inscrito",
        cpf="52998224725",
        data_nascimento=timezone.localdate() - timedelta(days=365 * 30),
        status=Membro.Status.ATIVO,
    )
    membro.organizacoes.add(org)
    evento = Evento.objects.create(
        titulo="Congresso Estadual",
        tipo=Evento.Tipo.CONGRESSO,
        abrangencia=Evento.Abrangencia.ESTADUAL,
        inicio=timezone.now() + timedelta(days=10),
        fim=timezone.now() + timedelta(days=12),
        local_nome="Palmas",
    )
    return {"assoc": assoc, "igreja": igreja, "org": org, "user": user, "membro": membro, "evento": evento}


@pytest.mark.django_db
def test_evento_regional_exige_associacao(cenario):
    evento = Evento(
        titulo="Evento Regional",
        tipo=Evento.Tipo.SIMPOSIO,
        abrangencia=Evento.Abrangencia.REGIONAL,
        inicio=timezone.now(),
        fim=timezone.now() + timedelta(hours=1),
    )
    with pytest.raises(ValidationError) as exc:
        evento.full_clean()
    assert "associacao" in exc.value.message_dict


@pytest.mark.django_db
def test_evento_fim_anterior_ao_inicio(cenario):
    evento = Evento(
        titulo="Evento Inválido",
        tipo=Evento.Tipo.OUTRO,
        abrangencia=Evento.Abrangencia.ESTADUAL,
        inicio=timezone.now() + timedelta(days=1),
        fim=timezone.now(),
    )
    with pytest.raises(ValidationError) as exc:
        evento.full_clean()
    assert "fim" in exc.value.message_dict


@pytest.mark.django_db
def test_inscricao_unica(cenario):
    Inscricao.objects.create(evento=cenario["evento"], membro=cenario["membro"])
    with pytest.raises(IntegrityError):
        Inscricao.objects.create(evento=cenario["evento"], membro=cenario["membro"])


@pytest.mark.django_db
def test_token_gerado_automaticamente(cenario):
    inscricao = Inscricao.objects.create(evento=cenario["evento"], membro=cenario["membro"])
    assert inscricao.token is not None


@pytest.mark.django_db
def test_feed_ics(client, cenario):
    response = client.get(reverse("evento-ics", args=[cenario["evento"].pk]))
    assert response.status_code == 200
    assert response["Content-Type"].startswith("text/calendar")
    assert b"BEGIN:VCALENDAR" in response.content
    assert b"Congresso Estadual" in response.content


@pytest.mark.django_db
def test_qr_code_do_proprio_membro(client, cenario):
    inscricao = Inscricao.objects.create(evento=cenario["evento"], membro=cenario["membro"])
    client.force_login(cenario["user"])
    response = client.get(reverse("inscricao-qr", args=[inscricao.pk]))
    assert response.status_code == 200
    assert response["Content-Type"] == "image/png"
    assert response.content[:4] == b"\x89PNG"


@pytest.mark.django_db
def test_qr_code_de_outro_membro_negado(client, cenario):
    inscricao = Inscricao.objects.create(evento=cenario["evento"], membro=cenario["membro"])
    outro = make_user("outro@example.com", Role.MEMBRO)
    client.force_login(outro)
    assert client.get(reverse("inscricao-qr", args=[inscricao.pk])).status_code == 403


@pytest.mark.django_db
def test_checkin_por_diretor(client, cenario):
    inscricao = Inscricao.objects.create(evento=cenario["evento"], membro=cenario["membro"])
    diretor = make_user("diretor@example.com", Role.DIRETOR_LOCAL, igreja=cenario["igreja"])
    client.force_login(diretor)
    response = client.post(reverse("evento-checkin", args=[inscricao.token]))
    assert response.status_code == 200
    inscricao.refresh_from_db()
    assert inscricao.status == Inscricao.Status.PRESENTE
    assert inscricao.checkin_em is not None


@pytest.mark.django_db
def test_checkin_somente_post(client, cenario):
    inscricao = Inscricao.objects.create(evento=cenario["evento"], membro=cenario["membro"])
    diretor = make_user("diretor2@example.com", Role.DIRETOR_LOCAL, igreja=cenario["igreja"])
    client.force_login(diretor)
    assert client.get(reverse("evento-checkin", args=[inscricao.token])).status_code == 405


@pytest.mark.django_db
def test_checkin_de_inscricao_cancelada(client, cenario):
    inscricao = Inscricao.objects.create(
        evento=cenario["evento"], membro=cenario["membro"], status=Inscricao.Status.CANCELADA
    )
    diretor = make_user("diretor3@example.com", Role.DIRETOR_LOCAL, igreja=cenario["igreja"])
    client.force_login(diretor)
    response = client.post(reverse("evento-checkin", args=[inscricao.token]))
    assert response.status_code == 400
