from django.http import JsonResponse

from apps.accounts.permissions import role_required
from apps.accounts.roles import Role
from apps.census.services import resumo


def _int_param(request, name):
    value = request.GET.get(name)
    if not value:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


@role_required(Role.ADMIN_ESTADUAL, Role.COORDENADOR_REGIONAL, Role.DIRETOR_LOCAL)
def indicadores(request):
    dados = resumo(
        request.user,
        associacao_id=_int_param(request, "associacao"),
        municipio_id=_int_param(request, "municipio"),
        igreja_id=_int_param(request, "igreja"),
    )
    return JsonResponse(dados)
