from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.core.crypto import hash_cpf
from apps.core.fields import EncryptedTextField
from apps.core.models import TimeStampedModel
from apps.core.validators import normalize_cpf, validate_cpf


class TermoVersao(TimeStampedModel):
    versao = models.CharField("versão", max_length=20, unique=True)
    texto = models.TextField("texto do termo")
    vigente = models.BooleanField("vigente", default=True)

    class Meta:
        verbose_name = "versão do termo"
        verbose_name_plural = "versões do termo"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Termo {self.versao}"

    @classmethod
    def vigente_atual(cls):
        return cls.objects.filter(vigente=True).order_by("-created_at").first()


class ResponsavelLegal(TimeStampedModel):
    nome = models.CharField("nome", max_length=150)
    parentesco = models.CharField("parentesco", max_length=60)
    cpf = EncryptedTextField("CPF", blank=True)
    cpf_hash = models.CharField(max_length=64, blank=True, editable=False)
    email = models.EmailField("e-mail", blank=True)
    telefone = models.CharField("telefone", max_length=20, blank=True)

    class Meta:
        verbose_name = "responsável legal"
        verbose_name_plural = "responsáveis legais"
        ordering = ["nome"]

    def __str__(self):
        return self.nome

    def clean(self):
        super().clean()
        validate_cpf(self.cpf)

    def save(self, *args, **kwargs):
        self.cpf = normalize_cpf(self.cpf)
        self.cpf_hash = hash_cpf(self.cpf)
        super().save(*args, **kwargs)


class Membro(TimeStampedModel):
    class Status(models.TextChoices):
        PROVISORIO = "provisorio", "Provisório"
        ATIVO = "ativo", "Ativo"
        INATIVO = "inativo", "Inativo"

    class EstadoCivil(models.TextChoices):
        SOLTEIRO = "solteiro", "Solteiro(a)"
        CASADO = "casado", "Casado(a)"
        DIVORCIADO = "divorciado", "Divorciado(a)"
        VIUVO = "viuvo", "Viúvo(a)"
        OUTRO = "outro", "Outro"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="membro",
        verbose_name="usuário",
    )
    nome_completo = models.CharField("nome completo", max_length=150)
    cpf = EncryptedTextField("CPF", blank=True)
    cpf_hash = models.CharField(max_length=64, unique=True, blank=True, editable=False)
    data_nascimento = models.DateField("data de nascimento")
    estado_civil = models.CharField(
        "estado civil", max_length=20, choices=EstadoCivil.choices, blank=True
    )
    profissao = models.CharField("profissão", max_length=120, blank=True)
    talentos = models.TextField("talentos vocacionais", blank=True)
    email = models.EmailField("e-mail", blank=True)
    telefone = models.CharField("telefone", max_length=20, blank=True)
    endereco = models.CharField("endereço residencial", max_length=255, blank=True)
    organizacoes = models.ManyToManyField(
        "institutions.Organizacao",
        related_name="membros",
        blank=True,
        verbose_name="organizações",
    )
    responsavel = models.ForeignKey(
        ResponsavelLegal,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="dependentes",
        verbose_name="responsável legal",
    )
    status = models.CharField(
        "status", max_length=20, choices=Status.choices, default=Status.PROVISORIO
    )

    class Meta:
        verbose_name = "membro"
        verbose_name_plural = "membros"
        ordering = ["nome_completo"]

    def __str__(self):
        return self.nome_completo

    @property
    def idade(self):
        today = timezone.localdate()
        born = self.data_nascimento
        return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

    @property
    def menor_de_idade(self):
        return self.idade < 18

    def clean(self):
        super().clean()
        validate_cpf(self.cpf)
        if self.menor_de_idade and not self.responsavel_id:
            raise ValidationError(
                {"responsavel": "Membros menores de 18 anos exigem responsável legal."}
            )
        if self.cpf:
            duplicado = Membro.objects.filter(cpf_hash=hash_cpf(self.cpf))
            if self.pk:
                duplicado = duplicado.exclude(pk=self.pk)
            if duplicado.exists():
                raise ValidationError({"cpf": "CPF já cadastrado para outro membro."})

    def save(self, *args, **kwargs):
        self.cpf = normalize_cpf(self.cpf)
        self.cpf_hash = hash_cpf(self.cpf)
        super().save(*args, **kwargs)

    def consentimento_vigente(self):
        return self.consentimentos.select_related("termo").order_by("-criado_em").first()

    def pode_ativar(self):
        consentimento = self.consentimento_vigente()
        if consentimento is None:
            return False
        if self.menor_de_idade:
            if not self.responsavel_id:
                return False
            if consentimento.responsavel_id != self.responsavel_id:
                return False
        if self.pk and not self.organizacoes.filter(status="ativa").exists():
            return False
        return True

    def ativar(self):
        if not self.pode_ativar():
            raise ValidationError(
                "Membro não pode ser ativado: consentimento, responsável ou organização ausente."
            )
        self.status = self.Status.ATIVO
        self.save(update_fields=["status", "updated_at"])
        return self

    def registrar_consentimento(self, responsavel=None, ip=None, termo=None, finalidade=""):
        if self.menor_de_idade and not (responsavel or self.responsavel):
            raise ValidationError("Menor exige consentimento do responsável legal.")
        termo = termo or TermoVersao.vigente_atual()
        if termo is None:
            raise ValidationError("Não há termo de consentimento vigente.")
        consentimento = Consentimento.objects.create(
            membro=self,
            responsavel=responsavel or (self.responsavel if self.menor_de_idade else None),
            termo=termo,
            ip=ip,
            finalidade=finalidade,
        )
        self.ativar()
        return consentimento


class RevogacaoConsentimento(models.Model):
    membro = models.ForeignKey(
        Membro, on_delete=models.PROTECT, related_name="revogacoes", verbose_name="membro"
    )
    ip = models.GenericIPAddressField("IP de origem", null=True, blank=True)
    motivo = models.TextField("motivo", blank=True)
    criado_em = models.DateTimeField("revogado em", auto_now_add=True)

    class Meta:
        verbose_name = "revogação de consentimento"
        verbose_name_plural = "revogações de consentimento"
        ordering = ["-criado_em"]

    def __str__(self):
        return f"Revogação de {self.membro} em {self.criado_em:%d/%m/%Y}"

    def save(self, *args, **kwargs):
        if self.pk and not self._state.adding:
            raise ValidationError("Registros de revogação são imutáveis.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Registros de revogação não podem ser excluídos.")


class Consentimento(models.Model):
    membro = models.ForeignKey(
        Membro, on_delete=models.PROTECT, related_name="consentimentos", verbose_name="membro"
    )
    responsavel = models.ForeignKey(
        ResponsavelLegal,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="consentimentos",
        verbose_name="responsável legal",
    )
    termo = models.ForeignKey(
        TermoVersao, on_delete=models.PROTECT, related_name="consentimentos", verbose_name="termo"
    )
    ip = models.GenericIPAddressField("IP de origem", null=True, blank=True)
    finalidade = models.CharField("finalidade", max_length=255, blank=True)
    criado_em = models.DateTimeField("registrado em", auto_now_add=True)

    class Meta:
        verbose_name = "consentimento"
        verbose_name_plural = "consentimentos"
        ordering = ["-criado_em"]

    def __str__(self):
        return f"Consentimento de {self.membro} — {self.termo.versao}"

    def save(self, *args, **kwargs):
        if self.pk and not self._state.adding:
            raise ValidationError("Registros de consentimento são imutáveis.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Registros de consentimento não podem ser excluídos.")
