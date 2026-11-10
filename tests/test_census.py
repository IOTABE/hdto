from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.accounts.roles import Role
from apps.census.models import RespostaCenso
from apps.geo.models import Municipio
from apps.institutions.models import AssociacaoRegional, Igreja, Organizacao
from apps.members.models import Membro


def gerar_cpf(seed: str) -> str:
    digits = list(seed)
    for position in (9, 10):
        total = sum(
            int(digit) * weight
            for digit, weight in zip(digits[:position], range(position + 1, 1, -1), strict=True)
        )
        remainder = (total * 10) % 11
        digits.append("0" if remainder == 10 else str(remainder))
    return "".join(digits)


def make_user(email, role, **extra):
    from django.contrib.auth.models import Group

    user = User.objects.create_user(email=email, password="x", full_name=email, **extra)
    user.groups.add(Group.objects.get(name=role.value))
    return user


def make_igreja(assoc, municipio, cnpj, nome):
    return Igreja.objects.create(
        associacao=assoc,
        municipio=municipio,
        cnpj=cnpj,
        razao_social=nome,
        status=Igreja.Status.HOMOLOGADA,
        homologado_em=timezone.now(),
    )


def make_membro(nome, cpf_seed, idade, org, status=Membro.Status.ATIVO, **extra):
    membro = Membro.objects.create(
        nome_completo=nome,
        cpf=gerar_cpf(cpf_seed),
        data_nascimento=timezone.localdate() - timedelta(days=365 * idade + 10),
        status=status,
        **extra,
    )
    membro.organizacoes.add(org)
    return membro


@pytest.fixture
def dados(db):
    assoc_a = AssociacaoRegional.objects.create(nome="Associação Norte", sigla="NORTE")
    assoc_b = AssociacaoRegional.objects.create(nome="Associação Sul", sigla="SUL")
    palmas = Municipio.objects.create(nome="Palmas", codigo_ibge="1721000")
    gurupi = Municipio.objects.create(nome="Gurupi", codigo_ibge="1709500")

    igreja_a1 = make_igreja(assoc_a, palmas, "11222333000181", "PIB Palmas")
    igreja_a2 = make_igreja(assoc_a, palmas, "11444777000161", "Segunda Batista Palmas")
    igreja_b1 = make_igreja(assoc_b, gurupi, "04252011000110", "PIB Gurupi")

    org_a1 = Organizacao.objects.create(igreja=igreja_a1, tipo=Organizacao.Tipo.HD)
    org_a2_erv = Organizacao.objects.create(igreja=igreja_a2, tipo=Organizacao.Tipo.ERV)
    org_a2_er = Organizacao.objects.create(igreja=igreja_a2, tipo=Organizacao.Tipo.ER)
    org_b1 = Organizacao.objects.create(igreja=igreja_b1, tipo=Organizacao.Tipo.HD)

    make_membro("A Criança", "100000001", 10, org_a2_er)
    make_membro("A Adolescente", "100000002", 13, org_a2_er)
    make_membro("A Jovem", "100000003", 20, org_a2_erv)
    make_membro("A Adulto 1", "100000004", 30, org_a1)
    make_membro("A Adulto 2", "100000005", 40, org_a1)
    make_membro("A Idoso", "100000006", 65, org_a1)
    make_membro("B Jovem", "100000007", 25, org_b1)
    make_membro("B Adulto", "100000008", 50, org_b1)
    make_membro("Inativo", "100000009", 35, org_a1, status=Membro.Status.INATIVO)

    membros_a = list(Membro.objects.filter(organizacoes__igreja__associacao=assoc_a).distinct())
    RespostaCenso.objects.create(
        membro=membros_a[0], area_atuacao=RespostaCenso.AreaAtuacao.CONSTRUCAO_CIVIL
    )
    RespostaCenso.objects.create(
        membro=membros_a[1], area_atuacao=RespostaCenso.AreaAtuacao.SAUDE
    )
    RespostaCenso.objects.create(
        membro=membros_a[2], area_atuacao=RespostaCenso.AreaAtuacao.CONSTRUCAO_CIVIL
    )

    return {
        "assoc_a": assoc_a,
        "assoc_b": assoc_b,
        "palmas": palmas,
        "gurupi": gurupi,
        "igreja_a1": igreja_a1,
        "igreja_a2": igreja_a2,
        "igreja_b1": igreja_b1,
        "org_a1": org_a1,
        "org_a2_erv": org_a2_erv,
        "org_a2_er": org_a2_er,
        "org_b1": org_b1,
    }


@pytest.mark.django_db
def test_endpoint_exige_login(client):
    response = client.get(reverse("censo-indicadores"))
    assert response.status_code == 302


@pytest.mark.django_db
def test_membro_nao_acessa_dashboard(client, dados):
    user = make_user("membro@example.com", Role.MEMBRO, igreja=dados["igreja_a1"])
    client.force_login(user)
    assert client.get(reverse("censo-indicadores")).status_code == 403


@pytest.mark.django_db
def test_admin_ve_total_consolidado(client, dados, settings):
    settings.CENSO_K_ANONIMATO = 1
    admin = make_user("admin@example.com", Role.ADMIN_ESTADUAL)
    client.force_login(admin)
    data = client.get(reverse("censo-indicadores")).json()

    assert data["total_membros"] == 8
    assert data["por_organizacao"] == {"HD": 5, "ERV": 1, "ER": 2}
    assert data["piramide_etaria"] == {
        "9-11": 1,
        "12-17": 1,
        "18-29": 2,
        "30-59": 3,
        "60+": 1,
    }
    assert data["banco_vocacional"]["construcao_civil"] == 2
    assert data["banco_vocacional"]["saude"] == 1
    assert data["cobertura_geografica"]["municipios_com_organizacao"] == 2
    assert data["cobertura_geografica"]["total_municipios"] == 139


@pytest.mark.django_db
def test_coordenador_ve_apenas_sua_associacao(client, dados, settings):
    settings.CENSO_K_ANONIMATO = 1
    coord = make_user(
        "coord@example.com", Role.COORDENADOR_REGIONAL, associacao=dados["assoc_a"]
    )
    client.force_login(coord)
    data = client.get(reverse("censo-indicadores")).json()
    assert data["total_membros"] == 6
    assert data["cobertura_geografica"]["municipios_com_organizacao"] == 1


@pytest.mark.django_db
def test_filtro_por_associacao(client, dados, settings):
    settings.CENSO_K_ANONIMATO = 1
    admin = make_user("admin2@example.com", Role.ADMIN_ESTADUAL)
    client.force_login(admin)
    data = client.get(
        reverse("censo-indicadores") + f"?associacao={dados['assoc_b'].pk}"
    ).json()
    assert data["total_membros"] == 2


@pytest.mark.django_db
def test_k_anonimato_suprime_grupos_pequenos(client, dados, settings):
    settings.CENSO_K_ANONIMATO = 5
    admin = make_user("admin3@example.com", Role.ADMIN_ESTADUAL)
    client.force_login(admin)
    data = client.get(reverse("censo-indicadores")).json()
    assert data["total_membros"] == 8
    assert data["por_organizacao"]["HD"] == 5
    assert data["por_organizacao"]["ERV"] is None
    assert data["por_organizacao"]["ER"] is None
    assert data["banco_vocacional"]["saude"] is None
