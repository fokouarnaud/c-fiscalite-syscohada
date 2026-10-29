from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect, render
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.utils.translation import gettext as _

from courses.access import accessible_formations
from courses.models import Partie
from progress.models import Announcement, SectionView
from progress.services import exam_unlocked, module_row, progress_pct, steps_pct

from .models import SignupThrottle, User
from .signup import (
    SignupForm, client_ip_hash, create_pending_learner, email_verification_token, is_signup_throttled,
    send_verification_email,
)


@login_required
def dashboard(request):
    """« Mes cours » : une formation à la fois (sélecteur), reprise à la section, plan complet numéroté M1, M2…"""
    if request.user.is_trainer or (request.user.is_platform_admin and not request.user.enrollments.exists()):
        return redirect("trainer_table")
    parts = []
    formations = accessible_formations(request.user)
    parties = Partie.objects.filter(formation__in=formations).select_related("formation")
    for partie in parties.order_by("formation__order", "formation", "order"):
        parts.append({
            "partie": partie,
            "progress": progress_pct(request.user, partie),
            "modules": [module_row(request.user, m) for m in partie.modules.prefetch_related("sections")],
            "exam_unlocked": exam_unlocked(request.user, partie),
        })
    formation_blocks = []
    for row in parts:
        if not formation_blocks or formation_blocks[-1]["formation"] != row["partie"].formation:
            formation_blocks.append({"formation": row["partie"].formation, "parts": [], "modules": [], "resume": None})
        block = formation_blocks[-1]
        block["parts"].append(row)
        for item in row["modules"]:
            block["modules"].append(item["module"])
            item["number"] = len(block["modules"])  # numérotation sur toute la formation, comme le texte des cours
            if block["resume"] is None and not item["done"]:
                block["resume"], block["resume_row"], block["resume_part"] = item["module"], item, row["partie"]
    for block in formation_blocks:
        block["progress"] = steps_pct(request.user, block["modules"])
        block["resume_section"] = block["resume_row"]["next_section"] if block["resume"] else None
    announcements = Announcement.objects.filter(promotion__enrollments__user=request.user)[:5]
    return render(request, "accounts/dashboard.html", {
        "parts": parts,
        "formations": formation_blocks,
        "current": _current_formation(request, formation_blocks),
        "announcements": announcements,
    })


def _current_formation(request, blocks):
    """Formation affichée : celle du sélecteur si l'utilisateur y a accès, sinon la dernière travaillée, sinon la première."""
    if not blocks:
        return None
    wanted = request.GET.get("formation", "")
    chosen = next((b for b in blocks if str(b["formation"].public_id) == wanted), None)
    if chosen is None:
        last = (
            SectionView.objects.filter(user=request.user, section__module__partie__formation__in=[b["formation"] for b in blocks])
            .order_by("-viewed_at", "-pk").values_list("section__module__partie__formation", flat=True).first()
        )
        chosen = next((b for b in blocks if b["formation"].pk == last), blocks[0])
    return chosen


def signup(request):
    """Inscription publique (US-02, US-03)."""
    form = SignupForm(request.POST or None)
    if request.method == "POST":
        if form.is_bot:  # piège rempli : on simule un succès sans rien créer
            return redirect("signup_done")
        ip_hash = client_ip_hash(request)
        if is_signup_throttled(ip_hash):
            return HttpResponse(_("Trop d'inscriptions depuis cette connexion. Réessayez dans une heure."), status=429)
        if form.is_valid():
            SignupThrottle.objects.create(ip_hash=ip_hash)
            user = create_pending_learner(form)
            send_verification_email(request, user)
            return redirect("signup_done")
    return render(request, "accounts/signup.html", {"form": form})


def signup_done(request):
    return render(request, "accounts/signup_done.html")


def verify_email(request, uidb64, token):
    try:
        user = User.objects.get(pk=force_str(urlsafe_base64_decode(uidb64)))
    except (User.DoesNotExist, ValueError, TypeError, OverflowError):
        user = None
    if user is None or not email_verification_token.check_token(user, token):
        return HttpResponseBadRequest(_("Ce lien de confirmation est invalide ou a déjà servi."))
    user.is_active = True
    user.email_verified = True
    user.save(update_fields=["is_active", "email_verified"])
    messages.success(request, _("Adresse confirmée. Vous pouvez vous connecter."))
    return redirect("login")
