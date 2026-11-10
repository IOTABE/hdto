from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from apps.events.models import Evento

from .models import Galeria, Noticia, PaginaInstitucional


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
