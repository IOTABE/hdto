from django.db import models


class Role(models.TextChoices):
    ADMIN_ESTADUAL = "admin_estadual", "Administrador Estadual"
    COORDENADOR_REGIONAL = "coord_regional", "Coordenador Regional"
    DIRETOR_LOCAL = "diretor_local", "Diretor/Conselheiro Local"
    MEMBRO = "membro", "Membro"


ROLE_NAMES = [role.value for role in Role]

ROLE_LABELS = {role.value: role.label for role in Role}
