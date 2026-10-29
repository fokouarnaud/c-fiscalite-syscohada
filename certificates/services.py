"""Badges et certificats (AGENTS.md, E10) : badge par module terminé et par partie réussie ; un certificat par partie
réussie, émis quand le nom complet est connu et relevé si une meilleure tentative suit."""
from assessments.models import Assessment
from courses.models import Partie
from progress.services import module_completed

from .models import Badge, Certificate


def refresh_module_badge(user, module):
    if module_completed(user, module):
        Badge.objects.get_or_create(user=user, kind=Badge.Kind.MODULE, module=module)


def refresh_partie_achievements(user, partie):
    best = Assessment.exam_for(partie).best_attempt(user)
    if best is None or not best.passed:
        return None
    Badge.objects.get_or_create(user=user, kind=Badge.Kind.PARTIE, partie=partie)
    return issue_certificate(user, partie, best)


def issue_certificate(user, partie, best):
    certificate = Certificate.objects.filter(user=user, partie=partie).first()
    if certificate is not None:
        if best.score_pct > certificate.score_pct:
            certificate.score_pct, certificate.attempt = best.score_pct, best
            certificate.save(update_fields=["score_pct", "attempt"])
        return certificate
    if not (user.first_name.strip() and user.last_name.strip()):
        return None  # le titulaire doit d'abord compléter son nom (US-24)
    return Certificate.objects.create(
        user=user, partie=partie, attempt=best, holder_name=user.get_full_name().strip(), score_pct=best.score_pct
    )


def refresh_after_attempt(attempt):
    """Appelé à chaque envoi de tentative : quiz -> badge du module ; examen -> badge et certificat de la partie."""
    assessment = attempt.assessment
    if assessment.is_exam:
        refresh_partie_achievements(attempt.user, assessment.partie)
    else:
        refresh_module_badge(attempt.user, assessment.module)


def refresh_all_certificates(user):
    for partie in Partie.objects.filter(exam__attempts__user=user).distinct():
        refresh_partie_achievements(user, partie)
