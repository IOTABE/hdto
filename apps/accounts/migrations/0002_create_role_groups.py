from django.db import migrations

from apps.accounts.roles import Role


def create_groups(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    for role in Role:
        Group.objects.get_or_create(name=role.value)


def remove_groups(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name__in=[role.value for role in Role]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.RunPython(create_groups, remove_groups),
    ]
