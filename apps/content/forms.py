from captcha.fields import CaptchaField
from django import forms

from apps.core.forms import MaterialFormMixin

from .models import Contato


class ContatoForm(MaterialFormMixin, forms.ModelForm):
    captcha = CaptchaField(label="Verificação antirobô")

    class Meta:
        model = Contato
        fields = ["nome", "email", "telefone", "assunto", "mensagem", "canal"]
        widgets = {
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
            "telefone": forms.TextInput(
                attrs={"autocomplete": "tel", "placeholder": "(63) 9 9999-9999"}
            ),
            "mensagem": forms.Textarea(attrs={"rows": 5}),
        }

    def clean(self):
        dados = super().clean()
        canal = dados.get("canal")
        if canal == Contato.Canal.EMAIL and not dados.get("email"):
            self.add_error("email", "Informe um e-mail para receber a resposta.")
        if canal == Contato.Canal.WHATSAPP and not dados.get("telefone"):
            self.add_error("telefone", "Informe um telefone/WhatsApp para contato.")
        return dados
