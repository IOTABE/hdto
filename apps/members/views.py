from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from apps.core.utils import get_client_ip

from .forms import MembroForm
from .services import revogar_consentimento


@login_required
def meu_perfil(request):
    membro = getattr(request.user, "membro", None)
    consentimentos = membro.consentimentos.select_related("termo") if membro else []
    inscricoes = membro.inscricoes.select_related("evento") if membro else []
    return render(
        request,
        "members/perfil.html",
        {"membro": membro, "consentimentos": consentimentos, "inscricoes": inscricoes},
    )


@require_POST
@login_required
def revogar(request):
    membro = getattr(request.user, "membro", None)
    if membro is None:
        return redirect("home")
    revogar_consentimento(membro, ip=get_client_ip(request), motivo=request.POST.get("motivo", ""))
    return render(request, "members/revogado.html")


def membro_novo(request):
    if request.user.is_authenticated and getattr(request.user, "membro", None):
        messages.info(request, "Sua conta já possui cadastro de membro.")
        return redirect("meu-perfil")

    form = MembroForm(
        request.POST or None,
        user=request.user if request.user.is_authenticated else None,
        ip=get_client_ip(request),
    )
    if request.method == "POST" and form.is_valid():
        membro = form.save()
        messages.success(
            request,
            f"Cadastro de {membro.nome_completo} concluído com consentimento registrado.",
        )
        if request.user.is_authenticated:
            return redirect("meu-perfil")
        return render(request, "members/membro_sucesso.html", {"membro": membro})
    return render(request, "members/membro_form.html", {"form": form})
