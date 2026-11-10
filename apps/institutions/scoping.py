from .models import AssociacaoRegional, Igreja, Organizacao

ADMIN_ROLE = "admin_estadual"
COORD_ROLE = "coord_regional"
DIRETOR_ROLE = "diretor_local"
MEMBRO_ROLE = "membro"


def _has(user, role):
    return user.is_authenticated and (
        user.is_superuser or user.groups.filter(name=role).exists()
    )


def associacoes_visiveis(user):
    qs = AssociacaoRegional.objects.all()
    if not user.is_authenticated:
        return qs.none()
    if user.is_superuser or _has(user, ADMIN_ROLE):
        return qs
    if _has(user, COORD_ROLE) and user.associacao_id:
        return qs.filter(pk=user.associacao_id)
    if user.igreja_id:
        return qs.filter(pk=user.igreja.associacao_id)
    return qs.none()


def igrejas_visiveis(user):
    qs = Igreja.objects.select_related("associacao", "municipio")
    if not user.is_authenticated:
        return qs.none()
    if user.is_superuser or _has(user, ADMIN_ROLE):
        return qs
    if _has(user, COORD_ROLE) and user.associacao_id:
        return qs.filter(associacao_id=user.associacao_id)
    if user.igreja_id:
        return qs.filter(pk=user.igreja_id)
    return qs.none()


def organizacoes_visiveis(user):
    qs = Organizacao.objects.select_related("igreja")
    if not user.is_authenticated:
        return qs.none()
    if user.is_superuser or _has(user, ADMIN_ROLE):
        return qs
    if _has(user, COORD_ROLE) and user.associacao_id:
        return qs.filter(igreja__associacao_id=user.associacao_id)
    if user.igreja_id:
        return qs.filter(igreja_id=user.igreja_id)
    return qs.none()
