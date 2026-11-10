from django.db import models

from apps.core.crypto import decrypt_text, encrypt_text


class EncryptedTextField(models.TextField):
    description = "Campo de texto cifrado em repouso"

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        return encrypt_text(value)

    def from_db_value(self, value, expression, connection):
        return decrypt_text(value)

    def to_python(self, value):
        if value is None:
            return value
        return decrypt_text(value)
