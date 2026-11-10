import pytest


@pytest.fixture
def user(db):
    from apps.accounts.models import User

    return User.objects.create_user(
        email="membro@example.com",
        password="SenhaForte123!",
        full_name="Membro de Teste",
    )
