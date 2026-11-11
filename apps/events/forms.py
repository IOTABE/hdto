from captcha.fields import CaptchaField
from django import forms
from django.core.exceptions import ValidationError

from apps.core.forms import MaterialFormMixin
from apps.members.models import Membro
from apps.members.scoping import membros_visiveis

from .models import Inscricao


class InscricaoForm(MaterialFormMixin, forms.Form):
    membro = forms.ModelChoiceField(queryset=Membro.objects.none(), label="Quem vai se inscrever")
    captcha = CaptchaField(label="Verificação antirobô")

    def __init__(self, *args, user, evento, **kwargs):
        super().__init__(*args, **kwargs)
        self.evento = evento
        queryset = membros_visiveis(user).filter(status=Membro.Status.ATIVO).order_by(
            "nome_completo"
        )
        self.fields["membro"].queryset = queryset
        membro = getattr(user, "membro", None)
        if membro is not None and queryset.filter(pk=membro.pk).exists():
            self.fields["membro"].initial = membro.pk

    def clean_membro(self):
        membro = self.cleaned_data["membro"]
        if Inscricao.objects.filter(evento=self.evento, membro=membro).exists():
            raise ValidationError("Este membro já está inscrito neste evento.")
        return membro
