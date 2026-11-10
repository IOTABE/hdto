from django.contrib.auth.forms import AuthenticationForm

from apps.core.forms import MaterialFormMixin


class LoginForm(MaterialFormMixin, AuthenticationForm):
    pass
