from django.db.models import Q

from apps.accounts.roles import Role
from apps.institutions.models import Igreja, Organizacao
from apps.members.models import Membro


def membros_visiveis(user):
    qs = Membro.objects.select_related("user", "igreja")
    if user is None or not user.is_authenticated:
        return qs.none()
    if user.is_superuser or user.has_role(Role.ADMIN_ESTADUAL):
        return qs
    if user.has_role(Role.COORDENADOR_REGIONAL) and user.associacao_id:
        return qs.filter(
            Q(igreja__associacao_id=user.associacao_id)
            | Q(organizacoes__igreja__associacao_id=user.associacao_id)
        ).distinct()
    if user.has_role(Role.DIRETOR_LOCAL) and user.igreja_id:
        return qs.filter(
            Q(igreja_id=user.igreja_id) | Q(organizacoes__igreja_id=user.igreja_id)
        ).distinct()
    membro = getattr(user, "membro", None)
    if membro is not None:
        return qs.filter(pk=membro.pk)
    return qs.none()


def igrejas_para_cadastro(user):
    qs = Igreja.objects.filter(status=Igreja.Status.HOMOLOGADA)
    if user is None or not user.is_authenticated:
        return qs
    if user.is_superuser or user.has_role(Role.ADMIN_ESTADUAL):
        return qs
    if user.has_role(Role.COORDENADOR_REGIONAL) and user.associacao_id:
        return qs.filter(associacao_id=user.associacao_id)
    if user.has_role(Role.DIRETOR_LOCAL) and user.igreja_id:
        return qs.filter(pk=user.igreja_id)
    return qs


def organizacoes_para_cadastro(user):
    qs = (
        Organizacao.objects.filter(
            status=Organizacao.Status.ATIVA, igreja__status="homologada"
        )
        .select_related("igreja")
        .order_by("igreja__nome_fantasia", "igreja__razao_social", "tipo")
    )
    if user is None or not user.is_authenticated:
        return qs
    if user.is_superuser or user.has_role(Role.ADMIN_ESTADUAL):
        return qs
    if user.has_role(Role.COORDENADOR_REGIONAL) and user.associacao_id:
        return qs.filter(igreja__associacao_id=user.associacao_id)
    if user.has_role(Role.DIRETOR_LOCAL) and user.igreja_id:
        return qs.filter(igreja_id=user.igreja_id)
    return qs
