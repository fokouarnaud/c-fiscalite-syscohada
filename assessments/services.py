"""Cycle de vie des tentatives : démarrage, reprise, sauvegarde des réponses, envoi (AGENTS.md, Q8/Q8b)."""
import random
from datetime import timedelta
from decimal import ROUND_HALF_UP, Decimal

from django.db import transaction
from django.utils import timezone

from .models import Attempt, AttemptQuestion


class ExamLocked(Exception):
    """L'examen de partie n'est pas encore débloqué pour cet apprenant."""


class AttemptLimitReached(Exception):
    """Toutes les tentatives autorisées ont été utilisées."""


class AttemptClosed(Exception):
    """La tentative est envoyée ou son temps est écoulé."""


def percentage(scores):
    if not scores:
        return Decimal("0.00")
    total = sum(scores) / len(scores) * 100
    return (Decimal(total.numerator) / Decimal(total.denominator)).quantize(Decimal("0.01"), ROUND_HALF_UP)


@transaction.atomic
def start_attempt(user, assessment, now=None, rng=random):
    """Reprend la tentative ouverte s'il y en a une, sinon en démarre une nouvelle."""
    from progress.services import exam_unlocked

    now = now or timezone.now()
    if assessment.is_exam and not exam_unlocked(user, assessment.partie):
        raise ExamLocked
    open_attempt = assessment.attempts.filter(user=user, submitted_at__isnull=True).last()
    if open_attempt:
        close_if_expired(open_attempt, now)
        if open_attempt.submitted_at is None:
            return open_attempt
    used = assessment.attempts.filter(user=user).count()
    if assessment.max_attempts is not None and used >= assessment.max_attempts:
        raise AttemptLimitReached
    deadline = now + timedelta(minutes=assessment.duration_minutes) if assessment.duration_minutes else None
    attempt = Attempt.objects.create(
        user=user, assessment=assessment, number=used + 1, started_at=now, deadline=deadline
    )
    rows = []
    for i, question in enumerate(assessment.question_pool(rng)):
        if question.qtype == question.Type.MATCHING:
            order = list(question.pairs.values_list("pk", flat=True))
            rng.shuffle(order)  # sinon la colonne de droite donnerait la réponse
        else:
            order = list(question.choices.values_list("pk", flat=True))
            if assessment.shuffle:
                rng.shuffle(order)
        rows.append(AttemptQuestion(attempt=attempt, question=question, order=i, choice_order=order))
    AttemptQuestion.objects.bulk_create(rows)
    return attempt


MAX_TIME_PER_SAVE = 3600  # secondes : borne d'un temps déclaré par le navigateur


JOURNAL_MAX_LINES = 20
JOURNAL_FIELDS = {"account": 12, "side": 6, "amount": 20, "label": 200}  # champ -> longueur maximale gardée


def _clean_journal_lines(lines):
    """Écriture saisie (US-34) : champs connus seulement, tronqués ; un sens inconnu est vidé."""
    cleaned = []
    for line in list(lines or [])[:JOURNAL_MAX_LINES]:
        row = {field: str(line.get(field) or "").strip()[:size] for field, size in JOURNAL_FIELDS.items()}
        if row["side"] not in ("debit", "credit"):
            row["side"] = ""
        cleaned.append(row)
    return cleaned


def save_answer(attempt, question_id, choice_ids, now=None, text=None, pairs=None, time_spent_s=0, lines=None):
    """Enregistre la réponse ; question, choix et paires sont désignés par leur identifiant public (UUID).

    `text` : saisie d'une question numérique ; `pairs` : {paire de gauche: paire de droite} d'un appariement ;
    `lines` : lignes {account, side, amount, label} d'une écriture au journal ;
    `time_spent_s` : temps passé sur la question depuis son affichage, ajouté au total (US-20, US-28).
    """
    now = now or timezone.now()
    if attempt.submitted_at is not None or (attempt.deadline and now >= attempt.deadline):
        raise AttemptClosed
    aq = attempt.attempt_questions.select_related("question").get(question__public_id=question_id)
    question = aq.question
    if question.qtype == question.Type.NUMERIC:
        aq.answer_text = (text or "").strip()[:50]
    elif question.qtype == question.Type.MATCHING:
        known = {str(pk) for pk in question.pairs.values_list("public_id", flat=True)}
        aq.answer_json = {str(k): str(v) for k, v in (pairs or {}).items() if str(k) in known and str(v) in known}
    elif question.qtype == question.Type.JOURNAL:
        aq.answer_json = {"lines": _clean_journal_lines(lines)}
    else:
        aq.selected_choices.set(question.choices.filter(public_id__in=choice_ids))
    aq.time_spent_s = min(aq.time_spent_s + max(0, int(time_spent_s or 0)), MAX_TIME_PER_SAVE)
    aq.answered_at = now
    aq.save(update_fields=["answered_at", "answer_text", "answer_json", "time_spent_s"])


@transaction.atomic
def submit_attempt(attempt, now=None, auto=False):
    now = now or timezone.now()
    attempt.score_pct = percentage([item["score"] for item in attempt.feedback()])
    attempt.submitted_at = now
    attempt.auto_submitted = auto
    attempt.save(update_fields=["score_pct", "submitted_at", "auto_submitted"])
    from certificates.services import refresh_after_attempt

    refresh_after_attempt(attempt)
    return attempt


def close_if_expired(attempt, now=None):
    """Envoie automatiquement, à l'heure limite, une tentative dont le temps est écoulé."""
    now = now or timezone.now()
    if attempt.submitted_at is None and attempt.deadline and now >= attempt.deadline:
        submit_attempt(attempt, now=attempt.deadline, auto=True)
    return attempt
