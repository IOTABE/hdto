from django.db import models

from apps.core.models import TimeStampedModel


class PaginaInstitucional(TimeStampedModel):
    slug = models.SlugField("slug", max_length=120, unique=True)
    titulo = models.CharField("título", max_length=180)
    resumo = models.TextField("resumo", blank=True)
    conteudo = models.TextField("conteúdo", blank=True)
    publicada = models.BooleanField("publicada", default=True)
    ordem = models.PositiveIntegerField("ordem", default=0)

    class Meta:
        verbose_name = "página institucional"
        verbose_name_plural = "páginas institucionais"
        ordering = ["ordem", "titulo"]

    def __str__(self):
        return self.titulo


class Noticia(TimeStampedModel):
    slug = models.SlugField("slug", max_length=140, unique=True)
    titulo = models.CharField("título", max_length=180)
    resumo = models.TextField("resumo", blank=True)
    conteudo = models.TextField("conteúdo", blank=True)
    imagem = models.ImageField("imagem", upload_to="noticias/", null=True, blank=True)
    autor = models.CharField("autor", max_length=120, blank=True)
    publicada = models.BooleanField("publicada", default=False)
    publicada_em = models.DateTimeField("publicada em", null=True, blank=True)

    class Meta:
        verbose_name = "notícia"
        verbose_name_plural = "notícias"
        ordering = ["-publicada_em", "-created_at"]

    def __str__(self):
        return self.titulo


class Galeria(TimeStampedModel):
    slug = models.SlugField("slug", max_length=140, unique=True)
    titulo = models.CharField("título", max_length=180)
    descricao = models.TextField("descrição", blank=True)
    publicada = models.BooleanField("publicada", default=True)

    class Meta:
        verbose_name = "galeria"
        verbose_name_plural = "galerias"
        ordering = ["-created_at"]

    def __str__(self):
        return self.titulo


class Foto(TimeStampedModel):
    galeria = models.ForeignKey(
        Galeria, on_delete=models.CASCADE, related_name="fotos", verbose_name="galeria"
    )
    imagem = models.ImageField("imagem", upload_to="galerias/")
    legenda = models.CharField("legenda", max_length=180, blank=True)
    ordem = models.PositiveIntegerField("ordem", default=0)

    class Meta:
        verbose_name = "foto"
        verbose_name_plural = "fotos"
        ordering = ["ordem", "created_at"]

    def __str__(self):
        return self.legenda or f"Foto {self.pk}"


class Documento(TimeStampedModel):
    titulo = models.CharField("título", max_length=180)
    arquivo = models.FileField("arquivo", upload_to="documentos/")
    publico = models.BooleanField("público", default=True)

    class Meta:
        verbose_name = "documento"
        verbose_name_plural = "documentos"
        ordering = ["titulo"]

    def __str__(self):
        return self.titulo
