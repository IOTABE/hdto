import json
from gzip import decompress
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from django.contrib.gis.geos import GEOSGeometry, MultiPolygon
from django.core.management.base import BaseCommand, CommandError

from apps.geo.models import Municipio


class Command(BaseCommand):
    help = (
        "Importa os municípios do Tocantins a partir de um GeoJSON do IBGE. "
        "Quando o GeoJSON não traz o nome, busca os nomes na API de localidades do IBGE."
    )

    def add_arguments(self, parser):
        parser.add_argument("--arquivo", required=True, help="Caminho do GeoJSON do IBGE")
        parser.add_argument("--uf", default="TO", help="UF usada para buscar nomes (padrão: TO)")

    def _nomes_ibge(self, uf):
        url = f"https://servicodados.ibge.gov.br/api/v1/localidades/estados/{uf}/municipios"
        try:
            with urlopen(url, timeout=30) as resposta:
                conteudo = resposta.read()
            if conteudo[:2] == b"\x1f\x8b":
                conteudo = decompress(conteudo)
            dados = json.loads(conteudo.decode("utf-8"))
            return {str(municipio["id"]): municipio["nome"] for municipio in dados}
        except (HTTPError, URLError, OSError, ValueError, KeyError) as exc:
            self.stderr.write(
                self.style.WARNING(
                    f"Não foi possível consultar os nomes no IBGE ({exc}); "
                    "use um GeoJSON que já contenha 'nome'."
                )
            )
            return {}

    def handle(self, *args, **options):
        caminho = options["arquivo"]
        uf = options["uf"].upper()
        try:
            with open(caminho, encoding="utf-8") as arquivo:
                dados = json.load(arquivo)
        except (OSError, json.JSONDecodeError) as exc:
            raise CommandError(f"Não foi possível ler o arquivo: {exc}") from exc

        features = dados.get("features") if isinstance(dados, dict) else None
        if not features:
            raise CommandError("GeoJSON inválido: nenhuma feature encontrada.")

        nomes_ibge = None
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
            if not codigo or not geometria:
                ignorados += 1
                continue

            codigo = str(codigo)[:7]
            if not nome:
                if nomes_ibge is None:
                    nomes_ibge = self._nomes_ibge(uf)
                nome = nomes_ibge.get(codigo)
            if not nome:
                ignorados += 1
                continue

            geom = GEOSGeometry(json.dumps(geometria), srid=4326)
            if geom.geom_type == "Polygon":
                geom = MultiPolygon(geom, srid=4326)
            if geom.geom_type != "MultiPolygon":
                ignorados += 1
                continue

            _, criado = Municipio.objects.update_or_create(
                codigo_ibge=codigo,
                defaults={"nome": nome, "geom": geom, "uf": uf},
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
