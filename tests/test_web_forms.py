from datetime import timedelta

import pytest
from captcha.models import CaptchaStore
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.accounts.roles import Role
from apps.events.models import Evento, Inscricao
from apps.geo.models import Municipio
from apps.institutions.models import AssociacaoRegional, Igreja, Organizacao
from apps.members.models import Consentimento, Membro, ResponsavelLegal, TermoVersao

VALID_CNPJ = "11222333000181"


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
        cnpj=VALID_CNPJ,
        razao_social="PIB Palmas",
        nome_fantasia="PIB Palmas",
        status=Igreja.Status.HOMOLOGADA,
        homologado_em=timezone.now(),
    )
    org = Organizacao.objects.create(igreja=igreja, tipo=Organizacao.Tipo.HD)
    diretor = make_user("diretor@example.com", Role.DIRETOR_LOCAL, igreja=igreja, associacao=assoc)
    admin = make_user("admin@example.com", Role.ADMIN_ESTADUAL)
    membro_user = User.objects.create_user(
        email="membro@example.com", password="x", full_name="Membro"
    )
    membro = Membro.objects.create(
        user=membro_user,
        nome_completo="Membro Existente",
        cpf=gerar_cpf("500000001"),
        data_nascimento=timezone.localdate() - timedelta(days=365 * 30),
        status=Membro.Status.ATIVO,
    )
    membro.organizacoes.add(org)
    evento = Evento.objects.create(
        titulo="Congresso Estadual",
        tipo=Evento.Tipo.CONGRESSO,
        inicio=timezone.now() + timedelta(days=5),
        fim=timezone.now() + timedelta(days=7),
        local_nome="Palmas",
    )
    return {
        "assoc": assoc,
        "municipio": municipio,
        "igreja": igreja,
        "org": org,
        "diretor": diretor,
        "admin": admin,
        "membro_user": membro_user,
        "membro": membro,
        "evento": evento,
    }


@pytest.mark.django_db
def test_cadastro_igreja_exige_login(client):
    response = client.get(reverse("igreja-nova"))
    assert response.status_code == 302


@pytest.mark.django_db
def test_diretor_cadastra_igreja(client, cenario, captcha_data):
    client.force_login(cenario["diretor"])
    response = client.post(
        reverse("igreja-nova"),
        {
            "associacao": cenario["assoc"].pk,
            "municipio": cenario["municipio"].pk,
            "cnpj": "11444777000161",
            "razao_social": "Segunda Igreja Batista",
            "nome_fantasia": "SIB Palmas",
            "pastor_titular": "Pastor",
            "telefone": "63999999999",
            "email": "sib@example.com",
            "logradouro": "Rua 1",
            "bairro": "Centro",
            "cep": "77000-000",
            "latitude": "-10.18",
            "longitude": "-48.33",
            **captcha_data,
        },
    )
    assert response.status_code == 302
    igreja = Igreja.objects.get(razao_social="Segunda Igreja Batista")
    assert igreja.status == Igreja.Status.PENDENTE
    assert igreja.location is not None


@pytest.mark.django_db
def test_igreja_sem_cnpj_exige_mae_no_formulario(client, cenario, captcha_data):
    client.force_login(cenario["diretor"])
    response = client.post(
        reverse("igreja-nova"),
        {
            "associacao": cenario["assoc"].pk,
            "municipio": cenario["municipio"].pk,
            "razao_social": "Congregação Sem CNPJ",
            **captcha_data,
        },
    )
    assert response.status_code == 200
    assert "igreja_mae" in response.context["form"].errors


@pytest.mark.django_db
def test_diretor_ativa_organizacao(client, cenario, captcha_data):
    client.force_login(cenario["diretor"])
    response = client.post(
        reverse("organizacao-nova"),
        {
            "igreja": cenario["igreja"].pk,
            "tipo": Organizacao.Tipo.ERV,
            "data_fundacao": "2020-01-01",
            "lider_nome": "Líder",
            "lider_contato": "63999999999",
            "dia_reuniao": "Sábado",
            "horario_reuniao": "19:00",
            **captcha_data,
        },
    )
    assert response.status_code == 302
    assert Organizacao.objects.filter(
        igreja=cenario["igreja"], tipo=Organizacao.Tipo.ERV
    ).exists()


