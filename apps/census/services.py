from django.conf import settings
from django.db.models import Count

from apps.institutions.models import Organizacao
from apps.institutions.scoping import igrejas_visiveis
from apps.members.models import Membro

from .models import RespostaCenso

FAIXAS_ETARIAS = [
    ("9-11", 9, 11),
    ("12-17", 12, 17),
    ("18-29", 18, 29),
    ("30-59", 30, 59),
    ("60+", 60, 200),
]
TOTAL_MUNICIPIOS_TO = 139


def _anon(value):
    k = getattr(settings, "CENSO_K_ANONIMATO", 5)
    if value is None:
        return None
    return value if value >= k else None


def membros_visiveis(user):
    igrejas = igrejas_visiveis(user)
    return (
        Membro.objects.filter(status=Membro.Status.ATIVO, organizacoes__igreja__in=igrejas)
        .distinct()
    )


def aplicar_filtros(qs, associacao_id=None, municipio_id=None, igreja_id=None):
    if igreja_id:
        qs = qs.filter(organizacoes__igreja_id=igreja_id)
    if associacao_id:
        qs = qs.filter(organizacoes__igreja__associacao_id=associacao_id)
    if municipio_id:
        qs = qs.filter(organizacoes__igreja__municipio_id=municipio_id)
    return qs.distinct()


def faixa_etaria(idade):
    for label, minimo, maximo in FAIXAS_ETARIAS:
        if minimo <= idade <= maximo:
            return label
    return None


def _piramide(qs):
    contagem = {label: 0 for label, _, _ in FAIXAS_ETARIAS}
    for membro in qs.only("data_nascimento"):
        label = faixa_etaria(membro.idade)
        if label:
            contagem[label] += 1
    return {label: _anon(valor) for label, valor in contagem.items()}


def _cobertura(user, associacao_id=None, municipio_id=None, igreja_id=None):
    igrejas = igrejas_visiveis(user).filter(organizacoes__status=Organizacao.Status.ATIVA)
    if associacao_id:
        igrejas = igrejas.filter(associacao_id=associacao_id)
    if municipio_id:
        igrejas = igrejas.filter(municipio_id=municipio_id)
    if igreja_id:
        igrejas = igrejas.filter(pk=igreja_id)
    com_organizacao = igrejas.values("municipio_id").distinct().count()
    return {
        "municipios_com_organizacao": com_organizacao,
        "total_municipios": TOTAL_MUNICIPIOS_TO,
        "percentual": round((com_organizacao / TOTAL_MUNICIPIOS_TO) * 100, 2),
    }


def _vocacional(qs):
    linhas = (
        RespostaCenso.objects.filter(membro__in=qs)
        .exclude(area_atuacao="")
        .values("area_atuacao")
        .annotate(total=Count("id"))
        .order_by("-total")
    )
    return {linha["area_atuacao"]: _anon(linha["total"]) for linha in linhas}


def _transicoes(qs):
    def duplo(primeiro, segundo):
        return (
            qs.filter(organizacoes__tipo=primeiro)
            .filter(organizacoes__tipo=segundo)
            .distinct()
            .count()
        )

    return {
        "ER": _anon(qs.filter(organizacoes__tipo=Organizacao.Tipo.ER).distinct().count()),
        "GAM": _anon(qs.filter(organizacoes__tipo=Organizacao.Tipo.GAM).distinct().count()),
        "SMHB": _anon(qs.filter(organizacoes__tipo=Organizacao.Tipo.SMHB).distinct().count()),
        "ER_para_GAM": _anon(duplo(Organizacao.Tipo.ER, Organizacao.Tipo.GAM)),
        "GAM_para_SMHB": _anon(duplo(Organizacao.Tipo.GAM, Organizacao.Tipo.SMHB)),
    }


def resumo(user, associacao_id=None, municipio_id=None, igreja_id=None):
    qs = aplicar_filtros(
        membros_visiveis(user),
        associacao_id=associacao_id,
        municipio_id=municipio_id,
        igreja_id=igreja_id,
    )
    return {
        "total_membros": qs.count(),
        "por_organizacao": {
            tipo: _anon(qs.filter(organizacoes__tipo=tipo).distinct().count())
            for tipo in Organizacao.Tipo.values
        },
        "piramide_etaria": _piramide(qs),
        "cobertura_geografica": _cobertura(
            user, associacao_id=associacao_id, municipio_id=municipio_id, igreja_id=igreja_id
        ),
        "banco_vocacional": _vocacional(qs),
        "transicoes": _transicoes(qs),
    }
