from django.db import migrations

FORWARD = """
CREATE OR REPLACE FUNCTION prevent_consentimento_mutation() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'Registros de consentimento são imutáveis.';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS consentimento_no_update_delete ON members_consentimento;

CREATE TRIGGER consentimento_no_update_delete
BEFORE UPDATE OR DELETE ON members_consentimento
FOR EACH ROW EXECUTE FUNCTION prevent_consentimento_mutation();
"""

REVERSE = """
DROP TRIGGER IF EXISTS consentimento_no_update_delete ON members_consentimento;
DROP FUNCTION IF EXISTS prevent_consentimento_mutation();
"""


def apply_trigger(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        with schema_editor.connection.cursor() as cursor:
            cursor.execute(FORWARD)


def remove_trigger(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        with schema_editor.connection.cursor() as cursor:
            cursor.execute(REVERSE)


class Migration(migrations.Migration):
    dependencies = [
        ("members", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(apply_trigger, remove_trigger),
    ]
