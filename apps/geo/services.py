import json
import math

from django.db.models import Count

from apps.institutions.models import Igreja, Organizacao

from .models import Municipio

RAIO_TERRA_KM = 6371.0088


def haversine_km(lat1, lng1, lat2, lng2):
    lat1, lng1, lat2, lng2 = map(math.radians, (lat1, lng1, lat2, lng2))
    delta_lat = lat2 - lat1
    delta_lng = lng2 - lng1
    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lng / 2) ** 2
    )
    return 2 * RAIO_TERRA_KM * math.asin(math.sqrt(a))


def igrejas_para_mapa(tipo=None, associacao_id=None, municipio_id=None):
    qs = (
        Igreja.objects.filter(status=Igreja.Status.HOMOLOGADA, location__isnull=False)
        .select_related("associacao", "municipio")
        .prefetch_related("organizacoes")
    )
    if tipo:
        qs = qs.filter(organizacoes__tipo=tipo)
    if associacao_id:
        qs = qs.filter(associacao_id=associacao_id)
    if municipio_id:
        qs = qs.filter(municipio_id=municipio_id)
    return qs.distinct()


def serializar_igreja(igreja):
    return {
        "id": igreja.pk,
        "nome": igreja.nome_fantasia or igreja.razao_social,
        "pastor": igreja.pastor_titular,
        "municipio": igreja.municipio.nome,
        "associacao": igreja.associacao.nome,
        "lat": igreja.location.y,
        "lng": igreja.location.x,
        "organizacoes": [
            {"tipo": org.tipo, "dia": org.dia_reuniao, "horario": org.horario_reuniao}
            for org in igreja.organizacoes.all()
        ],
    }


def pontos_do_mapa(lat=None, lng=None, raio_km=None, **filtros):
    igrejas = list(igrejas_para_mapa(**filtros))
    if lat is not None and lng is not None and raio_km is not None:
        igrejas = [
            igreja
            for igreja in igrejas
            if haversine_km(lat, lng, igreja.location.y, igreja.location.x) <= raio_km
        ]
    return [serializar_igreja(igreja) for igreja in igrejas]


def municipios_geojson():
    contagens = {
        linha["municipio_id"]: linha["total"]
        for linha in Igreja.objects.filter(status=Igreja.Status.HOMOLOGADA)
        .values("municipio_id")
        .annotate(total=Count("id"))
    }
    features = []
    for municipio in Municipio.objects.exclude(geom__isnull=True).select_related():
        features.append(
            {
                "type": "Feature",
                "geometry": json.loads(municipio.geom.geojson),
                "properties": {
                    "id": municipio.pk,
                    "nome": municipio.nome,
                    "codigo_ibge": municipio.codigo_ibge,
                    "total_igrejas": contagens.get(municipio.pk, 0),
                },
            }
        )
    return {"type": "FeatureCollection", "features": features}


def tipos_organizacao():
    return [{"valor": valor, "rotulo": rotulo} for valor, rotulo in Organizacao.Tipo.choices]
