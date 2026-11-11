from django.core.exceptions import ValidationError
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


class Historia(TimeStampedModel):
    titulo = models.CharField("título", max_length=180)
    resumo = models.TextField("resumo", blank=True)
    conteudo = models.TextField("conteúdo")
    imagem = models.ImageField(
        "imagem", upload_to="institucional/historia/", null=True, blank=True
    )
    publicada = models.BooleanField("publicada", default=True)
    ordem = models.PositiveIntegerField("ordem", default=0)

    class Meta:
        verbose_name = "conteúdo da história"
        verbose_name_plural = "conteúdos da história"
        ordering = ["ordem", "-created_at"]

    def __str__(self):
        return self.titulo


class MembroDiretoria(TimeStampedModel):
    nome = models.CharField("nome", max_length=150)
    cargo = models.CharField("cargo", max_length=120)
    bienio_inicio = models.PositiveSmallIntegerField("início do biênio")
    bienio_fim = models.PositiveSmallIntegerField("fim do biênio")
    foto = models.ImageField(
        "foto", upload_to="institucional/diretoria/", null=True, blank=True
    )
    bio = models.TextField("biografia", blank=True)
    email = models.EmailField("e-mail", blank=True)
    telefone = models.CharField("telefone", max_length=20, blank=True)
    publicada = models.BooleanField("publicada", default=True)
    ordem = models.PositiveIntegerField("ordem", default=0)

    class Meta:
        verbose_name = "membro da diretoria"
        verbose_name_plural = "membros da diretoria"
        ordering = ["-bienio_inicio", "ordem", "nome"]

    def __str__(self):
        return f"{self.nome} — {self.cargo} ({self.bienio})"

    @property
    def bienio(self):
        return f"{self.bienio_inicio}–{self.bienio_fim}"

    def clean(self):
        super().clean()
        if self.bienio_fim <= self.bienio_inicio:
            raise ValidationError(
                {"bienio_fim": "O ano final do biênio deve ser maior que o inicial."}
            )


class Contato(TimeStampedModel):
    class Canal(models.TextChoices):
        EMAIL = "email", "E-mail"
        WHATSAPP = "whatsapp", "WhatsApp"
        LOCAL = "local", "Registro local"

    class Status(models.TextChoices):
        REGISTRADO = "registrado", "Registrado"
        ENVIADO = "enviado", "Enviado"
        FALHA_ENVIO = "falha_envio", "Falha no envio"

    nome = models.CharField("nome", max_length=150)
    email = models.EmailField("e-mail", blank=True)
    telefone = models.CharField("telefone", max_length=20, blank=True)
    assunto = models.CharField("assunto", max_length=180)
    mensagem = models.TextField("mensagem")
    canal = models.CharField(
        "canal de envio", max_length=20, choices=Canal.choices, default=Canal.EMAIL
    )
    status = models.CharField(
        "status", max_length=20, choices=Status.choices, default=Status.REGISTRADO
    )
    ip = models.GenericIPAddressField("IP de origem", null=True, blank=True)
    enviado_em = models.DateTimeField("enviado em", null=True, blank=True)

    class Meta:
        verbose_name = "contato"
        verbose_name_plural = "contatos"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.nome} — {self.assunto}"


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
