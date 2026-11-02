"""Échec CSRF (US-02) : jamais la page brute de Django.

Une connexion réussie renouvelle le jeton CSRF ; la même page de connexion, resoumise (double clic, retour arrière,
autre onglet), est donc refusée. Si l'utilisateur est déjà connecté, on le conduit simplement à sa destination ;
sinon, une page explique que la page a expiré et propose de la recharger. Toute autre action reste refusée (403).
"""
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme


def safe_next(request):
    target = request.POST.get("next") or request.GET.get("next") or ""
    allowed = url_has_allowed_host_and_scheme(target, allowed_hosts={request.get_host()},
                                              require_https=request.is_secure())
    return target if allowed else reverse("dashboard")


def csrf_failure(request, reason=""):
    login_path = reverse("login")
    if request.path == login_path and request.user.is_authenticated:
        return redirect(safe_next(request))
    retry = request.get_full_path() if request.path == login_path else request.META.get("HTTP_REFERER", "")
    if not url_has_allowed_host_and_scheme(retry, allowed_hosts={request.get_host()}):
        retry = reverse("dashboard")
    return render(request, "403_csrf.html", {"retry": retry}, status=403)
