from django.contrib.auth.decorators import login_required
import uuid

from django.http import Http404, HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from courses.access import accessible_formations
from courses.models import Module, Partie
from progress.services import module_completed, module_number, next_module

from .models import Assessment, Attempt, AttemptQuestion
from .services import (
    AttemptClosed,
    AttemptLimitReached,
    ExamLocked,
    close_if_expired,
    save_answer,
    start_attempt,
    submit_attempt,
)


def _own_attempt(request, public_id):
    return get_object_or_404(Attempt.objects.select_related("assessment"), public_id=public_id, user=request.user)


def _uuids(values):
    """UUID valides ou ValueError : aucune valeur brute du formulaire n'atteint la base."""
    return [uuid.UUID(str(value)) for value in values]


def _attempts_left(user, assessment):
    if assessment.max_attempts is None:
        return None
    return max(0, assessment.max_attempts - assessment.attempts.filter(user=user).count())


@login_required
@require_POST
def start_quiz(request, module_id):
    module = get_object_or_404(Module, public_id=module_id, partie__formation__in=accessible_formations(request.user))
    attempt = start_attempt(request.user, Assessment.quiz_for(module))
    return redirect("attempt_detail", public_id=attempt.public_id)


@login_required
def exam(request, partie_id):
    partie = get_object_or_404(Partie, public_id=partie_id, formation__in=accessible_formations(request.user))
    assessment = Assessment.exam_for(partie)
    if request.method == "POST":
        try:
            attempt = start_attempt(request.user, assessment)
        except (ExamLocked, AttemptLimitReached):
            return HttpResponse(status=403)
        return redirect("attempt_detail", public_id=attempt.public_id)
    missing = [{"module": m, "number": module_number(m)} for m in partie.modules.all() if not module_completed(request.user, m)]
    open_attempt = assessment.attempts.filter(user=request.user, submitted_at__isnull=True).last()
    if open_attempt and close_if_expired(open_attempt).submitted_at:
        open_attempt = None
    return render(request, "assessments/exam.html", {
        "partie": partie,
        "assessment": assessment,
        "unlocked": not missing,
        "missing_modules": missing,
        "attempts_left": _attempts_left(request.user, assessment),
        "best": assessment.best_attempt(request.user),
        "open_attempt": open_attempt,
    })


@login_required
def attempt_detail(request, public_id):
    attempt = close_if_expired(_own_attempt(request, public_id))
    if attempt.submitted_at:
        return redirect("attempt_result", public_id=attempt.public_id)
    rows = [
        {
            "question": aq.question,
            "choices": aq.ordered_choices(),
            "selected": set(aq.selected_choices.values_list("public_id", flat=True)),
            "answer_text": aq.answer_text,
            # Appariement : éléments de gauche dans l'ordre du cours, colonne de droite dans l'ordre tiré.
            "lefts": [
                {"pair": p, "chosen": aq.answer_json.get(str(p.public_id), "")} for p in aq.question.pairs.all()
            ],
            "rights": aq.ordered_pairs(),
            "journal_rows": _journal_rows(aq),
            "answered": aq.answered_at is not None,
        }
        for aq in attempt.attempt_questions.select_related("question").prefetch_related(
            "question__choices", "question__pairs", "selected_choices"
        )
    ]
    remaining = None
    if attempt.deadline:
        remaining = max(0, int((attempt.deadline - timezone.now()).total_seconds()))
    # Envoi demandé avec des questions sans réponse : on les liste et on demande confirmation (aucun envoi à l'aveugle).
    unanswered = [
        {"number": n, "question": row["question"]} for n, row in enumerate(rows, start=1) if not row["answered"]
    ] if request.GET.get("envoi") else []
    return render(request, "assessments/attempt.html", {
        "attempt": attempt, "rows": rows, "remaining_seconds": remaining, "unanswered": unanswered,
    })


JOURNAL_GRID_MIN = 6


def _journal_rows(aq):
    """Grille de saisie d'une écriture (US-34) : lignes déjà saisies, puis des lignes vides, six au moins."""
    if aq.question.qtype != aq.question.Type.JOURNAL:
        return []
    saved = aq.answer_json.get("lines", [])
    return saved + [{}] * max(JOURNAL_GRID_MIN - len(saved), 1)


def _journal_lines(post):
    """Écriture au journal (US-34) : une valeur par ligne dans line_account, line_side, line_amount et line_label."""
    columns = [post.getlist(f"line_{field}") for field in ("account", "side", "amount", "label")]
    count = max(len(column) for column in columns)
    return [
        dict(zip(("account", "side", "amount", "label"), (column[i] if i < len(column) else "" for column in columns)))
        for i in range(count)
    ]


@login_required
@require_POST
def save_answer_view(request, public_id):
    attempt = _own_attempt(request, public_id)
    try:
        question_id, = _uuids([request.POST.get("question")])
        choice_ids = _uuids(request.POST.getlist("choices"))
        # Appariement : un champ « pair_<paire de gauche> » = <paire de droite> par élément.
        pairs = {
            str(uuid.UUID(key[len("pair_"):])): str(uuid.UUID(value))
            for key, value in request.POST.items() if key.startswith("pair_") and value
        }
        time_spent = int(request.POST.get("time_spent") or 0)
    except ValueError:
        return HttpResponseBadRequest()
    try:
        save_answer(
            attempt, question_id, choice_ids,
            text=request.POST.get("answer_text"), pairs=pairs, time_spent_s=time_spent, lines=_journal_lines(request.POST),
        )
    except AttemptQuestion.DoesNotExist:
        raise Http404
    except AttemptClosed:
        return HttpResponse(status=409) if request.headers.get("HX-Request") else redirect("attempt_detail", public_id=attempt.public_id)
    if request.headers.get("HX-Request"):
        return HttpResponse(status=200)
    # Sans JavaScript : retour à la question enregistrée.
    return redirect(reverse("attempt_detail", args=[attempt.public_id]) + f"#q-{question_id}")


@login_required
@require_POST
def submit_view(request, public_id):
    attempt = close_if_expired(_own_attempt(request, public_id))
    if attempt.submitted_at is None:
        blank = attempt.attempt_questions.filter(answered_at__isnull=True).exists()
        if blank and request.POST.get("confirm") != "1":
            return redirect(reverse("attempt_detail", args=[attempt.public_id]) + "?envoi=1#envoi")
        submit_attempt(attempt)
    return redirect("attempt_result", public_id=attempt.public_id)


@login_required
def result(request, public_id):
    attempt = close_if_expired(_own_attempt(request, public_id))
    if attempt.submitted_at is None:
        return redirect("attempt_detail", public_id=attempt.public_id)
    is_exam = attempt.assessment.is_exam
    feedback = [] if is_exam else attempt.feedback()
    mistakes = [item for item in feedback if item["score"] < 1]
    context = {
        "attempt": attempt,
        "show_correction": not is_exam,
        "feedback": mistakes if request.GET.get("erreurs") else feedback,
        "mistakes_only": bool(request.GET.get("erreurs")),
        "total_count": len(feedback),
        "mistake_count": len(mistakes),
        "module_scores": attempt.module_scores() if is_exam else {},
        "attempts_left": _attempts_left(request.user, attempt.assessment),
    }
    if not is_exam and module_completed(request.user, attempt.assessment.module):
        # Le quiz termine le module : proposer la suite (module suivant de la partie, sinon son examen).
        module = attempt.assessment.module
        following = next_module(module)
        context["module_done"] = True
        if following is not None and following.partie_id == module.partie_id:
            context["next_module"], context["next_number"] = following, module_number(following)
    return render(request, "assessments/result.html", context)
