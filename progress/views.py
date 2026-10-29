import csv
from decimal import ROUND_HALF_UP, Decimal

from django import forms
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from accounts.models import Promotion, User
from assessments.models import Assessment, Attempt, AttemptQuestion, Question
from catalog.models import Enrollment
from courses.models import Module, Partie

from .models import Announcement, Deadline
from .services import late_deadlines, module_completed


FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def _csv_cell(value):
    """Neutralise l'injection de formules : Excel exécuterait une cellule qui commence par = + - @."""
    text = str(value)
    return "'" + text if text.startswith(FORMULA_PREFIXES) else text


def _require_staff_role(user):
    if not (user.is_trainer or user.is_platform_admin):
        raise PermissionDenied


def _formation_assessments(formation):
    return Assessment.objects.filter(module__partie__formation=formation) | Assessment.objects.filter(
        partie__formation=formation
    )


def _tables(user):
    """Une table par formation : colonnes = modules et examens de parties, lignes = apprenants visibles."""
    promotions = Promotion.objects.visible_to(user).select_related("formation")
    tables = []
    for formation in {p.formation for p in promotions}:
        modules = list(Module.objects.filter(partie__formation=formation).order_by("partie__order", "order"))
        parties = list(Partie.objects.filter(formation=formation))
        exams = [Assessment.exam_for(p) for p in parties]
        enrollments = Enrollment.objects.filter(
            user__role=User.Role.LEARNER, promotion__in=[p for p in promotions if p.formation_id == formation.pk]
        ).select_related("user", "promotion").order_by("promotion__name", "user__username")
        rows = []
        for enrollment in enrollments:
            learner = enrollment.user
            exam_results = []
            for partie, exam in zip(parties, exams):
                best = exam.best_attempt(learner)
                exam_results.append({
                    "partie": partie,
                    "best": best.score_pct if best else None,
                    "attempts": exam.attempts.filter(user=learner).count(),
                    "max_attempts": exam.max_attempts,
                })
            rows.append({
                "learner": learner,
                "promotion": enrollment.promotion,
                "late": late_deadlines(learner, enrollment.promotion),
                "submitted": list(Attempt.objects.filter(
                    user=learner, submitted_at__isnull=False, assessment__in=_formation_assessments(formation),
                ).select_related("assessment__module", "assessment__partie").order_by("-submitted_at")),
                "modules": [module_completed(learner, m) for m in modules],
                "exams": exam_results,
            })
        tables.append({"formation": formation, "modules": modules, "parties": parties, "rows": rows})
    return sorted(tables, key=lambda t: t["formation"].order)


@login_required
def trainer_table(request):
    _require_staff_role(request.user)
    tables = _tables(request.user)
    rows = [row for table in tables for row in table["rows"]]
    return render(request, "progress/trainer_table.html", {"tables": tables, "rows": rows})


@login_required
def export_csv(request):
    _require_staff_role(request.user)
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="progression.csv"'
    response.write("﻿")  # BOM : Excel ouvre l'UTF-8 correctement
    writer = csv.writer(response, delimiter=";")
    for table in _tables(request.user):
        header = [_("Promotion"), _("Identifiant"), _("Nom")] + [m.title for m in table["modules"]]
        for partie in table["parties"]:
            header += [_("Examen %(partie)s (%%)") % {"partie": partie.title}, _("Tentatives %(partie)s") % {"partie": partie.title}]
        writer.writerow([_csv_cell(cell) for cell in header])
        for row in table["rows"]:
            learner = row["learner"]
            line = [row["promotion"].name, learner.username, learner.get_full_name()]
            line += [_("oui") if done else _("non") for done in row["modules"]]
            for result in row["exams"]:
                line += ["" if result["best"] is None else result["best"], result["attempts"]]
            writer.writerow([_csv_cell(cell) for cell in line])
    return response


def _visible_learners(user):
    """Apprenants des promotions visibles par ce formateur (tous les inscrits pour un admin)."""
    enrollments = Enrollment.objects.filter(user__role=User.Role.LEARNER)
    if not user.is_platform_admin:
        enrollments = enrollments.filter(promotion__in=Promotion.objects.visible_to(user))
    return User.objects.filter(pk__in=enrollments.values("user_id"))


def _answer_display(aq):
    question = aq.question
    if question.qtype == Question.Type.NUMERIC:
        return aq.answer_text
    if question.qtype == Question.Type.MATCHING:
        pairs = {str(p.public_id): p for p in question.pairs.all()}
        return " ; ".join(
            f"{pairs[left].left} → {pairs[right].right}" for left, right in aq.answer_json.items()
            if left in pairs and right in pairs
        )
    return ", ".join(c.text for c in aq.selected_choices.all())


@login_required
def attempt_review(request, public_id):
    """Détail d'une tentative envoyée d'un apprenant visible (US-28) ; une tentative en cours reste cachée."""
    _require_staff_role(request.user)
    attempts = Attempt.objects.select_related("user", "assessment")
    if not request.user.is_platform_admin:
        # US-61 : un apprenant inscrit à deux formations n'ouvre pas au formateur de l'une ses tentatives de l'autre.
        formations = Promotion.objects.visible_to(request.user).values("formation")
        attempts = attempts.filter(
            Q(assessment__module__partie__formation__in=formations) | Q(assessment__partie__formation__in=formations)
        )
    attempt = get_object_or_404(
        attempts, public_id=public_id, submitted_at__isnull=False, user__in=_visible_learners(request.user),
    )
    rows = []
    for aq in attempt.attempt_questions.select_related("question").prefetch_related(
        "question__choices", "question__pairs", "selected_choices"
    ):
        correct = [c.pk for c in aq.question.choices.all() if c.is_correct]
        selected = [c.pk for c in aq.selected_choices.all()]
        rows.append({
            "question": aq.question,
            "answer": _answer_display(aq),
            "score": aq.score(correct, selected),
            "time_spent_s": aq.time_spent_s,
        })
    return render(request, "progress/attempt_review.html", {"attempt": attempt, "rows": rows})


