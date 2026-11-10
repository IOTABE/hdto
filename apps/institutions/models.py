from django.conf import settings
from django.contrib.gis.db import models
from django.core.exceptions import ValidationError
from django.db.models import Q

from apps.core.models import TimeStampedModel
from apps.core.validators import normalize_cnpj, validate_cnpj


class AssociacaoRegional(TimeStampedModel):
    nome = models.CharField("nome", max_length=150, unique=True)
    sigla = models.CharField("sigla", max_length=20, unique=True)
    macrorregiao = models.CharField("macrorregião", max_length=80, blank=True)
    email = models.EmailField("e-mail", blank=True)
    telefone = models.CharField("telefone", max_length=20, blank=True)
    ativo = models.BooleanField("ativa", default=True)

    class Meta:
        verbose_name = "associação regional"
        verbose_name_plural = "associações regionais"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Igreja(TimeStampedModel):
    class Status(models.TextChoices):
        PENDENTE = "pendente", "Pendente"
        HOMOLOGADA = "homologada", "Homologada"
        INATIVA = "inativa", "Inativa"

    associacao = models.ForeignKey(
        AssociacaoRegional,
        on_delete=models.PROTECT,
        related_name="igrejas",
        verbose_name="associação regional",
    )
    municipio = models.ForeignKey(
        "geo.Municipio",
        on_delete=models.PROTECT,
        related_name="igrejas",
        verbose_name="município",
    )
    igreja_mae = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="congregacoes",
        verbose_name="igreja-mãe",
    )
    cnpj = models.CharField("CNPJ", max_length=14, unique=True, null=True, blank=True)
    razao_social = models.CharField("razão social", max_length=200)
    nome_fantasia = models.CharField("nome fantasia", max_length=200, blank=True)
    pastor_titular = models.CharField("pastor titular", max_length=150, blank=True)
    telefone = models.CharField("telefone", max_length=20, blank=True)
    email = models.EmailField("e-mail", blank=True)
    logradouro = models.CharField("logradouro", max_length=200, blank=True)
    bairro = models.CharField("bairro", max_length=100, blank=True)
    cep = models.CharField("CEP", max_length=9, blank=True)
    location = models.PointField("coordenadas", srid=4326, null=True, blank=True)
    status = models.CharField("status", max_length=20, choices=Status.choices, default=Status.PENDENTE)
    homologado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="igrejas_homologadas",
    )
    homologado_em = models.DateTimeField("homologado em", null=True, blank=True)

    class Meta:
        verbose_name = "igreja"
        verbose_name_plural = "igrejas"
        ordering = ["nome_fantasia", "razao_social"]
        constraints = [
            models.CheckConstraint(
                condition=~Q(status="homologada") | Q(homologado_em__isnull=False),
                name="igreja_homologada_tem_data",
            )
        ]

    def __str__(self):
        return self.nome_fantasia or self.razao_social

    def clean(self):
        super().clean()
        if self.cnpj:
            validate_cnpj(self.cnpj)
        elif not self.igreja_mae_id:
            raise ValidationError(
                {"igreja_mae": "Congregações sem CNPJ devem informar a igreja-mãe."}
            )
        if self.igreja_mae_id and self.pk and self.igreja_mae_id == self.pk:
            raise ValidationError({"igreja_mae": "Uma igreja não pode ser mãe de si mesma."})

    def save(self, *args, **kwargs):
        if self.cnpj:
            self.cnpj = normalize_cnpj(self.cnpj)
        super().save(*args, **kwargs)

    def homologar(self, usuario):
        from django.utils import timezone

        self.status = self.Status.HOMOLOGADA
        self.homologado_por = usuario
        self.homologado_em = timezone.now()
        self.save()


class Organizacao(TimeStampedModel):
    class Tipo(models.TextChoices):
        HD = "HD", "Homens Discípulos"
        ERV = "ERV", "Embaixadores do Rei Valentes"
        ER = "ER", "Embaixadores do Rei"

    class Status(models.TextChoices):
        ATIVA = "ativa", "Ativa"
        INATIVA = "inativa", "Inativa"

    igreja = models.ForeignKey(
        Igreja,
        on_delete=models.PROTECT,
        related_name="organizacoes",
        verbose_name="igreja",
    )
    tipo = models.CharField("tipo", max_length=10, choices=Tipo.choices)
    data_fundacao = models.DateField("data de fundação", null=True, blank=True)
    lider_nome = models.CharField("líder/conselheiro", max_length=150, blank=True)
    lider_contato = models.CharField("contato do líder", max_length=20, blank=True)
    dia_reuniao = models.CharField("dia das reuniões", max_length=30, blank=True)
    horario_reuniao = models.TimeField("horário das reuniões", null=True, blank=True)
    status = models.CharField("status", max_length=20, choices=Status.choices, default=Status.ATIVA)

    class Meta:
        verbose_name = "organização local"
        verbose_name_plural = "organizações locais"
        ordering = ["igreja", "tipo"]
        constraints = [
            models.UniqueConstraint(fields=["igreja", "tipo"], name="organizacao_unica_por_tipo"),
        ]

    def __str__(self):
        return f"{self.get_tipo_display()} — {self.igreja}"

    def clean(self):
        super().clean()
        if self._state.adding and self.igreja_id:
            igreja = self.igreja
            if igreja.status != Igreja.Status.HOMOLOGADA:
                raise ValidationError(
                    {"igreja": "A igreja precisa estar homologada para ativar organizações."}
                )
