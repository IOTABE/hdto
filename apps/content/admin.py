from django.contrib import admin

from .models import Documento, Foto, Galeria, Noticia, PaginaInstitucional


class FotoInline(admin.TabularInline):
    model = Foto
    extra = 1


@admin.register(PaginaInstitucional)
class PaginaInstitucionalAdmin(admin.ModelAdmin):
    list_display = ["titulo", "slug", "publicada", "ordem"]
    list_filter = ["publicada"]
    prepopulated_fields = {"slug": ("titulo",)}


@admin.register(Noticia)
class NoticiaAdmin(admin.ModelAdmin):
    list_display = ["titulo", "publicada", "publicada_em", "autor"]
    list_filter = ["publicada"]
    search_fields = ["titulo", "resumo", "conteudo"]
    prepopulated_fields = {"slug": ("titulo",)}


@admin.register(Galeria)
class GaleriaAdmin(admin.ModelAdmin):
    list_display = ["titulo", "slug", "publicada"]
    list_filter = ["publicada"]
    prepopulated_fields = {"slug": ("titulo",)}
    inlines = [FotoInline]


@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
    list_display = ["titulo", "publico"]
    list_filter = ["publico"]
