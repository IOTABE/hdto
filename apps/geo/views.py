from django.http import JsonResponse

from .services import municipios_geojson, pontos_do_mapa


def _int_param(request, name):
    try:
        return int(request.GET.get(name, ""))
    except (TypeError, ValueError):
        return None


def _float_param(request, name):
    try:
        return float(request.GET.get(name, ""))
    except (TypeError, ValueError):
        return None


def pontos(request):
    lat = _float_param(request, "lat")
    lng = _float_param(request, "lng")
    raio = _float_param(request, "raio")
    if lat is None or lng is None or raio is None:
        lat = lng = raio = None
    dados = pontos_do_mapa(
        lat=lat,
        lng=lng,
        raio_km=raio,
        tipo=request.GET.get("tipo") or None,
        associacao_id=_int_param(request, "associacao"),
        municipio_id=_int_param(request, "municipio"),
    )
    return JsonResponse({"pontos": dados, "total": len(dados)})


def municipios(request):
    return JsonResponse(municipios_geojson())
