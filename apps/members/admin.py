from django.contrib import admin

from .models import Consentimento, Membro, ResponsavelLegal, RevogacaoConsentimento, TermoVersao


@admin.register(TermoVersao)
class TermoVersaoAdmin(admin.ModelAdmin):
    list_display = ["versao", "vigente", "created_at"]
    list_filter = ["vigente"]


@admin.register(ResponsavelLegal)
class ResponsavelLegalAdmin(admin.ModelAdmin):
    list_display = ["nome", "parentesco", "email", "telefone"]
    search_fields = ["nome", "cpf_hash"]


@admin.register(Membro)
class MembroAdmin(admin.ModelAdmin):
    list_display = ["nome_completo", "igreja", "idade", "status", "profissao", "responsavel"]
    list_filter = ["status", "estado_civil", "igreja", "organizacoes"]
    search_fields = ["nome_completo", "cpf_hash", "email", "igreja__nome_fantasia"]
    list_select_related = ["igreja", "responsavel"]
    filter_horizontal = ["organizacoes"]
    exclude = ["cpf_hash"]
    readonly_fields = ["status"]


@admin.register(Consentimento)
class ConsentimentoAdmin(admin.ModelAdmin):
    list_display = ["membro", "termo", "responsavel", "ip", "criado_em"]
    list_filter = ["termo"]
    search_fields = ["membro__nome_completo"]
    readonly_fields = [field.name for field in Consentimento._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(RevogacaoConsentimento)
class RevogacaoConsentimentoAdmin(admin.ModelAdmin):
    list_display = ["membro", "ip", "criado_em"]
    readonly_fields = ["membro", "ip", "motivo", "criado_em"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
