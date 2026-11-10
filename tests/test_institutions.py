import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from apps.accounts.models import User
from apps.accounts.roles import Role
from apps.geo.models import Municipio
from apps.institutions.models import AssociacaoRegional, Igreja, Organizacao
from apps.institutions.scoping import igrejas_visiveis, organizacoes_visiveis

VALID_CNPJ = "11222333000181"


@pytest.fixture
def municipio(db):
    return Municipio.objects.create(nome="Palmas", codigo_ibge="1721000")


@pytest.fixture
def associacao(db):
    return AssociacaoRegional.objects.create(nome="Associação Norte", sigla="NORTE")


@pytest.fixture
def igreja(db, associacao, municipio):
    return Igreja.objects.create(
        associacao=associacao,
        municipio=municipio,
        cnpj=VALID_CNPJ,
        razao_social="Primeira Igreja Batista de Palmas",
        nome_fantasia="PIB Palmas",
        status=Igreja.Status.HOMOLOGADA,
        homologado_em=timezone.now(),
    )


def make_role_user(email, role, **extra):
    from django.contrib.auth.models import Group

    name = role.value if isinstance(role, Role) else role
    user = User.objects.create_user(email=email, password="x", full_name=email, **extra)
    user.groups.add(Group.objects.get(name=name))
    return user


@pytest.mark.django_db
def test_cnpj_validator_accepts_valid_and_rejects_invalid():
    from apps.core.validators import validate_cnpj

    validate_cnpj(VALID_CNPJ)
    with pytest.raises(ValidationError):
        validate_cnpj("11222333000180")
    with pytest.raises(ValidationError):
        validate_cnpj("123")


@pytest.mark.django_db
def test_igreja_sem_cnpj_exige_igreja_mae(associacao, municipio):
    igreja = Igreja(
        associacao=associacao,
        municipio=municipio,
        razao_social="Congregação Sem CNPJ",
    )
    with pytest.raises(ValidationError) as exc:
        igreja.full_clean()
    assert "igreja_mae" in exc.value.message_dict


@pytest.mark.django_db
def test_congregacao_vinculada_a_igreja_mae(igreja, associacao, municipio):
    congregacao = Igreja(
        associacao=associacao,
        municipio=municipio,
        igreja_mae=igreja,
        razao_social="Congregação Central",
    )
    congregacao.full_clean()
    congregacao.save()
    assert congregacao.igreja_mae == igreja
    assert congregacao in igreja.congregacoes.all()


@pytest.mark.django_db
def test_organizacao_exige_igreja_homologada(associacao, municipio):
    pendente = Igreja.objects.create(
        associacao=associacao,
        municipio=municipio,
        cnpj="11222333000181",
        razao_social="Igreja Pendente",
        status=Igreja.Status.PENDENTE,
    )
    org = Organizacao(igreja=pendente, tipo=Organizacao.Tipo.GAM)
    with pytest.raises(ValidationError) as exc:
        org.full_clean()
    assert "igreja" in exc.value.message_dict


@pytest.mark.django_db
def test_organizacao_unica_por_tipo(igreja):
    Organizacao.objects.create(igreja=igreja, tipo=Organizacao.Tipo.GAM)
    with pytest.raises(IntegrityError):
        Organizacao.objects.create(igreja=igreja, tipo=Organizacao.Tipo.GAM)


@pytest.mark.django_db
def test_homologar_igreja(associacao, municipio):
    admin = make_role_user("admin@example.com", Role.ADMIN_ESTADUAL)
    igreja = Igreja.objects.create(
        associacao=associacao,
        municipio=municipio,
        cnpj="11222333000181",
        razao_social="Igreja Nova",
    )
    igreja.homologar(admin)
    igreja.refresh_from_db()
    assert igreja.status == Igreja.Status.HOMOLOGADA
    assert igreja.homologado_por == admin
    assert igreja.homologado_em is not None


@pytest.mark.django_db
def test_escopo_por_papel(db):
    assoc_a = AssociacaoRegional.objects.create(nome="Associação A", sigla="A")
    assoc_b = AssociacaoRegional.objects.create(nome="Associação B", sigla="B")
    mun = Municipio.objects.create(nome="Palmas", codigo_ibge="1721000")
    igreja_a = Igreja.objects.create(
        associacao=assoc_a, municipio=mun, cnpj="11222333000181",
        razao_social="Igreja A", status=Igreja.Status.HOMOLOGADA,
        homologado_em=timezone.now(),
    )
    igreja_b = Igreja.objects.create(
        associacao=assoc_b, municipio=mun, cnpj="11444777000161",
        razao_social="Igreja B", status=Igreja.Status.HOMOLOGADA,
        homologado_em=timezone.now(),
    )
    Organizacao.objects.create(igreja=igreja_a, tipo=Organizacao.Tipo.SMHB)
    Organizacao.objects.create(igreja=igreja_b, tipo=Organizacao.Tipo.ER)

    admin = make_role_user("admin2@example.com", Role.ADMIN_ESTADUAL)
    coord = make_role_user("coord2@example.com", Role.COORDENADOR_REGIONAL, associacao=assoc_a)
    diretor = make_role_user("dir2@example.com", Role.DIRETOR_LOCAL, igreja=igreja_b)
    membro = make_role_user("membro2@example.com", Role.MEMBRO, igreja=igreja_a)

    assert set(igrejas_visiveis(admin)) == {igreja_a, igreja_b}
    assert set(igrejas_visiveis(coord)) == {igreja_a}
    assert set(igrejas_visiveis(diretor)) == {igreja_b}
    assert set(igrejas_visiveis(membro)) == {igreja_a}
    assert organizacoes_visiveis(coord).count() == 1
    assert organizacoes_visiveis(diretor).get().igreja == igreja_b
