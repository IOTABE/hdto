from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.geo.models import Municipio
from apps.institutions.models import AssociacaoRegional, Igreja, Organizacao
from apps.members.models import Consentimento, Membro, RevogacaoConsentimento, TermoVersao


@pytest.fixture
def membro_com_consentimento(db):
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
    org = Organizacao.objects.create(igreja=igreja, tipo=Organizacao.Tipo.SMHB)
    termo, _ = TermoVersao.objects.get_or_create(versao="1.0", defaults={"texto": "Termo"})
    user = User.objects.create_user(
        email="titular@example.com", password="x", full_name="Titular"
    )
    membro = Membro.objects.create(
        user=user,
        nome_completo="Titular dos Dados",
        cpf="52998224725",
        data_nascimento=timezone.localdate() - timedelta(days=365 * 30),
        email="titular@example.com",
        telefone="63999999999",
        endereco="Quadra 1",
        status=Membro.Status.ATIVO,
    )
    membro.organizacoes.add(org)
    membro.registrar_consentimento(ip="127.0.0.1")
    return {"user": user, "membro": membro, "termo": termo, "org": org}


@pytest.mark.django_db
def test_perfil_exige_login(client):
    response = client.get(reverse("meu-perfil"))
    assert response.status_code == 302


@pytest.mark.django_db
def test_perfil_exibe_dados(client, membro_com_consentimento):
    client.force_login(membro_com_consentimento["user"])
    response = client.get(reverse("meu-perfil"))
    assert response.status_code == 200
    assert b"Titular dos Dados" in response.content


@pytest.mark.django_db
def test_revogacao_exige_post(client, membro_com_consentimento):
    client.force_login(membro_com_consentimento["user"])
    response = client.get(reverse("revogar-consentimento"))
    assert response.status_code == 405


@pytest.mark.django_db
def test_revogacao_anonimiza_dados(client, membro_com_consentimento):
    membro = membro_com_consentimento["membro"]
    user = membro_com_consentimento["user"]
    client.force_login(user)

    response = client.post(reverse("revogar-consentimento"), {"motivo": "Direito do titular"})
    assert response.status_code == 200

    membro.refresh_from_db()
    user.refresh_from_db()
    assert membro.nome_completo == "Titular anonimizado"
    assert membro.email == ""
    assert membro.telefone == ""
    assert membro.endereco == ""
    assert membro.status == Membro.Status.INATIVO
    assert not user.is_active
    assert RevogacaoConsentimento.objects.filter(membro=membro).count() == 1
    assert Consentimento.objects.filter(membro=membro).count() == 1


@pytest.mark.django_db
def test_revogacao_imutavel(membro_com_consentimento):
    from apps.members.services import revogar_consentimento

    revogacao = revogar_consentimento(membro_com_consentimento["membro"], ip="127.0.0.1")
    with pytest.raises(ValidationError):
        revogacao.motivo = "outro"
        revogacao.save()
    with pytest.raises(ValidationError):
        revogacao.delete()


@pytest.mark.django_db
def test_cabecalho_csp(client, db):
    response = client.get(reverse("home"))
    assert "Content-Security-Policy" in response.headers
    assert "default-src 'self'" in response.headers["Content-Security-Policy"]
