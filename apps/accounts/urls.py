from django.contrib.auth import views as auth_views
from django.urls import path

from apps.dashboard.views import painel

from .forms import LoginForm

urlpatterns = [
    path("login/", auth_views.LoginView.as_view(authentication_form=LoginForm), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("painel/", painel, name="dashboard"),
]
