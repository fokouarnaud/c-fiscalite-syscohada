"""En-tête Content-Security-Policy : seuls les scripts servis par le site s'exécutent.

Django 5.2 n'a pas de CSP intégrée. Les styles en ligne restent permis (barres de progression, HTMX),
mais aucun script en ligne ni gestionnaire `on…=` : une injection HTML ne peut donc rien exécuter.

Exception limitée au back-office (/admin/, réservé au personnel) : l'Alpine.js d'Unfold évalue ses expressions
avec `new Function`, d'où 'unsafe-eval' sur ces seules pages ; le script en ligne y reste interdit.
"""
import re


def _policy(script_src):
    return "; ".join([
        "default-src 'self'",
        f"script-src {script_src}",
        "style-src 'self' 'unsafe-inline'",
        "img-src 'self' data:",
        "font-src 'self'",
        "connect-src 'self'",
        "object-src 'none'",
        "base-uri 'self'",
        "form-action 'self'",
        "frame-ancestors 'none'",
    ])


CONTENT_SECURITY_POLICY = _policy("'self'")
ADMIN_CONTENT_SECURITY_POLICY = _policy("'self' 'unsafe-eval'")
ADMIN_PATH = re.compile(r"^/(?:[a-z]{2}/)?admin/")


class ContentSecurityPolicyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        policy = ADMIN_CONTENT_SECURITY_POLICY if ADMIN_PATH.match(request.path) else CONTENT_SECURITY_POLICY
        response.setdefault("Content-Security-Policy", policy)
        return response