@pytest.mark.django_db
def test_organizacao_duplicada_retorna_erro(client, cenario, captcha_data):
    client.force_login(cenario["diretor"])
    response = client.post(
        reverse("organizacao-nova"),
        {"igreja": cenario["igreja"].pk, "tipo": Organizacao.Tipo.HD, **captcha_data},
    )
    assert response.status_code == 200
    assert "já está ativa" in response.content.decode()


@pytest.mark.django_db
def test_autocadastro_adulto_ativa_com_consentimento(client, cenario, captcha_data):
    response = client.post(
        reverse("membro-novo"),
        {
            "nome_completo": "Novo Adulto",
            "cpf": gerar_cpf("600000001"),
            "data_nascimento": "1990-05-10",
            "estado_civil": "casado",
            "profissao": "Engenheiro",
            "email": "adulto@example.com",
            "telefone": "63999999999",
            "igreja": cenario["igreja"].pk,
            "organizacoes": [cenario["org"].pk],
            "consentimento": "on",
            **captcha_data,
        },
    )
    assert response.status_code == 200
    membro = Membro.objects.get(nome_completo="Novo Adulto")
    assert membro.status == Membro.Status.ATIVO
    assert membro.igreja == cenario["igreja"]
    assert membro.consentimentos.count() == 1
    assert Consentimento.objects.filter(membro=membro).exists()


@pytest.mark.django_db
def test_cadastro_exibe_termo_expansivel_acima_da_concordancia(client, cenario):
    response = client.get(reverse("membro-novo"))
    assert response.status_code == 200
    conteudo = response.content.decode()
    termo = TermoVersao.vigente_atual()
    assert "<details" in conteudo
    assert "<summary>" in conteudo
    assert termo.texto in conteudo
    assert conteudo.index(termo.texto) < conteudo.index('name="consentimento"')


@pytest.mark.django_db
def test_autocadastro_exige_captcha(client, cenario):
    response = client.post(
        reverse("membro-novo"),
        {
            "nome_completo": "Sem Captcha",
            "cpf": gerar_cpf("600000004"),
            "data_nascimento": "1990-05-10",
            "igreja": cenario["igreja"].pk,
            "organizacoes": [cenario["org"].pk],
            "consentimento": "on",
        },
    )
    assert response.status_code == 200
    assert "captcha" in response.context["form"].errors
    assert not Membro.objects.filter(nome_completo="Sem Captcha").exists()


@pytest.mark.django_db
def test_autocadastro_exige_igreja(client, cenario, captcha_data):
    response = client.post(
        reverse("membro-novo"),
        {
            "nome_completo": "Sem Igreja",
            "cpf": gerar_cpf("600000011"),
            "data_nascimento": "1990-05-10",
            "organizacoes": [cenario["org"].pk],
            "consentimento": "on",
            **captcha_data,
        },
    )
    assert response.status_code == 200
    assert "igreja" in response.context["form"].errors
    assert not Membro.objects.filter(nome_completo="Sem Igreja").exists()


@pytest.mark.django_db
def test_autocadastro_rejeita_organizacao_de_outra_igreja(client, cenario, captcha_data):
    outra = Igreja.objects.create(
        associacao=cenario["assoc"],
        municipio=cenario["municipio"],
        cnpj="11444777000161",
        razao_social="Outra Igreja",
        status=Igreja.Status.HOMOLOGADA,
        homologado_em=timezone.now(),
    )
    outra_org = Organizacao.objects.create(igreja=outra, tipo=Organizacao.Tipo.HD)
    response = client.post(
        reverse("membro-novo"),
        {
            "nome_completo": "Igreja Divergente",
            "cpf": gerar_cpf("600000012"),
            "data_nascimento": "1990-05-10",
            "igreja": cenario["igreja"].pk,
            "organizacoes": [outra_org.pk],
            "consentimento": "on",
            **captcha_data,
        },
    )
    assert response.status_code == 200
    assert "organizacoes" in response.context["form"].errors
    assert not Membro.objects.filter(nome_completo="Igreja Divergente").exists()


@pytest.mark.django_db
def test_cadastro_renderiza_captcha_local(client, cenario):
    response = client.get(reverse("membro-novo"))
    conteudo = response.content.decode()
    assert "/captcha/image/" in conteudo
    assert 'name="captcha_1"' in conteudo
    assert "js.hcaptcha.com" not in conteudo
    assert "google.com/recaptcha" not in conteudo


