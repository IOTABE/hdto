import pytest
from cryptography.fernet import Fernet


@pytest.fixture(autouse=True)
def crypto_settings(settings):
    settings.FIELD_ENCRYPTION_KEY = Fernet.generate_key().decode()
    settings.CPF_HASH_PEPPER = "test-pepper"


@pytest.fixture
def user(db):
    from apps.accounts.models import User

    return User.objects.create_user(
        email="membro@example.com",
        password="SenhaForte123!",
        full_name="Membro de Teste",
    )
