import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
def test_create_user_normalizes_email():
    user = User.objects.create_user(email="Fulano@Example.COM", password="x", full_name="Fulano")
    assert user.email == "fulano@example.com"
    assert user.check_password("x")
    assert user.is_active
    assert not user.is_staff


def test_create_user_requires_email(db):
    with pytest.raises(ValueError):
        User.objects.create_user(email="", password="x", full_name="Sem Email")


@pytest.mark.django_db
def test_create_superuser_flags():
    user = User.objects.create_superuser(email="admin@example.com", password="x", full_name="Admin")
    assert user.is_staff and user.is_superuser


@pytest.mark.django_db
def test_password_uses_argon2(user):
    assert user.password.startswith("argon2$")
