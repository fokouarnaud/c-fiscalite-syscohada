"""Réglages Django d'Acad Ventisax. Les secrets viennent de l'environnement (.env sur le serveur)."""
import os
from datetime import timedelta
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

from django.utils.translation import gettext_lazy as _

from .env import load_env_file

BASE_DIR = Path(__file__).resolve().parent.parent
load_env_file(BASE_DIR / ".env")  # secrets du serveur (fichier ignoré par git)

DEV_SECRET_KEY = "dev-insecure-key-ne-pas-utiliser-en-production"
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY") or DEV_SECRET_KEY
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"
if not DEBUG and (SECRET_KEY == DEV_SECRET_KEY or len(SECRET_KEY) < 50 or len(set(SECRET_KEY)) < 5):
    # Une clé connue ou faible permettrait de forger des cookies de session : refus de démarrer.
    raise ImproperlyConfigured("DJANGO_SECRET_KEY doit être définie (au moins 50 caractères variés) en production.")
ALLOWED_HOSTS = [h for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h]

INSTALLED_APPS = [
    "modeltranslation",  # doit précéder django.contrib.admin
    "unfold",  # back-office Django Unfold (AGENTS.md, E8) : doit précéder django.contrib.admin
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts",
    "courses",
    "assessments",
    "progress",
    "catalog",
    "certificates",
    "referentiel",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "config.middleware.ContentSecurityPolicyMiddleware",
    "progress.middleware.DailyBackupMiddleware",
]

# Sauvegarde quotidienne de la base (vide = désactivée, comme en développement).
BACKUP_DIR = os.environ.get("DJANGO_BACKUP_DIR", "")

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_USER_MODEL = "accounts.User"
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "dashboard"
LOGOUT_REDIRECT_URL = "login"

# Sessions : cookies inaccessibles au JavaScript, durée d'une journée de formation (téléphones partagés).
SESSION_COOKIE_AGE = 8 * 3600
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_HTTPONLY = True  # le jeton CSRF est injecté par le gabarit (hx-headers), jamais lu dans le cookie
# Force brute : verrouillage d'un identifiant après LOGIN_MAX_FAILURES échecs en LOGIN_LOCKOUT (accounts/throttling.py).
LOGIN_MAX_FAILURES = 5
LOGIN_LOCKOUT = timedelta(minutes=15)
# Inscription publique (accounts/signup.py) : N inscriptions par heure et par IP. Derrière le proxy de PythonAnywhere,
# l'IP réelle est dans X-Real-IP (DJANGO_SIGNUP_IP_HEADER=HTTP_X_REAL_IP en production).
SIGNUP_MAX_PER_HOUR = 5
SIGNUP_CLIENT_IP_HEADER = os.environ.get("DJANGO_SIGNUP_IP_HEADER", "REMOTE_ADDR")
PASSWORD_RESET_TIMEOUT = 3600 * 24  # lien de mot de passe oublié valable 24 h

# E-mail sortant : Gmail SMTP (seul autorisé sur le plan gratuit), mot de passe d'application dans .env.
EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "1") == "1"
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
# Repli console seulement en développement : en production, un e-mail non envoyé doit échouer (US-01, accounts.E001).
EMAIL_BACKEND = (
    "django.core.mail.backends.console.EmailBackend" if DEBUG and not EMAIL_HOST_PASSWORD
    else "django.core.mail.backends.smtp.EmailBackend"
)
DEFAULT_FROM_EMAIL = f"ComptaFisca Acad Ventisax <{EMAIL_HOST_USER}>" if EMAIL_HOST_USER else "webmaster@localhost"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Back-office : Unfold, sans ressource externe (polices et scripts servis par le site).
UNFOLD = {
    "SITE_TITLE": "ComptaFisca Acad Ventisax",
    "SITE_HEADER": "ComptaFisca Acad Ventisax",
    "SITE_SYMBOL": "bolt",
    "SHOW_LANGUAGES": True,
}

LANGUAGE_CODE = "fr"
LANGUAGES = [("fr", _("Français")), ("en", _("English"))]
LOCALE_PATHS = [BASE_DIR / "locale"]
MODELTRANSLATION_DEFAULT_LANGUAGE = "fr"
MODELTRANSLATION_FALLBACK_LANGUAGES = ("fr",)
TIME_ZONE = "Africa/Douala"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = Path(os.environ.get("DJANGO_STATIC_ROOT", BASE_DIR / "staticfiles"))
STATICFILES_DIRS = [BASE_DIR / "static"]
# Versionnement anti-cache : empreinte dans le nom en production (manifeste),
# ?v=<empreinte> en développement (config/storage.py).
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "config.storage.VersionedStaticFilesStorage"
        if DEBUG
        else "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"
    },
}
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

if not DEBUG:
    # PythonAnywhere termine le HTTPS en amont et transmet X-Forwarded-Proto.
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    # Préfixe __Host- : cookie limité à HTTPS, à ce domaine exact et au chemin /, impossible à injecter
    # depuis un autre sous-domaine de pythonanywhere.com.
    SESSION_COOKIE_NAME = "__Host-sessionid"
    CSRF_COOKIE_NAME = "__Host-csrftoken"
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    # Préchargement HSTS impossible : la liste de préchargement n'accepte que des domaines enregistrables,
    # pas un sous-domaine de pythonanywhere.com.
    SILENCED_SYSTEM_CHECKS = ["security.W021"]

# Exercice de référence du contenu fiscal (C3) : CGI Cameroun éd. 2026. Les taux en vigueur sont lus dans
# referentiel.FiscalParameter pour cet exercice ; passer à la loi de finances suivante = changer cette valeur.
FISCAL_YEAR = 2026
