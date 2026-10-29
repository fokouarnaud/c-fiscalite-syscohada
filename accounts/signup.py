"""Inscription publique (US-02 à US-04) : e-mail vérifié, piège à robots, limite par IP, purge des comptes non vérifiés."""
import hashlib
import hmac
import time
from datetime import timedelta

from django import forms
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Q
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import gettext_lazy as _

from .models import SignupThrottle, User

UNVERIFIED_LIFETIME = timedelta(days=7)
MAINTENANCE_INTERVAL = 3600  # secondes entre deux purges, par processus


class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
    """Jeton à usage unique : il change dès que le compte est vérifié ou réactivé."""

    key_salt = "accounts.signup.EmailVerificationTokenGenerator"

    def _make_hash_value(self, user, timestamp):
        return f"{user.pk}{timestamp}{user.is_active}{user.email_verified}{user.email}"


email_verification_token = EmailVerificationTokenGenerator()


class SignupForm(UserCreationForm):
    # Champ piège : invisible pour un humain (masqué en CSS), rempli par les robots.
    website = forms.CharField(required=False, label=_("Site web"))

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ("email", "first_name", "last_name"):
            self.fields[name].required = True

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if username and not confirmed_or_active().filter(username__iexact=username).exists():
            return username  # libre, ou tenu par un compte jamais confirmé que l'inscription remplacera
        return super().clean_username()

    def clean_email(self):
        email = self.cleaned_data["email"].strip()
        if confirmed_or_active().filter(email__iexact=email).exists():
            raise forms.ValidationError(_("Un compte utilise déjà cette adresse e-mail."))
        return email

    def validate_unique(self):
        # L'unicité de l'identifiant est jugée par clean_username, qui ignore les comptes jamais confirmés.
        exclude = self._get_validation_exclusions() | {"username"}
        try:
            self.instance.validate_unique(exclude=exclude)
        except forms.ValidationError as e:
            self._update_errors(e)

    @property
    def is_bot(self):
        return bool(self.data.get("website"))


def client_ip_hash(request):
    """Empreinte HMAC de l'adresse IP : jamais stockée en clair (AGENTS.md, confidentialité)."""
    ip = request.META.get(settings.SIGNUP_CLIENT_IP_HEADER) or request.META.get("REMOTE_ADDR", "")
    ip = ip.split(",")[0].strip()
    return hmac.new(force_bytes(settings.SECRET_KEY), force_bytes(ip), hashlib.sha256).hexdigest()


def is_signup_throttled(ip_hash, now=None):
    since = (now or timezone.now()) - timedelta(hours=1)
    SignupThrottle.objects.filter(created_at__lt=since).delete()
    return SignupThrottle.objects.filter(ip_hash=ip_hash).count() >= settings.SIGNUP_MAX_PER_HOUR


def never_confirmed():
    """Comptes créés par l'inscription publique dont le lien n'a jamais servi (US-01)."""
    return User.objects.filter(is_active=False, email_verified=False)


def confirmed_or_active():
    return User.objects.exclude(pk__in=never_confirmed())


@transaction.atomic
def create_pending_learner(form):
    """Crée le compte en attente ; un compte jamais confirmé qui portait cet identifiant ou cette adresse est remplacé,
    pour qu'un lien perdu (ou jamais parti) ne bloque pas l'apprenant."""
    username, email = form.cleaned_data["username"], form.cleaned_data["email"]
    never_confirmed().filter(Q(username__iexact=username) | Q(email__iexact=email)).delete()
    user = form.save(commit=False)
    user.is_active = False
    user.role = User.Role.LEARNER
    user.save()
    return user


def send_verification_email(request, user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    link = request.build_absolute_uri(reverse("verify_email", args=[uid, email_verification_token.make_token(user)]))
    context = {"user": user, "link": link}
    send_mail(
        subject=str(_("Confirmez votre inscription à ComptaFisca Acad Ventisax")),
        message=render_to_string("accounts/email/verify_email.txt", context),
        from_email=None,
        recipient_list=[user.email],
    )


def purge_unverified_accounts(now=None):
    """Supprime les comptes publics jamais vérifiés après 7 jours (US-04) ; renvoie leur nombre."""
    limit = (now or timezone.now()) - UNVERIFIED_LIFETIME
    stale = User.objects.filter(is_active=False, email_verified=False, date_joined__lt=limit)
    _, per_model = stale.delete()
    return per_model.get(User._meta.label, 0)


_last_maintenance = 0.0


def run_maintenance_if_due():
    """Purge au plus une fois par heure et par processus (le plan gratuit n'a pas de tâche planifiée)."""
    global _last_maintenance
    if time.monotonic() - _last_maintenance < MAINTENANCE_INTERVAL and _last_maintenance:
        return False
    _last_maintenance = time.monotonic()
    purge_unverified_accounts()
    return True


def reset_maintenance():
    global _last_maintenance
    _last_maintenance = 0.0
