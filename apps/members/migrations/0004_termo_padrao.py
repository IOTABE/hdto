from django.db import migrations


def criar_termo_padrao(apps, schema_editor):
    TermoVersao = apps.get_model("members", "TermoVersao")
    TermoVersao.objects.get_or_create(
        versao="1.0",
        defaults={
            "texto": (
                "Autorizo o tratamento dos meus dados pessoais, incluindo a filiação a "
                "organização religiosa, para fins de cadastro, censo e comunicação dos "
                "Homens Batistas do Tocantins, nos termos da LGPD."
            ),
            "vigente": True,
        },
    )


def remover_termo_padrao(apps, schema_editor):
    TermoVersao = apps.get_model("members", "TermoVersao")
    TermoVersao.objects.filter(versao="1.0").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("members", "0003_revogacaoconsentimento"),
    ]

    operations = [
        migrations.RunPython(criar_termo_padrao, remover_termo_padrao),
    ]
