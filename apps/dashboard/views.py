from django.http import JsonResponse
from django.shortcuts import render

from apps.accounts.permissions import role_required
from apps.accounts.roles import Role
from apps.census.services import resumo
from apps.geo.models import Municipio
from apps.institutions.scoping import associacoes_visiveis, igrejas_visiveis


def _int_param(request, name):
    value = request.GET.get(name)
    if not value:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


@role_required(Role.ADMIN_ESTADUAL, Role.COORDENADOR_REGIONAL, Role.DIRETOR_LOCAL)
def painel(request):
    igrejas = igrejas_visiveis(request.user).order_by("nome_fantasia", "razao_social")
    municipios = (
        Municipio.objects.filter(igrejas__in=igrejas).distinct().order_by("nome")
    )
    return render(
        request,
        "dashboard/painel.html",
        {
            "associacoes": associacoes_visiveis(request.user),
            "municipios": municipios,
            "igrejas": igrejas,
            "papel": request.user.role,
        },
    )


@role_required(Role.ADMIN_ESTADUAL, Role.COORDENADOR_REGIONAL, Role.DIRETOR_LOCAL)
def indicadores(request):
    dados = resumo(
        request.user,
        associacao_id=_int_param(request, "associacao"),
        municipio_id=_int_param(request, "municipio"),
        igreja_id=_int_param(request, "igreja"),
    )
    return JsonResponse(dados)
