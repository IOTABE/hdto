from django.conf import settings
from django.db import connection
from django.http import JsonResponse
from django.views.static import serve


def health(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        return JsonResponse({"status": "error", "database": "unavailable"}, status=503)
    return JsonResponse({"status": "ok", "database": "ok"})


def media(request, path):
    return serve(request, path, document_root=settings.MEDIA_ROOT)
