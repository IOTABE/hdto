from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.core.crypto import hash_cpf
from apps.core.forms import MaterialFormMixin
from apps.core.validators import validate_cpf

from .models import Membro, ResponsavelLegal, TermoVersao
from .scoping import organizacoes_para_cadastro


def calcular_idade(nascimento, referencia=None):
    referencia = referencia or timezone.localdate()
    return (
        referencia.year
        - nascimento.year
        - ((referencia.month, referencia.day) < (nascimento.month, nascimento.day))
    )


class MembroForm(MaterialFormMixin, forms.ModelForm):
    responsavel = forms.ModelChoiceField(
        queryset=ResponsavelLegal.objects.all(),
        required=False,
        widget=forms.HiddenInput(),
    )
    responsavel_nome = forms.CharField(label="Nome do responsável", required=False)
    responsavel_cpf = forms.CharField(label="CPF do responsável", required=False)
    responsavel_parentesco = forms.CharField(label="Parentesco", required=False)
    responsavel_telefone = forms.CharField(label="Telefone do responsável", required=False)
    consentimento = forms.BooleanField(
        label="Li e concordo com o termo de consentimento para tratamento dos dados.",
        required=True,
    )

    class Meta:
        model = Membro
        fields = [
            "nome_completo",
            "cpf",
            "data_nascimento",
            "estado_civil",
            "profissao",
            "talentos",
            "email",
            "telefone",
            "endereco",
            "organizacoes",
        ]
        widgets = {
            "cpf": forms.TextInput(attrs={"inputmode": "numeric", "autocomplete": "off"}),
            "data_nascimento": forms.DateInput(attrs={"type": "date"}),
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
            "telefone": forms.TextInput(attrs={"autocomplete": "tel"}),
            "endereco": forms.TextInput(attrs={"autocomplete": "street-address"}),
            "talentos": forms.Textarea(
                attrs={"rows": 3, "placeholder": "Ex.: elétrica, pedreiro, música, saúde…"}
            ),
        }

    def __init__(self, *args, user=None, ip=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.ip = ip
        self.fields["organizacoes"].queryset = organizacoes_para_cadastro(user)
        self.fields["organizacoes"].help_text = "Selecione ao menos uma organização ativa."

    def clean(self):
        dados = super().clean()
        nascimento = dados.get("data_nascimento")
        menor = bool(nascimento and calcular_idade(nascimento) < 18)

        cpf = dados.get("cpf")
        if cpf:
            try:
                validate_cpf(cpf)
            except ValidationError as exc:
                self.add_error("cpf", exc)
            else:
                duplicado = Membro.objects.filter(cpf_hash=hash_cpf(cpf))
                if self.instance.pk:
                    duplicado = duplicado.exclude(pk=self.instance.pk)
                if duplicado.exists():
                    self.add_error("cpf", "CPF já cadastrado para outro membro.")

        if menor:
            for campo, rotulo in [
                ("responsavel_nome", "nome"),
                ("responsavel_cpf", "CPF"),
                ("responsavel_parentesco", "parentesco"),
            ]:
                if not dados.get(campo):
                    self.add_error(campo, f"Informe o {rotulo} do responsável legal.")
            responsavel_cpf = dados.get("responsavel_cpf")
            if responsavel_cpf:
                try:
                    validate_cpf(responsavel_cpf)
                except ValidationError as exc:
                    self.add_error("responsavel_cpf", exc)

        if not dados.get("organizacoes"):
            self.add_error("organizacoes", "Selecione ao menos uma organização ativa.")

        if TermoVersao.vigente_atual() is None:
            self.add_error(
                None,
                "Não há termo de consentimento vigente. Procure a liderança da organização.",
            )

        dados["responsavel"] = None
        if menor and not self._errors and dados.get("responsavel_cpf"):
            responsavel, _ = ResponsavelLegal.objects.get_or_create(
                cpf_hash=hash_cpf(dados["responsavel_cpf"]),
                defaults={
                    "nome": dados["responsavel_nome"],
                    "cpf": dados["responsavel_cpf"],
                    "parentesco": dados["responsavel_parentesco"],
                    "telefone": dados.get("responsavel_telefone", ""),
                },
            )
            self.instance.responsavel = responsavel
            dados["responsavel"] = responsavel

        return dados

    def save(self, commit=True):
        membro = super().save(commit=False)
        if self.user and self.user.is_authenticated and not membro.user_id:
            membro.user = self.user
        if commit:
            membro.save()
            self.save_m2m()
            if self.cleaned_data.get("consentimento"):
                membro.registrar_consentimento(
                    responsavel=membro.responsavel,
                    ip=self.ip,
                    finalidade="Autocadastro censitário",
                )
        return membro