@login_required
def question_stats(request):
    """Taux de réussite par question sur les tentatives envoyées des apprenants visibles (US-29)."""
    _require_staff_role(request.user)
    formations = {p.formation_id for p in Promotion.objects.visible_to(request.user)}
    answered = AttemptQuestion.objects.filter(
        attempt__submitted_at__isnull=False, attempt__user__in=_visible_learners(request.user),
        question__module__partie__formation__in=formations,
    ).select_related("question").prefetch_related("question__choices", "question__pairs", "selected_choices")
    scores = {}
    for aq in answered:
        correct = [c.pk for c in aq.question.choices.all() if c.is_correct]
        scores.setdefault(aq.question, []).append(aq.score(correct, [c.pk for c in aq.selected_choices.all()]))
    stats = []
    questions = Question.objects.published().filter(module__partie__formation__in=formations).select_related("module")
    for question in questions.order_by("module__partie__order", "module__order", "pk"):
        values = scores.get(question, [])
        pct = None
        if values:
            mean = sum(values) / len(values) * 100
            pct = (Decimal(mean.numerator) / Decimal(mean.denominator)).quantize(Decimal("1"), ROUND_HALF_UP)
        stats.append({"question": question, "answers": len(values), "success_pct": pct})
    return render(request, "progress/question_stats.html", {"stats": stats})


class PromotionChoiceField(forms.ModelChoiceField):
    def __init__(self, user, **kwargs):
        promotions = Promotion.objects.visible_to(user)
        only = list(promotions[:2])
        if len(only) == 1:
            kwargs.setdefault("initial", only[0].public_id)  # une seule promotion : déjà choisie
        super().__init__(promotions, to_field_name="public_id", **kwargs)


class AnnouncementForm(forms.Form):
    title = forms.CharField(label=gettext_lazy("Titre"), max_length=200)
    body = forms.CharField(label=gettext_lazy("Message"), widget=forms.Textarea)

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["promotion"] = PromotionChoiceField(user, label=gettext_lazy("Promotion"))
        self.order_fields(["promotion", "title", "body"])


@login_required
def announcements(request):
    """Annonces des promotions du formateur (US-31)."""
    _require_staff_role(request.user)
    form = AnnouncementForm(request.user, request.POST or None)
    if request.method == "POST" and form.is_valid():
        Announcement.objects.create(
            promotion=form.cleaned_data["promotion"], author=request.user,
            title=form.cleaned_data["title"], body=form.cleaned_data["body"],
        )
        return redirect("trainer_announcements")
    items = Announcement.objects.filter(promotion__in=Promotion.objects.visible_to(request.user)).select_related("promotion")
    return render(request, "progress/announcements.html", {"form": form, "announcements": items})


class DeadlineForm(forms.Form):
    target = forms.CharField(label=gettext_lazy("Quiz ou examen"))
    due_at = forms.DateTimeField(label=gettext_lazy("Date limite"), input_formats=["%Y-%m-%dT%H:%M"])

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["promotion"] = PromotionChoiceField(user, label=gettext_lazy("Promotion"))
        self.order_fields(["promotion", "target", "due_at"])

    def clean(self):
        cleaned = super().clean()
        promotion, target = cleaned.get("promotion"), cleaned.get("target", "")
        if promotion is None:
            return cleaned
        kind, _sep, public_id = target.partition(":")
        try:
            if kind == "quiz":
                module = Module.objects.get(public_id=public_id, partie__formation=promotion.formation)
                cleaned["assessment"] = Assessment.quiz_for(module)
            elif kind == "exam":
                partie = Partie.objects.get(public_id=public_id, formation=promotion.formation)
                cleaned["assessment"] = Assessment.exam_for(partie)
            else:
                raise ValueError
        except (ValueError, Module.DoesNotExist, Partie.DoesNotExist, forms.ValidationError):
            self.add_error("target", _("Choisissez un quiz ou un examen de la formation de cette promotion."))
        return cleaned


@login_required
def deadlines(request):
    """Dates limites indicatives (US-32) : une seule par quiz ou examen et par promotion."""
    _require_staff_role(request.user)
    form = DeadlineForm(request.user, request.POST or None)
    if request.method == "POST" and form.is_valid():
        Deadline.objects.update_or_create(
            promotion=form.cleaned_data["promotion"], assessment=form.cleaned_data["assessment"],
            defaults={"due_at": form.cleaned_data["due_at"]},
        )
        return redirect("trainer_deadlines")
    promotions = Promotion.objects.visible_to(request.user)
    targets = [
        {"promotion": p, "modules": Module.objects.filter(partie__formation=p.formation).order_by("partie__order", "order"),
         "parties": Partie.objects.filter(formation=p.formation)}
        for p in promotions.select_related("formation")
    ]
    items = Deadline.objects.filter(promotion__in=promotions).select_related("promotion", "assessment")
    return render(request, "progress/deadlines.html", {"form": form, "deadlines": items, "targets": targets})
