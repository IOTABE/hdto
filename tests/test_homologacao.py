from datetime import timedelta

import pytest
from django.contrib.gis.geos import Point
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.accounts.roles import Role
from apps.census.models import RespostaCenso
from apps.geo.models import Municipio
from apps.institutions.models import AssociacaoRegional, Igreja, Organizacao
from apps.members.models import Membro


def make_user(email, role, **extra):
    from django.contrib.auth.models import Group

    user = User.objects.create_user(email=email, password="x", full_name=email, **extra)
    user.groups.add(Group.objects.get(name=role.value))
    return user


def gerar_cpf(seed):
    digits = list(seed)
    for position in (9, 10):
        total = sum(
            int(digit) * weight
            for digit, weight in zip(digits[:position], range(position + 1, 1, -1), strict=True)
        )
        remainder = (total * 10) % 11
        digits.append("0" if remainder == 10 else str(remainder))
    return "".join(digits)


@pytest.fixture
def cenario(db):
    norte = AssociacaoRegional.objects.create(nome="Associação Norte", sigla="NORTE")
    sul = AssociacaoRegional.objects.create(nome="Associação Sul", sigla="SUL")
    palmas = Municipio.objects.create(nome="Palmas", codigo_ibge="1721000")
    gurupi = Municipio.objects.create(nome="Gurupi", codigo_ibge="1709500")

    igreja_palmas = Igreja.objects.create(
        associacao=norte,
        municipio=palmas,
        cnpj="11222333000181",
        razao_social="PIB Palmas",
        nome_fantasia="PIB Palmas",
        location=Point(-48.33, -10.18, srid=4326),
        status=Igreja.Status.HOMOLOGADA,
        homologado_em=timezone.now(),
    )
    igreja_gurupi = Igreja.objects.create(
        associacao=sul,
        municipio=gurupi,
        cnpj="11444777000161",
        razao_social="PIB Gurupi",
        nome_fantasia="PIB Gurupi",
        location=Point(-49.07, -11.73, srid=4326),
        status=Igreja.Status.HOMOLOGADA,
        homologado_em=timezone.now(),
    )
    return {
        "norte": norte,
        "sul": sul,
        "palmas": palmas,
        "gurupi": gurupi,
        "igreja_palmas": igreja_palmas,
        "igreja_gurupi": igreja_gurupi,
    }


@pytest.mark.django_db
def test_ct01_diretor_ativa_gam_e_mapa_reflete(cenario):
    igreja = cenario["igreja_palmas"]
    diretor = make_user("diretor@example.com", Role.DIRETOR_LOCAL, igreja=igreja)

    organizacao = Organizacao(igreja=igreja, tipo=Organizacao.Tipo.GAM, lider_nome=diretor.full_name)
    organizacao.full_clean()
    organizacao.save()

    assert igreja.organizacoes.filter(tipo=Organizacao.Tipo.GAM).exists()

    from django.test import Client

    client = Client()
    resposta = client.get(
        reverse("mapa-pontos")
        + f"?municipio={cenario['palmas'].pk}&tipo=GAM"
    )
    dados = resposta.json()
    assert dados["total"] == 1
    assert dados["pontos"][0]["nome"] == "PIB Palmas"


@pytest.mark.django_db
def test_ct02_menor_sem_responsavel_bloqueado(cenario):
    membro = Membro(
        nome_completo="Embaixador Menor",
        cpf=gerar_cpf("200000001"),
        data_nascimento=timezone.localdate() - timedelta(days=365 * 13),
    )
    with pytest.raises(ValidationError) as exc:
        membro.full_clean()
    assert "responsavel" in exc.value.message_dict


@pytest.mark.django_db
def test_ct03_filtro_palmas_smhb(cenario):
    Organizacao.objects.create(igreja=cenario["igreja_palmas"], tipo=Organizacao.Tipo.SMHB)
    Organizacao.objects.create(igreja=cenario["igreja_palmas"], tipo=Organizacao.Tipo.ER)
    Organizacao.objects.create(igreja=cenario["igreja_gurupi"], tipo=Organizacao.Tipo.SMHB)

    from django.test import Client

    client = Client()
    resposta = client.get(
        reverse("mapa-pontos")
        + f"?municipio={cenario['palmas'].pk}&tipo=SMHB"
    )
    dados = resposta.json()
    assert dados["total"] == 1
    assert dados["pontos"][0]["nome"] == "PIB Palmas"


@pytest.mark.django_db
def test_ct04_dashboard_recalcula_por_associacao(cenario, settings):
    settings.CENSO_K_ANONIMATO = 1
    for igreja, quantidade, prefixo in [
        (cenario["igreja_palmas"], 3, "30000000"),
        (cenario["igreja_gurupi"], 2, "40000000"),
    ]:
        org = Organizacao.objects.create(igreja=igreja, tipo=Organizacao.Tipo.SMHB)
        for indice in range(quantidade):
            membro = Membro.objects.create(
                nome_completo=f"Membro {prefixo}{indice}",
                cpf=gerar_cpf(f"{prefixo}{indice}"),
                data_nascimento=timezone.localdate() - timedelta(days=365 * (20 + indice)),
                status=Membro.Status.ATIVO,
            )
            membro.organizacoes.add(org)
            RespostaCenso.objects.create(
                membro=membro, area_atuacao=RespostaCenso.AreaAtuacao.CONSTRUCAO_CIVIL
            )

    admin = make_user("admin@example.com", Role.ADMIN_ESTADUAL)
    from django.test import Client

    client = Client()
    client.force_login(admin)
    geral = client.get(reverse("censo-indicadores")).json()
    norte = client.get(
        reverse("censo-indicadores") + f"?associacao={cenario['norte'].pk}"
    ).json()
    sul = client.get(
        reverse("censo-indicadores") + f"?associacao={cenario['sul'].pk}"
    ).json()

    assert geral["total_membros"] == 5
    assert norte["total_membros"] == 3
    assert sul["total_membros"] == 2
    assert norte["banco_vocacional"]["construcao_civil"] == 3
    assert sul["banco_vocacional"]["construcao_civil"] == 2
