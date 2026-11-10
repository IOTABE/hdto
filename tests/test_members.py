from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection
from django.utils import timezone

from apps.accounts.models import User
from apps.geo.models import Municipio
from apps.institutions.models import AssociacaoRegional, Igreja, Organizacao
from apps.members.models import Consentimento, Membro, ResponsavelLegal, TermoVersao

CPF_ADULTO = "52998224725"
CPF_MENOR = "11144477735"
CPF_RESPONSAVEL = "12345678909"


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
    org = Organizacao.objects.create(igreja=igreja, tipo=Organizacao.Tipo.SMHB)
    termo = TermoVersao.objects.create(versao="1.0", texto="Consinto com o tratamento dos dados.")
    return {"igreja": igreja, "org": org, "termo": termo}


def criar_membro(nome, cpf, idade, **extra):
    return Membro.objects.create(
        nome_completo=nome,
        cpf=cpf,
        data_nascimento=timezone.localdate() - timedelta(days=365 * idade),
        **extra,
    )


@pytest.mark.django_db
def test_cpf_validator():
    from apps.core.validators import validate_cpf

    validate_cpf(CPF_ADULTO)
    with pytest.raises(ValidationError):
        validate_cpf("12345678900")


@pytest.mark.django_db
def test_cpf_armazenado_cifrado_e_hash_consistente(cenario):
    membro = criar_membro("João Adulto", CPF_ADULTO, 30)
    membro.organizacoes.add(cenario["org"])
    assert membro.cpf == CPF_ADULTO
    with connection.cursor() as cursor:
        cursor.execute("SELECT cpf, cpf_hash FROM members_membro WHERE id = %s", [membro.pk])
        raw_cpf, raw_hash = cursor.fetchone()
    assert raw_cpf != CPF_ADULTO
    assert len(raw_hash) == 64


@pytest.mark.django_db
def test_cpf_duplicado_impedido(cenario):
    criar_membro("João Um", CPF_ADULTO, 30)
    with pytest.raises(IntegrityError):
        criar_membro("João Dois", CPF_ADULTO, 40)


@pytest.mark.django_db
def test_menor_sem_responsavel_invalido(cenario):
    membro = Membro(
        nome_completo="Menino Embaixador",
        cpf=CPF_MENOR,
        data_nascimento=timezone.localdate() - timedelta(days=365 * 13),
    )
    with pytest.raises(ValidationError) as exc:
        membro.full_clean()
    assert "responsavel" in exc.value.message_dict


@pytest.mark.django_db
def test_menor_ativacao_exige_consentimento_do_responsavel(cenario):
    responsavel = ResponsavelLegal.objects.create(
        nome="Pai Responsável", parentesco="Pai", cpf=CPF_RESPONSAVEL
    )
    membro = criar_membro("Menino Embaixador", CPF_MENOR, 13, responsavel=responsavel)
    membro.organizacoes.add(cenario["org"])

    with pytest.raises(ValidationError):
        membro.ativar()

    consentimento = membro.registrar_consentimento(ip="127.0.0.1")
    membro.refresh_from_db()
    assert membro.status == Membro.Status.ATIVO
    assert consentimento.responsavel == responsavel
    assert consentimento.termo == cenario["termo"]


@pytest.mark.django_db
def test_adulto_sem_consentimento_nao_ativa(cenario):
    membro = criar_membro("Adulto Sem Consentimento", CPF_ADULTO, 30)
    membro.organizacoes.add(cenario["org"])
    with pytest.raises(ValidationError):
        membro.ativar()
    assert membro.status == Membro.Status.PROVISORIO


@pytest.mark.django_db
def test_adulto_com_consentimento_ativa(cenario):
    membro = criar_membro("Adulto com Consentimento", CPF_ADULTO, 30)
    membro.organizacoes.add(cenario["org"])
    membro.registrar_consentimento(ip="127.0.0.1")
    membro.refresh_from_db()
    assert membro.status == Membro.Status.ATIVO


@pytest.mark.django_db
def test_ativacao_exige_organizacao_ativa(cenario):
    membro = criar_membro("Adulto Sem Organização", CPF_ADULTO, 30)
    with pytest.raises(ValidationError):
        membro.registrar_consentimento(ip="127.0.0.1")
    membro.refresh_from_db()
    assert membro.status == Membro.Status.PROVISORIO
    assert Consentimento.objects.filter(membro=membro).count() == 1
    assert not membro.pode_ativar()


@pytest.mark.django_db
def test_consentimento_imutavel(cenario):
    membro = criar_membro("Adulto Consentimento", CPF_ADULTO, 30)
    membro.organizacoes.add(cenario["org"])
    consentimento = membro.registrar_consentimento(ip="127.0.0.1")

    with pytest.raises(ValidationError):
        consentimento.finalidade = "outra"
        consentimento.save()

    with pytest.raises(ValidationError):
        consentimento.delete()

    assert Consentimento.objects.count() == 1


@pytest.mark.django_db
def test_usuario_do_membro(cenario):
    user = User.objects.create_user(email="m@example.com", password="x", full_name="Membro")
    membro = criar_membro("Membro Vinculado", CPF_ADULTO, 30, user=user)
    assert user.membro == membro
