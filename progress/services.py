"""Progression (AGENTS.md, Q9) : sections vues + quiz envoyé ; examen ouvert quand tous les modules sont terminés."""
from django.db.models import Q

from assessments.models import Assessment, Attempt, Question
from courses.models import Module, Section

from .models import SectionView


def mark_section_viewed(user, section):
    from certificates.services import refresh_module_badge

    _, created = SectionView.objects.get_or_create(user=user, section=section)
    if created:
        refresh_module_badge(user, section.module)


def module_has_quiz(module):
    return Question.objects.published().filter(module=module, usage=Question.Usage.QUIZ).exists()


def _quiz_submitted(user, module):
    return Attempt.objects.filter(
        user=user,
        assessment__kind=Assessment.Kind.MODULE_QUIZ,
        assessment__module=module,
        submitted_at__isnull=False,
    ).exists()


def _module_steps(user, module):
    """Renvoie (étapes faites, étapes totales) pour un module."""
    section_ids = list(Section.objects.filter(module=module).values_list("pk", flat=True))
    done = SectionView.objects.filter(user=user, section_id__in=section_ids).count()
    total = len(section_ids)
    if module_has_quiz(module):
        total += 1
        done += _quiz_submitted(user, module)
    return done, total


def module_completed(user, module):
    done, total = _module_steps(user, module)
    return done == total


def module_row(user, module):
    """État d'un module pour « Mes cours » : étapes faites, terminé, prochaine section à lire (None : il reste le quiz ou rien)."""
    done, total = _module_steps(user, module)
    viewed = set(SectionView.objects.filter(user=user, section__module=module).values_list("section_id", flat=True))
    next_section = next((s for s in module.sections.all() if s.pk not in viewed), None)
    return {"module": module, "done": done == total, "steps_done": done, "steps_total": total, "next_section": next_section}


def module_number(module):
    """Numéro M1, M2… d'un module sur toute sa formation, comme le texte des cours et le tableau formateur."""
    earlier = Module.objects.filter(partie__formation=module.partie.formation_id, partie__order__lt=module.partie.order).count()
    return earlier + list(module.partie.modules.values_list("pk", flat=True)).index(module.pk) + 1


def next_module(module):
    """Module qui suit dans la formation (partie suivante comprise), ou None pour le dernier."""
    return (
        Module.objects.filter(partie__formation=module.partie.formation_id)
        .filter(Q(partie__order__gt=module.partie.order) | Q(partie=module.partie_id, order__gt=module.order))
        .order_by("partie__order", "order").select_related("partie").first()
    )


def next_step(user, module):
    """Étape suivante d'un module : première section non lue, sinon son quiz à envoyer, sinon None (module terminé)."""
    viewed = set(SectionView.objects.filter(user=user, section__module=module).values_list("section_id", flat=True))
    section = next((s for s in module.sections.all() if s.pk not in viewed), None)
    if section is not None:
        return {"section": section, "started": bool(viewed)}
    if module_has_quiz(module) and not _quiz_submitted(user, module):
        return {"quiz": True}
    return None


def exam_unlocked(user, partie):
    return all(module_completed(user, m) for m in partie.modules.all())


def progress_pct(user, partie):
    return steps_pct(user, partie.modules.all())


def steps_pct(user, modules):
    """Part des étapes faites (sections vues, quiz envoyés) sur un ensemble de modules : une partie ou toute une formation."""
    done = total = 0
    for module in modules:
        d, t = _module_steps(user, module)
        done, total = done + d, total + t
    return done * 100 // total if total else 0


def outline(user, partie, current_section=None, current_module=None):
    """Sommaire latéral façon NetAcad : modules de la partie, leurs sections, états vu / terminé / courant."""
    if current_section is not None:
        current_module = current_section.module
    viewed = set(
        SectionView.objects.filter(user=user, section__module__partie=partie).values_list("section_id", flat=True)
    )
    # Numérotation sur toute la formation (M1, M2…), comme « Mes cours » et le texte des cours.
    first = Module.objects.filter(partie__formation=partie.formation_id, partie__order__lt=partie.order).count()
    rows = []
    for number, module in enumerate(partie.modules.prefetch_related("sections"), start=first + 1):
        rows.append({
            "module": module,
            "number": number,
            "current": current_module is not None and module.pk == current_module.pk,
            "has_quiz": current_module is not None and module.pk == current_module.pk and module_has_quiz(module),
            "done": module_completed(user, module),
            "sections": [
                {
                    "section": s,
                    "viewed": s.pk in viewed,
                    "current": current_section is not None and s.pk == current_section.pk,
                }
                for s in module.sections.all()
            ],
        })
    return rows


def _deadline_met(user, assessment):
    attempts = assessment.attempts.filter(user=user, submitted_at__isnull=False)
    if assessment.is_exam:
        return attempts.filter(score_pct__gte=assessment.pass_threshold).exists()
    return attempts.exists()


def late_deadlines(user, promotion, now=None):
    """Dates limites dépassées sans quiz envoyé ou sans examen réussi (« en retard », US-32)."""
    from django.utils import timezone

    from .models import Deadline

    now = now or timezone.now()
    passed = Deadline.objects.filter(promotion=promotion, due_at__lt=now).select_related("assessment")
    return [d for d in passed if not _deadline_met(user, d.assessment)]
