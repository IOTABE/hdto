from django.contrib import messages
from django.shortcuts import redirect, render

from apps.accounts.permissions import role_required
from apps.accounts.roles import Role

from .forms import IgrejaForm, OrganizacaoForm


@role_required(Role.ADMIN_ESTADUAL, Role.COORDENADOR_REGIONAL, Role.DIRETOR_LOCAL)
def igreja_nova(request):
    form = IgrejaForm(request.POST or None, user=request.user)
    if request.method == "POST" and form.is_valid():
        igreja = form.save()
        messages.success(
            request,
            f"Igreja “{igreja}” cadastrada. Aguardando homologação do administrador estadual.",
        )
        return redirect("dashboard")
    return render(request, "institutions/igreja_form.html", {"form": form})


@role_required(Role.ADMIN_ESTADUAL, Role.COORDENADOR_REGIONAL, Role.DIRETOR_LOCAL)
def organizacao_nova(request):
    form = OrganizacaoForm(request.POST or None, user=request.user)
    if request.method == "POST" and form.is_valid():
        organizacao = form.save()
        messages.success(request, f"Organização “{organizacao.get_tipo_display()}” ativada.")
        return redirect("dashboard")
    return render(request, "institutions/organizacao_form.html", {"form": form})
