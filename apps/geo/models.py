from django.contrib.gis.db import models

from apps.core.models import TimeStampedModel


class Municipio(TimeStampedModel):
    nome = models.CharField("nome", max_length=120)
    codigo_ibge = models.CharField("código IBGE", max_length=7, unique=True)
    uf = models.CharField("UF", max_length=2, default="TO")
    geom = models.MultiPolygonField("polígono", srid=4326, null=True, blank=True)

    class Meta:
        verbose_name = "município"
        verbose_name_plural = "municípios"
        ordering = ["nome"]

    def __str__(self):
        return f"{self.nome}/{self.uf}"
