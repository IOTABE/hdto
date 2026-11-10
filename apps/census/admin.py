from django.contrib import admin

from .models import RespostaCenso


@admin.register(RespostaCenso)
class RespostaCensoAdmin(admin.ModelAdmin):
    list_display = ["membro", "escolaridade", "area_atuacao", "disponivel_voluntariado"]
    list_filter = ["escolaridade", "area_atuacao", "disponivel_voluntariado"]
    search_fields = ["membro__nome_completo", "competencias"]
