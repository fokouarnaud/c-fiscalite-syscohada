"""Contrôles de déploiement propres aux comptes (exécutés par `check --deploy` dans deploy.sh)."""
from django.conf import settings
from django.core.checks import Error, register


@register(deploy=True)
def smtp_credentials(app_configs, **kwargs):
    """US-01 : sans identifiants SMTP, ni lien de vérification ni lien de mot de passe oublié ne peut partir."""
    if settings.EMAIL_HOST_USER and settings.EMAIL_HOST_PASSWORD:
        return []
    return [Error(
        "EMAIL_HOST_USER ou EMAIL_HOST_PASSWORD est vide : aucun e-mail d'inscription ni de mot de passe oublié ne peut partir.",
        hint="Renseigner l'adresse Gmail et son mot de passe d'application dans le .env du serveur.",
        id="accounts.E001",
    )]
