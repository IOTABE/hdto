import json
from gzip import decompress
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from django.contrib.gis.geos import GEOSGeometry, MultiPolygon, Point
from django.core.management.base import BaseCommand, CommandError

from apps.geo.models import Municipio

REFERENCIA_PADRAO = Path(__file__).resolve().parents[2] / "data" / "municipios_to_referencia.json"


class Command(BaseCommand):
    help = (
        "Importa os municípios do Tocantins a partir de um GeoJSON do IBGE. "
        "Aceita GeoJSON só com geometria: nesse caso identifica o município pela "
        "referência local (código/nome/ponto) e, se faltar o nome, consulta a API "
        "de localidades do IBGE."
    )

    def add_arguments(self, parser):
        parser.add_argument("--arquivo", required=True, help="Caminho do GeoJSON do IBGE")
        parser.add_argument("--uf", default="TO", help="UF usada para buscar nomes (padrão: TO)")
        parser.add_argument(
            "--referencia",
            default=None,
            help=(
                "JSON com codigo_ibge, nome e ponto de referência para completar "
                "GeoJSON sem propriedades. Padrão: "
                "apps/geo/data/municipios_to_referencia.json"
            ),
        )

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

    def _carregar_referencia(self, caminho):
        if self._referencia is not None:
            return self._referencia

        self._referencia = {}
        caminho = Path(caminho) if caminho else REFERENCIA_PADRAO
        try:
            with caminho.open(encoding="utf-8") as arquivo:
                dados = json.load(arquivo)
        except (OSError, json.JSONDecodeError) as exc:
            self.stderr.write(
                self.style.WARNING(
                    f"Não foi possível ler a referência de municípios ({exc})."
                )
            )
            return self._referencia

        for item in dados if isinstance(dados, list) else []:
            codigo = str(item.get("codigo_ibge") or "").strip()
            nome = str(item.get("nome") or "").strip()
            ponto = item.get("ponto")
            if not codigo or not nome:
                continue
            if not isinstance(ponto, (list, tuple)) or len(ponto) != 2:
                continue
            try:
                ponto = Point(float(ponto[0]), float(ponto[1]), srid=4326)
            except (TypeError, ValueError):
                continue
            self._por_codigo[codigo] = nome
            self._por_nome[nome.casefold()] = codigo
            self._pontos.append((codigo, ponto))

        return self._referencia

    def _codigo_por_geometria(self, geom):
        alvo = geom.point_on_surface
        candidatos = [
            (codigo, ponto) for codigo, ponto in self._pontos if geom.covers(ponto)
        ]
        if not candidatos:
            return None
        if len(candidatos) == 1:
            return candidatos[0][0]
        return min(candidatos, key=lambda item: item[1].distance(alvo))[0]

    def handle(self, *args, **options):
        caminho = options["arquivo"]
        uf = options["uf"].upper()
        referencia = options.get("referencia")
        try:
            with open(caminho, encoding="utf-8") as arquivo:
                dados = json.load(arquivo)
        except (OSError, json.JSONDecodeError) as exc:
            raise CommandError(f"Não foi possível ler o arquivo: {exc}") from exc

        features = dados.get("features") if isinstance(dados, dict) else None
        if not features:
            raise CommandError("GeoJSON inválido: nenhuma feature encontrada.")

        self._referencia = None
        self._por_codigo = {}
        self._por_nome = {}
        self._pontos = []

        nomes_ibge = None
        criados = atualizados = ignorados = 0
        for feature in features:
            propriedades = feature.get("properties") or {}
            codigo = (
                propriedades.get("codarea")
                or propriedades.get("codigo_ibge")
                or propriedades.get("id")
            )
            if not codigo:
                id_feature = str(feature.get("id") or "").strip()
                if id_feature.isdigit() and len(id_feature) >= 7:
                    codigo = id_feature
            nome = propriedades.get("nome") or propriedades.get("name")
            geometria = feature.get("geometry")
            if not geometria:
                ignorados += 1
                continue

            try:
                geom = GEOSGeometry(json.dumps(geometria), srid=4326)
            except (TypeError, ValueError):
                ignorados += 1
                continue
            if geom.geom_type == "Polygon":
                geom = MultiPolygon(geom, srid=4326)
            if geom.geom_type != "MultiPolygon":
                ignorados += 1
                continue

            if codigo:
                codigo = str(codigo)[:7]
            else:
                self._carregar_referencia(referencia)
                if nome:
                    codigo = self._por_nome.get(str(nome).strip().casefold())
                if not codigo:
                    codigo = self._codigo_por_geometria(geom)
            if not codigo:
                ignorados += 1
                continue

            if not nome:
                self._carregar_referencia(referencia)
                nome = self._por_codigo.get(codigo)
            if not nome:
                if nomes_ibge is None:
                    nomes_ibge = self._nomes_ibge(uf)
                nome = nomes_ibge.get(codigo)
            if not nome:
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
