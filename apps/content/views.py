import re
from urllib.parse import quote

from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from apps.accounts.permissions import conteudo_required
from apps.core.utils import get_client_ip
from apps.events.models import Evento

from .forms import (
    ContatoForm,
    FotoForm,
    GaleriaForm,
    HistoriaForm,
    MembroDiretoriaForm,
    NoticiaForm,
)
from .models import (
    Contato,
    Foto,
    Galeria,
    Historia,
    MembroDiretoria,
    Noticia,
    PaginaInstitucional,
)


def home(request):
    noticias = Noticia.objects.filter(publicada=True).order_by("-publicada_em", "-created_at")[:3]
    proximos_eventos = (
        Evento.objects.filter(fim__gte=timezone.now())
        .prefetch_related("arquivos")
        .order_by("inicio")[:3]
    )
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


def _render_editor(
    request, form, *, titulo, subtitulo, cancel_url, submit_label="Salvar"
):
    return render(
        request,
        "content/editor_form.html",
        {
            "form": form,
            "titulo": titulo,
            "subtitulo": subtitulo,
            "cancel_url": cancel_url,
            "submit_label": submit_label,
        },
    )


def _confirmar_exclusao(
    request,
    objeto,
    *,
    titulo,
    descricao,
    cancel_url,
    success_url,
    mensagem,
):
    if request.method == "POST":
        objeto.delete()
        messages.success(request, mensagem)
        return redirect(success_url)
    return render(
        request,
        "content/confirmar_exclusao.html",
        {
            "objeto": objeto,
            "titulo": titulo,
            "descricao": descricao,
            "cancel_url": cancel_url,
        },
    )


@conteudo_required
def gestao_conteudo(request):
    return render(
        request,
        "content/gestao_painel.html",
        {
            "noticias": Noticia.objects.order_by("-created_at")[:8],
            "eventos": Evento.objects.order_by("-inicio")[:8],
            "galerias": Galeria.objects.order_by("-created_at")[:8],
            "historias": Historia.objects.order_by("-created_at")[:8],
            "diretores": MembroDiretoria.objects.order_by(
                "-bienio_inicio", "ordem", "nome"
            )[:8],
        },
    )


def _salvar_noticia(form):
    noticia = form.save(commit=False)
    if noticia.publicada and noticia.publicada_em is None:
        noticia.publicada_em = timezone.now()
    noticia.save()
    form.save_m2m()
    return noticia


@conteudo_required
def noticia_nova(request):
    form = NoticiaForm(
        request.POST or None, request.FILES or None
    )
    if request.method == "POST" and form.is_valid():
        noticia = _salvar_noticia(form)
        messages.success(request, f"Notícia “{noticia.titulo}” salva com sucesso.")
        return redirect("conteudo-painel")
    return _render_editor(
        request,
        form,
        titulo="Nova notícia",
        subtitulo="Publique uma nova notícia no portal.",
        cancel_url=reverse("conteudo-painel"),
    )


@conteudo_required
def noticia_editar(request, pk):
    noticia = get_object_or_404(Noticia, pk=pk)
    form = NoticiaForm(
        request.POST or None, request.FILES or None, instance=noticia
    )
    if request.method == "POST" and form.is_valid():
        noticia = _salvar_noticia(form)
        messages.success(request, f"Notícia “{noticia.titulo}” atualizada.")
        return redirect("conteudo-painel")
    cancel_url = (
        reverse("noticia-detalhe", args=[noticia.slug])
        if noticia.publicada
        else reverse("conteudo-painel")
    )
    return _render_editor(
        request,
        form,
        titulo="Editar notícia",
        subtitulo=noticia.titulo,
        cancel_url=cancel_url,
    )


@conteudo_required
def noticia_excluir(request, pk):
    noticia = get_object_or_404(Noticia, pk=pk)
    return _confirmar_exclusao(
        request,
        noticia,
        titulo="Excluir notícia",
        descricao=f"Tem certeza de que deseja excluir “{noticia.titulo}”?",
        cancel_url=reverse("conteudo-painel"),
        success_url=reverse("conteudo-painel"),
        mensagem=f"Notícia “{noticia.titulo}” excluída.",
    )


@conteudo_required
def galeria_nova(request):
    form = GaleriaForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        galeria = form.save()
        messages.success(request, f"Galeria “{galeria.titulo}” salva com sucesso.")
        return redirect("conteudo-painel")
    return _render_editor(
        request,
        form,
        titulo="Nova galeria",
        subtitulo="Crie uma galeria para organizar as fotos.",
        cancel_url=reverse("conteudo-painel"),
    )


@conteudo_required
def galeria_editar(request, slug):
    galeria = get_object_or_404(Galeria, slug=slug)
    form = GaleriaForm(request.POST or None, instance=galeria)
    if request.method == "POST" and form.is_valid():
        galeria = form.save()
        messages.success(request, f"Galeria “{galeria.titulo}” atualizada.")
        return redirect("conteudo-painel")
    cancel_url = (
        reverse("galeria-detalhe", args=[galeria.slug])
        if galeria.publicada
        else reverse("conteudo-painel")
    )
    return _render_editor(
        request,
        form,
        titulo="Editar galeria",
        subtitulo=galeria.titulo,
        cancel_url=cancel_url,
    )


