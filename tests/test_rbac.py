import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.test import RequestFactory
from django.urls import reverse

from apps.accounts.permissions import role_required, user_has_role
from apps.accounts.roles import Role

User = get_user_model()


def make_user(email, role=None):
    user = User.objects.create_user(email=email, password="x", full_name=email)
    if role:
        user.groups.add(Group.objects.get(name=role.value))
    return user


@pytest.mark.django_db
def test_role_groups_created_by_migration():
    names = set(Group.objects.values_list("name", flat=True))
    assert {role.value for role in Role}.issubset(names)


@pytest.mark.django_db
def test_user_role_property():
    user = make_user("coord@example.com", Role.COORDENADOR_REGIONAL)
    assert user.role == Role.COORDENADOR_REGIONAL
    assert user.has_role(Role.COORDENADOR_REGIONAL)
    assert not user.has_role(Role.ADMIN_ESTADUAL)


@pytest.mark.django_db
def test_role_required_redirects_anonymous():
    @role_required(Role.ADMIN_ESTADUAL)
    def view(request):
        return HttpResponse("ok")

    request = RequestFactory().get("/restrito/")
    from django.contrib.auth.models import AnonymousUser

    request.user = AnonymousUser()
    response = view(request)
    assert response.status_code == 302
    assert "/contas/login/" in response["Location"]


@pytest.mark.django_db
def test_role_required_denies_wrong_role():
    @role_required(Role.ADMIN_ESTADUAL)
    def view(request):
        return HttpResponse("ok")

    user = make_user("membro@example.com", Role.MEMBRO)
    request = RequestFactory().get("/restrito/")
    request.user = user
    with pytest.raises(PermissionDenied):
        view(request)


@pytest.mark.django_db
def test_role_required_allows_correct_role():
    @role_required(Role.ADMIN_ESTADUAL)
    def view(request):
        return HttpResponse("ok")

    user = make_user("admin@example.com", Role.ADMIN_ESTADUAL)
    request = RequestFactory().get("/restrito/")
    request.user = user
    assert view(request).status_code == 200


@pytest.mark.django_db
def test_dashboard_requires_login(client):
    response = client.get(reverse("dashboard"))
    assert response.status_code == 302


@pytest.mark.django_db
def test_dashboard_shows_role(client):
    user = make_user("dir@example.com", Role.DIRETOR_LOCAL)
    client.force_login(user)
    response = client.get(reverse("dashboard"))
    assert response.status_code == 200
    assert b"Diretor" in response.content


@pytest.mark.django_db
def test_user_has_role_false_for_anonymous():
    from django.contrib.auth.models import AnonymousUser

    assert not user_has_role(AnonymousUser(), Role.MEMBRO)
