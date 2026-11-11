from django.db import migrations


def preencher_igreja(apps, schema_editor):
    Membro = apps.get_model("members", "Membro")
    for membro in Membro.objects.filter(igreja__isnull=True):
        organizacao = membro.organizacoes.order_by("pk").first()
        if organizacao is not None:
            membro.igreja_id = organizacao.igreja_id
            membro.save(update_fields=["igreja"])


class Migration(migrations.Migration):
    dependencies = [
        ("members", "0006_membro_igreja"),
    ]

    operations = [
        migrations.RunPython(preencher_igreja, migrations.RunPython.noop),
    ]
