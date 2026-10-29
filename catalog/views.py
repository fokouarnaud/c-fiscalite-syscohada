from django import forms
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from courses.models import Formation, Module

from .services import InvalidJoinCode, enroll_open, join_with_code


def _row(formation, user):
    modules = Module.objects.filter(partie__formation=formation)
    hours = modules.aggregate(total=Sum("duration_hours"))["total"]
    return {
        "formation": formation,
        "parties": list(formation.parties.prefetch_related("modules")),
        "hours": hours or 0,
        "module_count": modules.count(),
        "enrolled": user.is_authenticated and formation.enrollments.filter(user=user).exists(),
    }


def _require_learner(user):
    if not user.is_learner:
        raise PermissionDenied


def catalogue(request):
    """Catalogue public (US-01) : seules les formations ouvertes sont listées."""
    rows = [_row(f, request.user) for f in Formation.objects.filter(is_open=True)]
    return render(request, "catalog/catalogue.html", {"rows": rows})


def formation_detail(request, public_id):
    formation = get_object_or_404(Formation, public_id=public_id, is_open=True)
    return render(request, "catalog/formation_detail.html", {"row": _row(formation, request.user)})


@require_POST
@login_required
def enroll(request, public_id):
    """Inscription libre (US-05)."""
    _require_learner(request.user)
    formation = get_object_or_404(Formation, public_id=public_id, is_open=True)
    enroll_open(request.user, formation)
    return redirect("dashboard")


class JoinCodeForm(forms.Form):
    code = forms.CharField(label=_("Code de promotion"), max_length=20)


@login_required
def join(request):
    """Rejoindre une promotion avec son code (US-06)."""
    _require_learner(request.user)
    form = JoinCodeForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            join_with_code(request.user, form.cleaned_data["code"])
        except InvalidJoinCode:
            form.add_error("code", _("Ce code est inconnu ou n'est plus actif."))
        else:
            return redirect("dashboard")
    return render(request, "catalog/join.html", {"form": form})
