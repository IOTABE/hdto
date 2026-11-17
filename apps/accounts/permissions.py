from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied

from .roles import Role


def user_has_role(user, *roles):
    if not getattr(user, "is_authenticated", False):
        return False
    values = {role.value if isinstance(role, Role) else role for role in roles}
    return user.groups.filter(name__in=values).exists()


def has_any_role(user, roles):
    return user_has_role(user, *roles)


def role_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            if not has_any_role(request.user, roles):
                raise PermissionDenied("Você não possui permissão para esta ação.")
            return view(request, *args, **kwargs)

        return wrapper

    return decorator


def in_role_group(user, *roles):
    return user_has_role(user, *roles)


def pode_gerir_conteudo(user):
    return bool(
        getattr(user, "is_authenticated", False)
        and (user.is_superuser or user_has_role(user, Role.ADMIN_ESTADUAL))
    )


def conteudo_required(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if not pode_gerir_conteudo(request.user):
            raise PermissionDenied("Você não possui permissão para gerir conteúdo.")
        return view(request, *args, **kwargs)

    return wrapper
