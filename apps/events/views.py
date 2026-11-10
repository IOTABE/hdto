import io

import qrcode
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.accounts.permissions import role_required
from apps.accounts.roles import Role

from .forms import InscricaoForm
from .models import Evento, Inscricao


def evento_lista(request):
    eventos = Evento.objects.filter(fim__gte=timezone.now()).order_by("inicio")
    return render(request, "events/evento_lista.html", {"eventos": eventos})


def evento_detalhe(request, pk):
    evento = get_object_or_404(Evento, pk=pk)
    minha_inscricao = None
    if request.user.is_authenticated:
        minha_inscricao = Inscricao.objects.filter(
            evento=evento, membro__user=request.user
        ).first()
    return render(
        request,
        "events/evento_detalhe.html",
        {"evento": evento, "minha_inscricao": minha_inscricao},
    )


@login_required
def inscricao_nova(request, pk):
    evento = get_object_or_404(Evento, pk=pk)
    if not evento.esta_aberto():
        messages.warning(request, "As inscrições para este evento estão encerradas.")
        return redirect("evento-detalhe", pk=evento.pk)

    if getattr(request.user, "membro", None) is None and not request.user.has_role(
        Role.ADMIN_ESTADUAL, Role.COORDENADOR_REGIONAL, Role.DIRETOR_LOCAL
    ):
        messages.info(request, "Conclua seu cadastro de membro para se inscrever.")
        return redirect("membro-novo")

    form = InscricaoForm(request.POST or None, user=request.user, evento=evento)
    if request.method == "POST" and form.is_valid():
        inscricao = Inscricao.objects.create(
            evento=evento, membro=form.cleaned_data["membro"]
        )
        messages.success(
            request,
            f"Inscrição de {inscricao.membro.nome_completo} confirmada. "
            "A credencial com QR Code está disponível no seu perfil.",
        )
        return redirect("evento-detalhe", pk=evento.pk)
    return render(request, "events/inscricao_form.html", {"evento": evento, "form": form})


def _ics_escape(valor):
    return (
        (valor or "")
        .replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
    )


def evento_ics(request, pk):
    evento = get_object_or_404(Evento, pk=pk)
    linhas = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//HDTO//Eventos//PT-BR",
        "CALSCALE:GREGORIAN",
        "BEGIN:VEVENT",
        f"UID:evento-{evento.pk}@hdto",
        f"DTSTAMP:{timezone.now().strftime('%Y%m%dT%H%M%SZ')}",
        f"DTSTART:{evento.inicio.strftime('%Y%m%dT%H%M%SZ')}",
        f"DTEND:{evento.fim.strftime('%Y%m%dT%H%M%SZ')}",
        f"SUMMARY:{_ics_escape(evento.titulo)}",
        f"DESCRIPTION:{_ics_escape(evento.descricao)}",
        f"LOCATION:{_ics_escape(evento.local_nome or evento.endereco)}",
        "END:VEVENT",
        "END:VCALENDAR",
    ]
    response = HttpResponse("\r\n".join(linhas), content_type="text/calendar; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="evento-{evento.pk}.ics"'
    return response


@login_required
def inscricao_qr(request, pk):
    inscricao = get_object_or_404(
        Inscricao.objects.select_related("membro", "evento"), pk=pk
    )
    if not (
        request.user.is_staff
        or request.user.is_superuser
        or inscricao.membro.user_id == request.user.id
    ):
        raise PermissionDenied("Você não pode acessar esta credencial.")

    url = request.build_absolute_uri(reverse("evento-checkin", args=[inscricao.token]))
    imagem = qrcode.make(url)
    buffer = io.BytesIO()
    imagem.save(buffer, format="PNG")
    return HttpResponse(buffer.getvalue(), content_type="image/png")


@require_POST
@role_required(Role.ADMIN_ESTADUAL, Role.COORDENADOR_REGIONAL, Role.DIRETOR_LOCAL)
def checkin(request, token):
    inscricao = get_object_or_404(Inscricao, token=token)
    if inscricao.status == Inscricao.Status.CANCELADA:
        return JsonResponse({"detail": "Inscrição cancelada."}, status=400)
    inscricao.realizar_checkin()
    return JsonResponse(
        {
            "status": inscricao.status,
            "membro": inscricao.membro.nome_completo,
            "evento": inscricao.evento.titulo,
            "checkin_em": inscricao.checkin_em,
        }
    )
