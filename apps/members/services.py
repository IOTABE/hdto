import uuid

from django.db import transaction

from .models import Membro, RevogacaoConsentimento


def anonimizar_membro(membro):
    membro.nome_completo = "Titular anonimizado"
    membro.cpf = f"{uuid.uuid4().int:011d}"[-11:]
    membro.email = ""
    membro.telefone = ""
    membro.endereco = ""
    membro.profissao = ""
    membro.talentos = ""
    membro.responsavel = None
    membro.status = Membro.Status.INATIVO
    membro.save()

    censo = getattr(membro, "censo", None)
    if censo is not None:
        censo.escolaridade = ""
        censo.area_atuacao = ""
        censo.competencias = ""
        censo.ministerio_socorro = ""
        censo.disponivel_voluntariado = False
        censo.save()

    if membro.user_id:
        membro.user.is_active = False
        membro.user.save(update_fields=["is_active"])


@transaction.atomic
def revogar_consentimento(membro, ip=None, motivo=""):
    revogacao = RevogacaoConsentimento.objects.create(membro=membro, ip=ip, motivo=motivo)
    anonimizar_membro(membro)
    return revogacao
