import io
import json
from unittest.mock import patch

import pytest
from django.contrib.gis.geos import Point
from django.core.management import call_command
from django.urls import reverse
from django.utils import timezone

from apps.geo.models import Municipio
from apps.institutions.models import AssociacaoRegional, Igreja, Organizacao

PALMAS = (-10.18, -48.33)
GURUPI = (-11.73, -49.07)


def make_igreja(assoc, municipio, cnpj, nome, ponto):
    lat, lng = ponto
    return Igreja.objects.create(
        associacao=assoc,
        municipio=municipio,
        cnpj=cnpj,
        razao_social=nome,
        nome_fantasia=nome,
        pastor_titular="Pastor Teste",
        location=Point(lng, lat, srid=4326),
        status=Igreja.Status.HOMOLOGADA,
        homologado_em=timezone.now(),
    )


@pytest.fixture
def mapa(db):
    assoc = AssociacaoRegional.objects.create(nome="Associação Norte", sigla="NORTE")
    palmas = Municipio.objects.create(nome="Palmas", codigo_ibge="1721000")
    gurupi = Municipio.objects.create(nome="Gurupi", codigo_ibge="1709500")
    igreja_palmas = make_igreja(assoc, palmas, "11222333000181", "PIB Palmas", PALMAS)
    igreja_gurupi = make_igreja(assoc, gurupi, "11444777000161", "PIB Gurupi", GURUPI)
    Organizacao.objects.create(igreja=igreja_palmas, tipo=Organizacao.Tipo.ER)
    Organizacao.objects.create(igreja=igreja_gurupi, tipo=Organizacao.Tipo.HD)
    return {
        "assoc": assoc,
        "palmas": palmas,
        "gurupi": gurupi,
        "igreja_palmas": igreja_palmas,
        "igreja_gurupi": igreja_gurupi,
    }


@pytest.mark.django_db
def test_pontos_do_mapa_publico(client, mapa):
    response = client.get(reverse("mapa-pontos"))
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    nomes = {ponto["nome"] for ponto in data["pontos"]}
    assert nomes == {"PIB Palmas", "PIB Gurupi"}


@pytest.mark.django_db
def test_filtro_por_tipo_de_organizacao(client, mapa):
    response = client.get(reverse("mapa-pontos") + "?tipo=ER")
    data = response.json()
    assert data["total"] == 1
    assert data["pontos"][0]["nome"] == "PIB Palmas"
    assert data["pontos"][0]["organizacoes"][0]["tipo"] == "ER"


@pytest.mark.django_db
def test_filtro_por_proximidade(client, mapa):
    lat, lng = PALMAS
    response = client.get(reverse("mapa-pontos") + f"?lat={lat}&lng={lng}&raio=50")
    data = response.json()
    assert data["total"] == 1
    assert data["pontos"][0]["nome"] == "PIB Palmas"


@pytest.mark.django_db
def test_importar_municipios_geojson(tmp_path):
    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"codarea": "1721000", "nome": "Palmas"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [-48.4, -10.3],
                            [-48.2, -10.3],
                            [-48.2, -10.1],
                            [-48.4, -10.1],
                            [-48.4, -10.3],
                        ]
                    ],
                },
            }
        ],
    }
    arquivo = tmp_path / "municipios.geojson"
    arquivo.write_text(json.dumps(geojson), encoding="utf-8")

    call_command("importar_municipios_to", arquivo=str(arquivo))

    municipio = Municipio.objects.get(codigo_ibge="1721000")
    assert municipio.nome == "Palmas"
    assert municipio.geom is not None
    assert municipio.geom.srid == 4326


@pytest.mark.django_db
def test_importar_municipios_busca_nome_no_ibge(tmp_path):
    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"codarea": "1721000"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [-48.4, -10.3],
                            [-48.2, -10.3],
                            [-48.2, -10.1],
                            [-48.4, -10.1],
                            [-48.4, -10.3],
                        ]
                    ],
                },
            }
        ],
    }
    arquivo = tmp_path / "municipios.geojson"
    arquivo.write_text(json.dumps(geojson), encoding="utf-8")

    localidades = io.BytesIO(
        json.dumps([{"id": 1721000, "nome": "Palmas"}]).encode("utf-8")
    )
    with patch(
        "apps.geo.management.commands.importar_municipios_to.urlopen",
        return_value=localidades,
    ):
        call_command("importar_municipios_to", arquivo=str(arquivo))

    assert Municipio.objects.get(codigo_ibge="1721000").nome == "Palmas"


@pytest.mark.django_db
def test_municipios_geojson(client, tmp_path, mapa):
    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"codarea": "1721000", "nome": "Palmas"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [-48.4, -10.3],
                            [-48.2, -10.3],
                            [-48.2, -10.1],
                            [-48.4, -10.1],
                            [-48.4, -10.3],
                        ]
                    ],
                },
            }
        ],
    }
    arquivo = tmp_path / "municipios.geojson"
    arquivo.write_text(json.dumps(geojson), encoding="utf-8")
    call_command("importar_municipios_to", arquivo=str(arquivo))

    response = client.get(reverse("mapa-municipios"))
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) == 1
    assert data["features"][0]["properties"]["nome"] == "Palmas"
