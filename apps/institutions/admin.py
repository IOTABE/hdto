from django.contrib import admin

from .models import AssociacaoRegional, Igreja, Organizacao


@admin.register(AssociacaoRegional)
class AssociacaoRegionalAdmin(admin.ModelAdmin):
    list_display = ["nome", "sigla", "macrorregiao", "ativo"]
    search_fields = ["nome", "sigla"]
    list_filter = ["ativo", "macrorregiao"]


@admin.register(Igreja)
class IgrejaAdmin(admin.ModelAdmin):
    list_display = ["nome_fantasia", "razao_social", "municipio", "associacao", "status"]
    search_fields = ["nome_fantasia", "razao_social", "cnpj"]
    list_filter = ["status", "associacao", "municipio"]
    readonly_fields = ["homologado_por", "homologado_em"]
    actions = ["homologar_igrejas"]

    @admin.action(description="Homologar igrejas selecionadas")
    def homologar_igrejas(self, request, queryset):
        for igreja in queryset:
            igreja.homologar(request.user)
        self.message_user(request, f"{queryset.count()} igreja(s) homologada(s).")


@admin.register(Organizacao)
class OrganizacaoAdmin(admin.ModelAdmin):
    list_display = ["igreja", "tipo", "status", "lider_nome", "dia_reuniao"]
    list_filter = ["tipo", "status", "igreja__associacao"]
    search_fields = ["igreja__nome_fantasia", "lider_nome"]
