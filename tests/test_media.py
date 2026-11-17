import pytest


@pytest.mark.django_db
def test_media_servida_fora_do_debug(client, settings, tmp_path):
    settings.DEBUG = False
    settings.MEDIA_ROOT = tmp_path
    (tmp_path / "teste.txt").write_text("ok", encoding="utf-8")

    resposta = client.get("/media/teste.txt")

    assert resposta.status_code == 200
