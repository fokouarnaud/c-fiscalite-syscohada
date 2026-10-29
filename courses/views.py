from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import redirect, render
from django.utils.translation import get_language

from progress.models import SectionView
from progress.services import mark_section_viewed, module_has_quiz, module_number, next_module, next_step, outline
from referentiel.models import FiscalParameter

from .access import accessible_formations
from .models import Formation, Module, Section
from .rendering import render_markdown


def _catalogue_or_404(formation_filter):
    """Contenu hors inscription (US-11) : renvoi vers la fiche du catalogue si la formation est ouverte, sinon 404."""
    formation = Formation.objects.filter(is_open=True, **formation_filter).first()
    if formation is None:
        raise Http404
    return redirect("formation_detail", public_id=formation.public_id)


@login_required
def module_detail(request, public_id):
    module = Module.objects.filter(public_id=public_id, partie__formation__in=accessible_formations(request.user)).first()
    if module is None:
        return _catalogue_or_404({"parties__modules__public_id": public_id})
    viewed = set(SectionView.objects.filter(user=request.user, section__module=module).values_list("section_id", flat=True))
    sections = [{"section": s, "viewed": s.pk in viewed} for s in module.sections.all()]
    step = next_step(request.user, module)
    following = next_module(module) if step is None else None
    return render(request, "courses/module_detail.html", {
        "module": module,
        "number": module_number(module),
        "sections": sections,
        "outline": outline(request.user, module.partie, current_module=module),
        "has_quiz": module_has_quiz(module),
        "step": step,
        # Module terminé : l'examen de la partie si c'était son dernier module, sinon le module suivant.
        "next_module": following if following is not None and following.partie_id == module.partie_id else None,
        "next_number": module_number(following) if following is not None else None,
    })


@login_required
def section_detail(request, public_id):
    section = Section.objects.select_related("module__partie").filter(
        public_id=public_id,
        module__partie__formation__in=accessible_formations(request.user),
    ).first()
    if section is None:
        return _catalogue_or_404({"parties__modules__sections__public_id": public_id})
    mark_section_viewed(request.user, section)
    siblings = list(section.module.sections.all())
    index = siblings.index(section)
    lang = get_language()
    body_html = render_markdown(section.body_md)
    return render(request, "courses/section_detail.html", {
        "section": section,
        "body_html": body_html,
        # US-26 : taux en vigueur lus par les calculateurs, seulement si la section en contient un.
        "calc_params": FiscalParameter.objects.in_force() if 'data-calc="' in body_html else None,
        "number": module_number(section.module),
        "position": index + 1,
        "total": len(siblings),
        "previous": siblings[index - 1] if index > 0 else None,
        "next": siblings[index + 1] if index + 1 < len(siblings) else None,
        "fallback_fr": lang != "fr" and not getattr(section, f"body_md_{lang}", ""),
        "outline": outline(request.user, section.module.partie, current_section=section),
    })
