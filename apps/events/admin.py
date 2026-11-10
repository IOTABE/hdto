from django.contrib import admin

from .models import Evento, EventoArquivo, Inscricao


class InscricaoInline(admin.TabularInline):
    model = Inscricao
    extra = 0
    readonly_fields = ["token", "checkin_em"]


@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    list_display = ["titulo", "tipo", "abrangencia", "inicio", "fim", "inscricoes_abertas"]
    list_filter = ["tipo", "abrangencia", "inscricoes_abertas"]
    search_fields = ["titulo", "local_nome"]
    inlines = [InscricaoInline]


@admin.register(Inscricao)
class InscricaoAdmin(admin.ModelAdmin):
    list_display = ["membro", "evento", "status", "checkin_em"]
    list_filter = ["status", "evento"]
    search_fields = ["membro__nome_completo", "evento__titulo"]
    readonly_fields = ["token", "checkin_em"]


@admin.register(EventoArquivo)
class EventoArquivoAdmin(admin.ModelAdmin):
    list_display = ["titulo", "evento"]
    search_fields = ["titulo"]
