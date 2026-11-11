from django.contrib import admin

from .models import (
    Contato,
    Documento,
    Foto,
    Galeria,
    Historia,
    MembroDiretoria,
    Noticia,
    PaginaInstitucional,
)


class FotoInline(admin.TabularInline):
    model = Foto
    extra = 1


@admin.register(PaginaInstitucional)
class PaginaInstitucionalAdmin(admin.ModelAdmin):
    list_display = ["titulo", "slug", "publicada", "ordem"]
    list_filter = ["publicada"]
    prepopulated_fields = {"slug": ("titulo",)}


@admin.register(Historia)
class HistoriaAdmin(admin.ModelAdmin):
    list_display = ["titulo", "publicada", "ordem", "updated_at"]
    list_filter = ["publicada"]
    search_fields = ["titulo", "resumo", "conteudo"]
    list_editable = ["publicada", "ordem"]


@admin.register(MembroDiretoria)
class MembroDiretoriaAdmin(admin.ModelAdmin):
    list_display = ["nome", "cargo", "bienio", "publicada", "ordem"]
    list_filter = ["publicada", "bienio_inicio"]
    search_fields = ["nome", "cargo", "bio"]
    ordering = ["-bienio_inicio", "ordem", "nome"]


@admin.register(Contato)
class ContatoAdmin(admin.ModelAdmin):
    list_display = ["nome", "assunto", "canal", "status", "created_at"]
    list_filter = ["canal", "status"]
    search_fields = ["nome", "email", "telefone", "assunto", "mensagem"]
    readonly_fields = ["created_at", "updated_at", "enviado_em", "ip"]
    date_hierarchy = "created_at"


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
