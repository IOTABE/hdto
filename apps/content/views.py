import re
from urllib.parse import quote

from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.core.utils import get_client_ip
from apps.events.models import Evento

from .forms import ContatoForm
from .models import (
    Contato,
    Galeria,
    Historia,
    MembroDiretoria,
    Noticia,
    PaginaInstitucional,
)


def home(request):
    noticias = Noticia.objects.filter(publicada=True).order_by("-publicada_em", "-created_at")[:3]
    proximos_eventos = Evento.objects.filter(fim__gte=timezone.now()).order_by("inicio")[:3]
    paginas = PaginaInstitucional.objects.filter(publicada=True)[:6]
    return render(
        request,
        "content/home.html",
        {"noticias": noticias, "proximos_eventos": proximos_eventos, "paginas": paginas},
    )


def pagina(request, slug):
    pagina_obj = get_object_or_404(PaginaInstitucional, slug=slug, publicada=True)
    return render(request, "content/pagina.html", {"pagina": pagina_obj})


def historia(request):
    registros = Historia.objects.filter(publicada=True)
    return render(request, "content/historia.html", {"registros": registros})


def diretoria(request):
    membros = MembroDiretoria.objects.filter(publicada=True).order_by(
        "-bienio_inicio", "ordem", "nome"
    )
    grupos = []
    for membro in membros:
        if not grupos or grupos[-1]["inicio"] != membro.bienio_inicio:
            grupos.append(
                {"inicio": membro.bienio_inicio, "rotulo": membro.bienio, "membros": []}
            )
        grupos[-1]["membros"].append(membro)
    return render(request, "content/diretoria.html", {"grupos": grupos})


def _whatsapp_numero():
    return re.sub(r"\D", "", getattr(settings, "CONTACT_WHATSAPP", "") or "")


def _notificar_contato(contato_obj):
    destinatario = getattr(settings, "CONTACT_EMAIL", "") or settings.DEFAULT_FROM_EMAIL
    send_mail(
        f"[Contato] {contato_obj.assunto}",
        (
            f"Nome: {contato_obj.nome}\n"
            f"E-mail: {contato_obj.email or 'não informado'}\n"
            f"Telefone: {contato_obj.telefone or 'não informado'}\n"
            f"Canal escolhido: {contato_obj.get_canal_display()}\n\n"
            f"{contato_obj.mensagem}"
        ),
        settings.DEFAULT_FROM_EMAIL,
        [destinatario],
        fail_silently=False,
    )


def contato(request):
    if request.method == "POST":
        form = ContatoForm(request.POST)
        if form.is_valid():
            contato_obj = form.save(commit=False)
            contato_obj.ip = get_client_ip(request)
            contato_obj.status = Contato.Status.REGISTRADO

            if contato_obj.canal == Contato.Canal.EMAIL:
                try:
                    _notificar_contato(contato_obj)
                except Exception:
                    contato_obj.status = Contato.Status.FALHA_ENVIO
                    contato_obj.save()
                    messages.warning(
                        request,
                        "Não foi possível enviar o e-mail. Seu contato foi registrado "
                        "e será atendido pela equipe.",
                    )
                else:
                    contato_obj.status = Contato.Status.ENVIADO
                    contato_obj.enviado_em = timezone.now()
                    contato_obj.save()
                    messages.success(request, "Mensagem enviada por e-mail com sucesso.")
                return redirect("contato")

            contato_obj.save()
            if contato_obj.canal == Contato.Canal.WHATSAPP:
                numero = _whatsapp_numero()
                if numero:
                    texto = (
                        f"Olá! Meu nome é {contato_obj.nome}. "
                        f"Assunto: {contato_obj.assunto}. {contato_obj.mensagem}"
                    )
                    return redirect(f"https://wa.me/{numero}?text={quote(texto)}")
                messages.warning(
                    request,
                    "O WhatsApp ainda não está configurado. Seu contato foi registrado "
                    "localmente e será atendido pela equipe.",
                )
                return redirect("contato")

            messages.success(request, "Contato registrado com sucesso.")
            return redirect("contato")
    else:
        form = ContatoForm()

    numero = _whatsapp_numero()
    return render(
        request,
        "content/contato.html",
        {
            "form": form,
            "contact_email": getattr(settings, "CONTACT_EMAIL", ""),
            "whatsapp_url": f"https://wa.me/{numero}" if numero else "",
        },
    )


def noticia_lista(request):
    noticias = Noticia.objects.filter(publicada=True).order_by("-publicada_em", "-created_at")
    return render(request, "content/noticia_lista.html", {"noticias": noticias})


def noticia_detalhe(request, slug):
    noticia = get_object_or_404(Noticia, slug=slug, publicada=True)
    return render(request, "content/noticia_detalhe.html", {"noticia": noticia})


def galeria_lista(request):
    galerias = Galeria.objects.filter(publicada=True)
    return render(request, "content/galeria_lista.html", {"galerias": galerias})


def galeria_detalhe(request, slug):
    galeria = get_object_or_404(Galeria, slug=slug, publicada=True)
    return render(
        request,
        "content/galeria_detalhe.html",
        {"galeria": galeria, "fotos": galeria.fotos.all()},
    )
