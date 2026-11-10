from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .services import revogar_consentimento


def _client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


@login_required
def meu_perfil(request):
    membro = getattr(request.user, "membro", None)
    consentimentos = membro.consentimentos.select_related("termo") if membro else []
    return render(
        request,
        "members/perfil.html",
        {"membro": membro, "consentimentos": consentimentos},
    )


@require_POST
@login_required
def revogar(request):
    membro = getattr(request.user, "membro", None)
    if membro is None:
        return redirect("home")
    revogar_consentimento(membro, ip=_client_ip(request), motivo=request.POST.get("motivo", ""))
    return render(request, "members/revogado.html")
