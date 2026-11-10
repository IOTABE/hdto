import json

from django.contrib.gis.geos import GEOSGeometry, MultiPolygon
from django.core.management.base import BaseCommand, CommandError

from apps.geo.models import Municipio


class Command(BaseCommand):
    help = "Importa os municípios do Tocantins a partir de um GeoJSON do IBGE."

    def add_arguments(self, parser):
        parser.add_argument("--arquivo", required=True, help="Caminho do GeoJSON do IBGE")

    def handle(self, *args, **options):
        caminho = options["arquivo"]
        try:
            with open(caminho, encoding="utf-8") as arquivo:
                dados = json.load(arquivo)
        except (OSError, json.JSONDecodeError) as exc:
            raise CommandError(f"Não foi possível ler o arquivo: {exc}") from exc

        features = dados.get("features") if isinstance(dados, dict) else None
        if not features:
            raise CommandError("GeoJSON inválido: nenhuma feature encontrada.")

        criados = atualizados = ignorados = 0
        for feature in features:
            propriedades = feature.get("properties") or {}
            codigo = (
                propriedades.get("codarea")
                or propriedades.get("codigo_ibge")
                or propriedades.get("id")
            )
            nome = propriedades.get("nome") or propriedades.get("name")
            geometria = feature.get("geometry")
            if not codigo or not nome or not geometria:
                ignorados += 1
                continue

            geom = GEOSGeometry(json.dumps(geometria), srid=4326)
            if geom.geom_type == "Polygon":
                geom = MultiPolygon(geom, srid=4326)
            if geom.geom_type != "MultiPolygon":
                ignorados += 1
                continue

            _, criado = Municipio.objects.update_or_create(
                codigo_ibge=str(codigo)[:7],
                defaults={"nome": nome, "geom": geom, "uf": "TO"},
            )
            if criado:
                criados += 1
            else:
                atualizados += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Importação concluída: {criados} criados, {atualizados} atualizados, "
                f"{ignorados} ignorados."
            )
        )
