import hashlib
import hmac

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def _fernet():
    key = settings.FIELD_ENCRYPTION_KEY
    if not key:
        raise ImproperlyConfigured("FIELD_ENCRYPTION_KEY não configurada.")
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt_text(value):
    if value in (None, ""):
        return value
    return _fernet().encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_text(value):
    if value in (None, ""):
        return value
    try:
        return _fernet().decrypt(value.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        return value


def hash_cpf(value):
    normalized = "".join(filter(str.isdigit, value or ""))
    pepper = settings.CPF_HASH_PEPPER.encode("utf-8")
    return hmac.new(pepper, normalized.encode("utf-8"), hashlib.sha256).hexdigest()