@pytest.mark.django_db
def test_autocadastro_com_captcha_invalido_bloqueado(client, cenario):
    response = client.post(
        reverse("membro-novo"),
        {
            "nome_completo": "Com Captcha Inválido",
            "cpf": gerar_cpf("600000010"),
            "data_nascimento": "1990-05-10",
            "igreja": cenario["igreja"].pk,
            "organizacoes": [cenario["org"].pk],
            "consentimento": "on",
            "captcha_0": CaptchaStore.generate_key(),
            "captcha_1": "errado",
        },
    )
    assert response.status_code == 200
    assert "captcha" in response.context["form"].errors
    assert not Membro.objects.filter(nome_completo="Com Captcha Inválido").exists()


@pytest.mark.django_db
def test_autocadastro_menor_sem_responsavel_bloqueado(client, cenario, captcha_data):
    response = client.post(
        reverse("membro-novo"),
        {
            "nome_completo": "Menor Sem Responsável",
            "cpf": gerar_cpf("600000002"),
            "data_nascimento": timezone.localdate().replace(year=timezone.localdate().year - 13).isoformat(),
            "igreja": cenario["igreja"].pk,
            "organizacoes": [cenario["org"].pk],
            "consentimento": "on",
            **captcha_data,
        },
    )
    assert response.status_code == 200
    assert not Membro.objects.filter(nome_completo="Menor Sem Responsável").exists()
    assert "responsavel_nome" in response.context["form"].errors


@pytest.mark.django_db
def test_autocadastro_menor_com_responsavel(client, cenario, captcha_data):
    nascimento = timezone.localdate().replace(year=timezone.localdate().year - 13)
    response = client.post(
        reverse("membro-novo"),
        {
            "nome_completo": "Menor Com Responsável",
            "cpf": gerar_cpf("600000003"),
            "data_nascimento": nascimento.isoformat(),
            "igreja": cenario["igreja"].pk,
            "organizacoes": [cenario["org"].pk],
            "responsavel_nome": "Pai Responsável",
            "responsavel_cpf": gerar_cpf("700000001"),
            "responsavel_parentesco": "Pai",
            "responsavel_telefone": "63988888888",
            "consentimento": "on",
            **captcha_data,
        },
    )
    assert response.status_code == 200
    membro = Membro.objects.get(nome_completo="Menor Com Responsável")
    assert membro.status == Membro.Status.ATIVO
    assert membro.responsavel is not None
    assert ResponsavelLegal.objects.filter(nome="Pai Responsável").exists()


@pytest.mark.django_db
def test_formularios_institucionais_renderizam_captcha(client, cenario):
    client.force_login(cenario["admin"])
    for nome in ("igreja-nova", "organizacao-nova"):
        response = client.get(reverse(nome))
        assert response.status_code == 200
        assert "/captcha/image/" in response.content.decode()


@pytest.mark.django_db
def test_inscricao_renderiza_captcha(client, cenario):
    client.force_login(cenario["membro_user"])
    response = client.get(reverse("evento-inscricao", args=[cenario["evento"].pk]))
    assert response.status_code == 200
    assert "/captcha/image/" in response.content.decode()


@pytest.mark.django_db
def test_inscricao_em_evento(client, cenario, captcha_data):
    client.force_login(cenario["membro_user"])
    response = client.post(
        reverse("evento-inscricao", args=[cenario["evento"].pk]),
        {"membro": cenario["membro"].pk, **captcha_data},
    )
    assert response.status_code == 302
    assert Inscricao.objects.filter(
        evento=cenario["evento"], membro=cenario["membro"]
    ).exists()


@pytest.mark.django_db
def test_inscricao_duplicada_nao_cria(client, cenario, captcha_data):
    Inscricao.objects.create(evento=cenario["evento"], membro=cenario["membro"])
    client.force_login(cenario["membro_user"])
    response = client.post(
        reverse("evento-inscricao", args=[cenario["evento"].pk]),
        {"membro": cenario["membro"].pk, **captcha_data},
    )
    assert response.status_code == 200
    assert Inscricao.objects.filter(evento=cenario["evento"]).count() == 1


@pytest.mark.django_db
def test_inscricao_anonima_exige_login(client, cenario):
    response = client.get(reverse("evento-inscricao", args=[cenario["evento"].pk]))
    assert response.status_code == 302


@pytest.mark.django_db
def test_painel_admin_e_membro(client, cenario):
    client.force_login(cenario["admin"])
    response = client.get(reverse("dashboard"))
    assert response.status_code == 200
    assert "Painel analítico" in response.content.decode()

    client.force_login(cenario["membro_user"])
    assert client.get(reverse("dashboard")).status_code == 403