@conteudo_required
def galeria_excluir(request, slug):
    galeria = get_object_or_404(Galeria, slug=slug)
    return _confirmar_exclusao(
        request,
        galeria,
        titulo="Excluir galeria",
        descricao=(
            f"Tem certeza de que deseja excluir “{galeria.titulo}” e todas as suas fotos?"
        ),
        cancel_url=reverse("conteudo-painel"),
        success_url=reverse("conteudo-painel"),
        mensagem=f"Galeria “{galeria.titulo}” excluída.",
    )


@conteudo_required
def foto_nova(request, slug):
    galeria = get_object_or_404(Galeria, slug=slug)
    form = FotoForm(
        request.POST or None,
        request.FILES or None,
        initial={"galeria": galeria},
    )
    if request.method == "POST" and form.is_valid():
        foto = form.save()
        messages.success(request, "Foto adicionada à galeria.")
        if foto.galeria.publicada:
            return redirect("galeria-detalhe", slug=foto.galeria.slug)
        return redirect("conteudo-painel")
    return _render_editor(
        request,
        form,
        titulo="Adicionar foto",
        subtitulo=galeria.titulo,
        cancel_url=(
            reverse("galeria-detalhe", args=[galeria.slug])
            if galeria.publicada
            else reverse("conteudo-painel")
        ),
        submit_label="Adicionar foto",
    )


@conteudo_required
def foto_editar(request, pk):
    foto = get_object_or_404(Foto, pk=pk)
    form = FotoForm(
        request.POST or None, request.FILES or None, instance=foto
    )
    if request.method == "POST" and form.is_valid():
        foto = form.save()
        messages.success(request, "Foto atualizada.")
        if foto.galeria.publicada:
            return redirect("galeria-detalhe", slug=foto.galeria.slug)
        return redirect("conteudo-painel")
    return _render_editor(
        request,
        form,
        titulo="Editar foto",
        subtitulo=foto.galeria.titulo,
        cancel_url=reverse("galeria-detalhe", args=[foto.galeria.slug]),
    )


@conteudo_required
def foto_excluir(request, pk):
    foto = get_object_or_404(Foto, pk=pk)
    galeria = foto.galeria
    return _confirmar_exclusao(
        request,
        foto,
        titulo="Excluir foto",
        descricao="Tem certeza de que deseja excluir esta foto da galeria?",
        cancel_url=reverse("galeria-detalhe", args=[galeria.slug]),
        success_url=reverse("galeria-detalhe", args=[galeria.slug]),
        mensagem="Foto excluída.",
    )


@conteudo_required
def historia_nova(request):
    form = HistoriaForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        historia_obj = form.save()
        messages.success(request, f"História “{historia_obj.titulo}” salva.")
        return redirect("historia")
    return _render_editor(
        request,
        form,
        titulo="Novo conteúdo da história",
        subtitulo="Adicione um registro à linha do tempo institucional.",
        cancel_url=reverse("historia"),
    )


@conteudo_required
def historia_editar(request, pk):
    historia_obj = get_object_or_404(Historia, pk=pk)
    form = HistoriaForm(
        request.POST or None, request.FILES or None, instance=historia_obj
    )
    if request.method == "POST" and form.is_valid():
        historia_obj = form.save()
        messages.success(request, f"História “{historia_obj.titulo}” atualizada.")
        return redirect("historia")
    return _render_editor(
        request,
        form,
        titulo="Editar conteúdo da história",
        subtitulo=historia_obj.titulo,
        cancel_url=reverse("historia"),
    )


@conteudo_required
def historia_excluir(request, pk):
    historia_obj = get_object_or_404(Historia, pk=pk)
    return _confirmar_exclusao(
        request,
        historia_obj,
        titulo="Excluir conteúdo da história",
        descricao=f"Tem certeza de que deseja excluir “{historia_obj.titulo}”?",
        cancel_url=reverse("historia"),
        success_url=reverse("historia"),
        mensagem=f"História “{historia_obj.titulo}” excluída.",
    )


@conteudo_required
def diretor_novo(request):
    form = MembroDiretoriaForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        diretor = form.save()
        messages.success(request, f"Membro “{diretor.nome}” salvo na diretoria.")
        return redirect("diretoria")
    return _render_editor(
        request,
        form,
        titulo="Novo membro da diretoria",
        subtitulo="Inclua um membro e seu cargo no biênio correspondente.",
        cancel_url=reverse("diretoria"),
    )


@conteudo_required
def diretor_editar(request, pk):
    diretor = get_object_or_404(MembroDiretoria, pk=pk)
    form = MembroDiretoriaForm(
        request.POST or None, request.FILES or None, instance=diretor
    )
    if request.method == "POST" and form.is_valid():
        diretor = form.save()
        messages.success(request, f"Membro “{diretor.nome}” atualizado.")
        return redirect("diretoria")
    return _render_editor(
        request,
        form,
        titulo="Editar membro da diretoria",
        subtitulo=diretor.nome,
        cancel_url=reverse("diretoria"),
    )


@conteudo_required
def diretor_excluir(request, pk):
    diretor = get_object_or_404(MembroDiretoria, pk=pk)
    return _confirmar_exclusao(
        request,
        diretor,
        titulo="Excluir membro da diretoria",
        descricao=f"Tem certeza de que deseja excluir “{diretor.nome}”?",
        cancel_url=reverse("diretoria"),
        success_url=reverse("diretoria"),
        mensagem=f"Membro “{diretor.nome}” excluído da diretoria.",
    )
