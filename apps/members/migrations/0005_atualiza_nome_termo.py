from django.db import migrations

ANTIGO = "União Missionária de Homens Batistas do Tocantins"
NOVO = "Homens Batistas do Tocantins"


def atualizar_nome(apps, schema_editor):
    TermoVersao = apps.get_model("members", "TermoVersao")
    for termo in TermoVersao.objects.filter(texto__contains=ANTIGO):
        texto = termo.texto.replace(f"da {ANTIGO}", f"dos {NOVO}")
        termo.texto = texto.replace(ANTIGO, NOVO)
        termo.save(update_fields=["texto"])


def restaurar_nome(apps, schema_editor):
    TermoVersao = apps.get_model("members", "TermoVersao")
    for termo in TermoVersao.objects.filter(texto__contains=NOVO):
        texto = termo.texto.replace(f"dos {NOVO}", f"da {ANTIGO}")
        termo.texto = texto.replace(NOVO, ANTIGO)
        termo.save(update_fields=["texto"])


class Migration(migrations.Migration):
    dependencies = [
        ("members", "0004_termo_padrao"),
    ]

    operations = [
        migrations.RunPython(atualizar_nome, restaurar_nome),
    ]
