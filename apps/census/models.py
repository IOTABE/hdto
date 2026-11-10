from django.db import models

from apps.core.models import TimeStampedModel


class RespostaCenso(TimeStampedModel):
    class Escolaridade(models.TextChoices):
        FUNDAMENTAL = "fundamental", "Ensino Fundamental"
        MEDIO = "medio", "Ensino Médio"
        TECNICO = "tecnico", "Ensino Técnico"
        SUPERIOR = "superior", "Ensino Superior"
        POS_GRADUACAO = "pos_graduacao", "Pós-graduação"

    class AreaAtuacao(models.TextChoices):
        CONSTRUCAO_CIVIL = "construcao_civil", "Construção civil"
        SAUDE = "saude", "Saúde"
        LOGISTICA = "logistica", "Logística"
        ENSINO = "ensino", "Ensino"
        ADMINISTRATIVO = "administrativo", "Administrativo"
        OUTRO = "outro", "Outro"

    membro = models.OneToOneField(
        "members.Membro",
        on_delete=models.CASCADE,
        related_name="censo",
        verbose_name="membro",
    )
    escolaridade = models.CharField(
        "escolaridade", max_length=20, choices=Escolaridade.choices, blank=True
    )
    area_atuacao = models.CharField(
        "área de atuação", max_length=30, choices=AreaAtuacao.choices, blank=True
    )
    competencias = models.TextField("competências técnicas", blank=True)
    ministerio_socorro = models.CharField("ministério de socorro", max_length=150, blank=True)
    disponivel_voluntariado = models.BooleanField("disponível para voluntariado", default=False)
    versao_formulario = models.CharField("versão do formulário", max_length=10, default="1.0")

    class Meta:
        verbose_name = "resposta do censo"
        verbose_name_plural = "respostas do censo"
        ordering = ["membro__nome_completo"]

    def __str__(self):
        return f"Censo de {self.membro}"
