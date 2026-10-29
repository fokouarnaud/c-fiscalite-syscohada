"""Import idempotent du contenu versionné (manifeste JSON + fichiers Markdown fr/en + questions JSON)."""
import json
from decimal import Decimal
from pathlib import Path

from django.db import transaction

from assessments.models import Question

from .models import Formation, Module, Partie, Section

LANGS = ("fr", "en")


def _translated(data, field):
    values = data.get(field) or {}
    return {f"{field}_{lang}": values.get(lang, "") for lang in LANGS}


def _read(path):
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _question_signature(question):
    return (
        question.qtype, question.usage,
        question.prompt_fr, question.prompt_en, question.explanation_fr, question.explanation_en,
        tuple((c.text_fr, c.text_en, c.is_correct, json.dumps(c.shape, sort_keys=True)) for c in question.choices.all()),
        question.numeric_value, question.unit, question.tolerance_pct, question.tolerance_abs, question.hotspot_svg,
        tuple((p.left_fr, p.left_en, p.right_fr, p.right_en) for p in question.pairs.all()),
        tuple((l.account, l.account_match, l.side, l.amount, l.label_fr, l.label_en) for l in question.journal_lines.all()),
        question.exercice,
    )


def _read_inside(folder, relative):
    """Lit un fichier du dossier du module ; un chemin qui en sort (« ../ ») est refusé."""
    path = (folder / relative).resolve()
    if not path.is_relative_to(folder.resolve()):
        raise ValueError(f"Chemin hors du dossier du module : {relative}")
    return path.read_text(encoding="utf-8")


def _import_questions(module, path, stats, prefix=""):
    folder = path.parent
    if not path.exists():
        return
    for data in json.loads(path.read_text(encoding="utf-8")):
        if prefix and not data["id"].startswith(f"{prefix}-"):
            # US-70 (U10) : C- pour la comptabilité, F- pour la fiscalité ; tout l'import est annulé.
            raise ValueError(f"Identifiant de question sans le préfixe {prefix}- de sa formation : {data['id']}")
        question = Question.objects.filter(external_id=data["id"]).select_related("module__partie").first()
        if question and question.module.partie.formation_id != module.partie.formation_id:
            # US-62 : un identifiant pris par une autre formation ne déplace jamais sa question.
            raise ValueError(f"Identifiant de question déjà utilisé par une autre formation : {data['id']}")
        before = _question_signature(question) if question else None
        question = question or Question(external_id=data["id"])
        question.module = module
        question.qtype = data.get("type", Question.Type.SINGLE)
        question.usage = data.get("usage", Question.Usage.QUIZ)
        for field, value in {**_translated(data, "prompt"), **_translated(data, "explanation")}.items():
            setattr(question, field, value)
        numeric = data.get("numeric") or {}
        question.numeric_value = Decimal(str(numeric["value"])) if "value" in numeric else None
        question.unit = numeric.get("unit", "")
        question.tolerance_pct = Decimal(str(numeric.get("tolerance_pct", 0)))
        # C11 : 1 FCFA d'écart absorbe les arrondis ; un taux ou une durée s'attend exact, sauf mention contraire.
        default_abs = 1 if question.unit == "FCFA" else 0
        question.tolerance_abs = Decimal(str(numeric.get("tolerance_abs", default_abs)))
        question.exercice = data.get("exercice")
        question.params = " ".join(data.get("params", []))
        question.hotspot_svg = _read_inside(folder, data["svg"]) if data.get("svg") else ""
        reviewed = data.get("reviewed") or {}
        question.reviewed_fr = bool(reviewed.get("fr"))
        question.reviewed_en = bool(reviewed.get("en"))
        question.save()
        existing = list(question.choices.all())
        for i, choice_data in enumerate(data.get("choices", [])):
            choice = existing[i] if i < len(existing) else question.choices.model(question=question)
            for field, value in _translated(choice_data, "text").items():
                setattr(choice, field, value)
            choice.is_correct = bool(choice_data.get("correct"))
            choice.shape = choice_data.get("shape")
            choice.order = i
            choice.save()
        for extra in existing[len(data.get("choices", [])):]:
            extra.delete()
        pairs = list(question.pairs.all())
        for i, pair_data in enumerate(data.get("pairs", [])):
            pair = pairs[i] if i < len(pairs) else question.pairs.model(question=question)
            for field, value in {**_translated(pair_data, "left"), **_translated(pair_data, "right")}.items():
                setattr(pair, field, value)
            pair.order = i
            pair.save()
        for extra in pairs[len(data.get("pairs", [])):]:
            extra.delete()
        lines = list(question.journal_lines.all())
        for i, line_data in enumerate(data.get("journal", [])):
            line = lines[i] if i < len(lines) else question.journal_lines.model(question=question)
            line.account, line.side = str(line_data["account"]), line_data["side"]
            line.account_match = str(line_data.get("match", "3"))  # US-34 : 3 chiffres par défaut
            line.amount = Decimal(str(line_data["amount"]))
            for field, value in _translated(line_data, "label").items():
                setattr(line, field, value)
            line.order = i
            line.save()
        for extra in lines[len(data.get("journal", [])):]:
            extra.delete()
        if before is not None and before != _question_signature(question):
            # Un texte modifié doit être relu à nouveau avant d'être servi.
            question.status = Question.Status.DRAFT
            question.save(update_fields=["status"])
        stats["questions"] += 1


@transaction.atomic
def import_formation(manifest_path):
    manifest_path = Path(manifest_path)
    root = manifest_path.parent
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    stats = {"sections": 0, "questions": 0}
    icon = data.get("icon", Formation.Icon.LEDGER)
    if icon not in Formation.Icon.values:
        raise ValueError(f"Icône de formation inconnue : {icon}")  # US-59 : liste fermée
    formation, _ = Formation.objects.update_or_create(
        slug=data["slug"],
        defaults={"is_open": bool(data.get("open")), "icon": icon,
                  **_translated(data, "title"), **_translated(data, "description"),
                  **_translated(data, "legal_reference"), **_translated(data, "prerequisite_note")},
    )
    for partie_data in data.get("parties", []):
        partie, _ = Partie.objects.update_or_create(
            formation=formation, slug=partie_data["slug"],
            defaults={
                "order": partie_data.get("order", 0),
                **_translated(partie_data, "title"),
                **_translated(partie_data, "description"),
            },
        )
        for module_data in partie_data.get("modules", []):
            module, _ = Module.objects.update_or_create(
                partie=partie, order=module_data["order"],
                defaults={
                    "duration_hours": module_data.get("duration_hours", 0),
                    **_translated(module_data, "title"),
                    **_translated(module_data, "competence"),
                    **_translated(module_data, "evaluation_note"),
                },
            )
            module_dir = root / module_data.get("dir", "")
            for section_data in module_data.get("sections", []):
                bodies = {f"body_md_{lang}": _read(module_dir / f"{section_data['file']}.{lang}.md") for lang in LANGS}
                Section.objects.update_or_create(
                    module=module, order=section_data["order"],
                    defaults={"kind": section_data.get("kind", Section.Kind.CONTENT), **_translated(section_data, "title"), **bodies},
                )
                stats["sections"] += 1
            _import_questions(module, module_dir / "questions.json", stats, prefix=data.get("prefix", ""))
    return stats
