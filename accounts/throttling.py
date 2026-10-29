"""Verrouillage temporaire après trop d'échecs de connexion pour un même identifiant.

Le compteur porte sur l'identifiant saisi, qu'il existe ou non : le message de blocage ne révèle donc pas
quels comptes existent. L'adresse IP n'est pas utilisée : derrière le proxy de PythonAnywhere, elle serait
commune à tous les visiteurs.
"""
from django.conf import settings
from django.contrib.admin.forms import AdminAuthenticationForm
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .models import LoginFailure


def _key(username):
    return (username or "").strip().lower()[:150]


def is_locked(username, now=None):
    since = (now or timezone.now()) - settings.LOGIN_LOCKOUT
    return LoginFailure.objects.filter(username=_key(username), created_at__gte=since).count() >= settings.LOGIN_MAX_FAILURES


def record_failure(username, now=None):
    LoginFailure.objects.filter(created_at__lt=(now or timezone.now()) - settings.LOGIN_LOCKOUT).delete()
    LoginFailure.objects.create(username=_key(username))


def clear_failures(username):
    LoginFailure.objects.filter(username=_key(username)).delete()


class LoginThrottleMixin:
    """À placer avant un formulaire d'authentification de Django."""

    locked_message = _("Trop de tentatives de connexion. Réessayez dans quelques minutes.")
    locked_out = False

    def clean(self):
        username = self.cleaned_data.get("username")
        if is_locked(username):
            self.locked_out = True
            raise ValidationError(self.locked_message, code="locked")
        try:
            cleaned = super().clean()
        except ValidationError:
            record_failure(username)
            raise
        clear_failures(username)
        return cleaned


class ThrottledAuthenticationForm(LoginThrottleMixin, AuthenticationForm):
    pass


class ThrottledAdminAuthenticationForm(LoginThrottleMixin, AdminAuthenticationForm):
    pass
