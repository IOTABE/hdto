import uuid

from django.contrib.gis.db import models
from django.core.exceptions import ValidationError
from django.db import models as db_models
from django.urls import reverse
from django.utils import timezone

from apps.core.models import TimeStampedModel


class Evento(TimeStampedModel):
    class Tipo(db_models.TextChoices):
        CONGRESSO = "congresso", "Congresso"
        ACAMPAMENTO = "acampamento", "Acampamento"
        SIMPOSIO = "simposio", "Simpósio"
        ACAO_SOCIAL = "acao_social", "Ação social"
        OUTRO = "outro", "Outro"

    class Abrangencia(db_models.TextChoices):
        ESTADUAL = "estadual", "Estadual"
        REGIONAL = "regional", "Regional"
        LOCAL = "local", "Local"

    titulo = db_models.CharField("título", max_length=200)
    tipo = db_models.CharField("tipo", max_length=20, choices=Tipo.choices)
    abrangencia = db_models.CharField(
        "abrangência", max_length=20, choices=Abrangencia.choices, default=Abrangencia.ESTADUAL
    )
    associacao = db_models.ForeignKey(
        "institutions.AssociacaoRegional",
        on_delete=db_models.PROTECT,
        null=True,
        blank=True,
        related_name="eventos",
        verbose_name="associação regional",
    )
    igreja = db_models.ForeignKey(
        "institutions.Igreja",
        on_delete=db_models.PROTECT,
        null=True,
        blank=True,
        related_name="eventos",
        verbose_name="igreja",
    )
    inicio = db_models.DateTimeField("início")
    fim = db_models.DateTimeField("fim")
    local_nome = db_models.CharField("local", max_length=200, blank=True)
    endereco = db_models.CharField("endereço", max_length=255, blank=True)
    location = models.PointField("coordenadas", srid=4326, null=True, blank=True)
    descricao = db_models.TextField("descrição", blank=True)
    banner = db_models.ImageField("banner", upload_to="eventos/", null=True, blank=True)
    capacidade = db_models.PositiveIntegerField("capacidade", null=True, blank=True)
    inscricoes_abertas = db_models.BooleanField("inscrições abertas", default=True)

    class Meta:
        verbose_name = "evento"
        verbose_name_plural = "eventos"
        ordering = ["inicio"]

    def __str__(self):
        return self.titulo

    def clean(self):
        super().clean()
        if self.abrangencia == self.Abrangencia.REGIONAL and not self.associacao_id:
            raise ValidationError({"associacao": "Eventos regionais exigem associação."})
        if self.abrangencia == self.Abrangencia.LOCAL and not self.igreja_id:
            raise ValidationError({"igreja": "Eventos locais exigem igreja."})
        if self.inicio and self.fim and self.fim < self.inicio:
            raise ValidationError({"fim": "O término deve ser posterior ao início."})

    def esta_aberto(self):
        return self.inscricoes_abertas and self.fim >= timezone.now()


class Inscricao(TimeStampedModel):
    class Status(db_models.TextChoices):
        CONFIRMADA = "confirmada", "Confirmada"
        CANCELADA = "cancelada", "Cancelada"
        PRESENTE = "presente", "Presente"

    evento = db_models.ForeignKey(
        Evento, on_delete=db_models.CASCADE, related_name="inscricoes", verbose_name="evento"
    )
    membro = db_models.ForeignKey(
        "members.Membro",
        on_delete=db_models.CASCADE,
        related_name="inscricoes",
        verbose_name="membro",
    )
    status = db_models.CharField(
        "status", max_length=20, choices=Status.choices, default=Status.CONFIRMADA
    )
    token = db_models.UUIDField("token", default=uuid.uuid4, unique=True, editable=False)
    checkin_em = db_models.DateTimeField("check-in em", null=True, blank=True)

    class Meta:
        verbose_name = "inscrição"
        verbose_name_plural = "inscrições"
        ordering = ["-created_at"]
        constraints = [
            db_models.UniqueConstraint(fields=["evento", "membro"], name="inscricao_unica"),
        ]

    def __str__(self):
        return f"{self.membro} — {self.evento}"

    def realizar_checkin(self):
        self.status = self.Status.PRESENTE
        self.checkin_em = timezone.now()
        self.save(update_fields=["status", "checkin_em", "updated_at"])

    def get_checkin_url(self):
        return reverse("evento-checkin", args=[self.token])


class EventoArquivo(TimeStampedModel):
    evento = db_models.ForeignKey(
        Evento, on_delete=db_models.CASCADE, related_name="arquivos", verbose_name="evento"
    )
    titulo = db_models.CharField("título", max_length=150)
    arquivo = db_models.FileField("arquivo", upload_to="eventos/arquivos/")

    class Meta:
        verbose_name = "arquivo do evento"
        verbose_name_plural = "arquivos do evento"

    def __str__(self):
        return self.titulo
