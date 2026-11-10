from django import forms

from apps.accounts.roles import Role
from apps.core.forms import MaterialFormMixin
from apps.institutions.models import Igreja, Organizacao


def _is_admin(user):
    return user.is_superuser or user.has_role(Role.ADMIN_ESTADUAL)


def _associacao_do_usuario(user):
    if user.associacao_id:
        return user.associacao_id
    if user.igreja_id:
        return user.igreja.associacao_id
    return None


class IgrejaForm(MaterialFormMixin, forms.ModelForm):
    latitude = forms.DecimalField(
        label="Latitude", max_digits=9, decimal_places=6, required=False
    )
    longitude = forms.DecimalField(
        label="Longitude", max_digits=9, decimal_places=6, required=False
    )

    class Meta:
        model = Igreja
        fields = [
            "associacao",
            "municipio",
            "igreja_mae",
            "cnpj",
            "razao_social",
            "nome_fantasia",
            "pastor_titular",
            "telefone",
            "email",
            "logradouro",
            "bairro",
            "cep",
        ]
        widgets = {
            "cnpj": forms.TextInput(attrs={"inputmode": "numeric", "autocomplete": "off"}),
            "cep": forms.TextInput(attrs={"inputmode": "numeric", "autocomplete": "postal-code"}),
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
            "telefone": forms.TextInput(attrs={"autocomplete": "tel"}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields["igreja_mae"].queryset = Igreja.objects.filter(
            status=Igreja.Status.HOMOLOGADA
        )
        self.fields["igreja_mae"].help_text = "Obrigatória apenas para congregações sem CNPJ."
        if user and user.is_authenticated and not _is_admin(user):
            associacao_id = _associacao_do_usuario(user)
            if associacao_id:
                self.fields["associacao"].queryset = self.fields[
                    "associacao"
                ].queryset.filter(pk=associacao_id)

    def clean(self):
        dados = super().clean()
        latitude = dados.get("latitude")
        longitude = dados.get("longitude")
        if (latitude is None) != (longitude is None):
            raise forms.ValidationError("Informe latitude e longitude juntas.")
        if latitude is not None and not (-90 <= latitude <= 90):
            self.add_error("latitude", "Latitude deve estar entre -90 e 90.")
        if longitude is not None and not (-180 <= longitude <= 180):
            self.add_error("longitude", "Longitude deve estar entre -180 e 180.")
        igreja_mae = dados.get("igreja_mae")
        associacao = dados.get("associacao")
        if igreja_mae and associacao and igreja_mae.associacao_id != associacao.pk:
            self.add_error("igreja_mae", "A igreja-mãe deve pertencer à mesma associação.")
        return dados

    def save(self, commit=True):
        igreja = super().save(commit=False)
        latitude = self.cleaned_data.get("latitude")
        longitude = self.cleaned_data.get("longitude")
        if latitude is not None and longitude is not None:
            from django.contrib.gis.geos import Point

            igreja.location = Point(float(longitude), float(latitude), srid=4326)
        if commit:
            igreja.save()
            self.save_m2m()
        return igreja


class OrganizacaoForm(MaterialFormMixin, forms.ModelForm):
    class Meta:
        model = Organizacao
        fields = [
            "igreja",
            "tipo",
            "data_fundacao",
            "lider_nome",
            "lider_contato",
            "dia_reuniao",
            "horario_reuniao",
        ]
        widgets = {
            "data_fundacao": forms.DateInput(attrs={"type": "date"}),
            "horario_reuniao": forms.TimeInput(attrs={"type": "time"}),
            "lider_contato": forms.TextInput(attrs={"autocomplete": "tel"}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        igrejas = Igreja.objects.filter(status=Igreja.Status.HOMOLOGADA)
        if user and user.is_authenticated and not _is_admin(user):
            associacao_id = _associacao_do_usuario(user)
            if user.has_role(Role.DIRETOR_LOCAL) and user.igreja_id:
                igrejas = igrejas.filter(pk=user.igreja_id)
            elif associacao_id:
                igrejas = igrejas.filter(associacao_id=associacao_id)
        self.fields["igreja"].queryset = igrejas
        self.fields["igreja"].help_text = "Somente igrejas homologadas aparecem aqui."

    def clean(self):
        dados = super().clean()
        igreja = dados.get("igreja")
        tipo = dados.get("tipo")
        if igreja and tipo and Organizacao.objects.filter(igreja=igreja, tipo=tipo).exists():
            raise forms.ValidationError("Esta organização já está ativa nesta igreja.")
        return dados
