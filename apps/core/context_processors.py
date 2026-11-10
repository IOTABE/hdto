from apps.accounts.roles import Role


def navigation(request):
    user = request.user
    pode_gerir = False
    tem_membro = False
    if user.is_authenticated:
        pode_gerir = user.is_superuser or user.has_role(
            Role.ADMIN_ESTADUAL, Role.COORDENADOR_REGIONAL, Role.DIRETOR_LOCAL
        )
        tem_membro = getattr(user, "membro", None) is not None
    return {
        "pode_gerir_cadastros": pode_gerir,
        "tem_membro": tem_membro,
    }
