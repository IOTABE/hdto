from captcha.fields import CaptchaField
from django import forms
from django.utils.text import slugify

from apps.core.forms import MaterialFormMixin

from .models import (
    Contato,
    Foto,
    Galeria,
    Historia,
    MembroDiretoria,
    Noticia,
)


class SlugUnicoMixin:
    def clean_slug(self):
        slug = self.cleaned_data.get("slug")
        base = slugify(
            self.cleaned_data.get("titulo") or self.cleaned_data.get("nome") or ""
        )
        if not slug:
            if not base:
                raise forms.ValidationError("Informe um título para gerar o slug.")
            Model = self._meta.model
            limite = Model._meta.get_field("slug").max_length or 50
            base = base[:limite]
            slug = base
            candidato = slug
            contador = 2
            while (
                Model.objects.filter(slug=candidato)
                .exclude(pk=self.instance.pk)
                .exists()
            ):
                sufixo = f"-{contador}"
                candidato = f"{base[: limite - len(sufixo)]}{sufixo}"
                contador += 1
            slug = candidato
        return slug


class NoticiaForm(SlugUnicoMixin, MaterialFormMixin, forms.ModelForm):
    slug = forms.SlugField(
        label="slug",
        required=False,
        help_text="Deixe em branco para gerar automaticamente a partir do título.",
    )

    class Meta:
        model = Noticia
        fields = [
            "titulo",
            "slug",
            "resumo",
            "conteudo",
            "imagem",
            "autor",
            "publicada",
            "publicada_em",
        ]
        widgets = {
            "publicada_em": forms.DateTimeInput(
                format="%Y-%m-%dT%H:%M", attrs={"type": "datetime-local"}
            ),
            "conteudo": forms.Textarea(attrs={"rows": 8}),
        }


class GaleriaForm(SlugUnicoMixin, MaterialFormMixin, forms.ModelForm):
    slug = forms.SlugField(
        label="slug",
        required=False,
        help_text="Deixe em branco para gerar automaticamente a partir do título.",
    )

    class Meta:
        model = Galeria
        fields = ["titulo", "slug", "descricao", "publicada"]


class FotoForm(MaterialFormMixin, forms.ModelForm):
    class Meta:
        model = Foto
        fields = ["galeria", "imagem", "legenda", "ordem"]


class HistoriaForm(MaterialFormMixin, forms.ModelForm):
    class Meta:
        model = Historia
        fields = ["titulo", "resumo", "conteudo", "imagem", "publicada", "ordem"]
        widgets = {
            "conteudo": forms.Textarea(attrs={"rows": 10}),
            "resumo": forms.Textarea(attrs={"rows": 3}),
        }


class MembroDiretoriaForm(MaterialFormMixin, forms.ModelForm):
    class Meta:
        model = MembroDiretoria
        fields = [
            "nome",
            "cargo",
            "bienio_inicio",
            "bienio_fim",
            "foto",
            "bio",
            "email",
            "telefone",
            "publicada",
            "ordem",
        ]
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 4}),
            "telefone": forms.TextInput(attrs={"autocomplete": "tel"}),
        }


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
