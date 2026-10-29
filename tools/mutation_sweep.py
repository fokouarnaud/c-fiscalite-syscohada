"""Balayage de mutations : pour chaque story, casse une règle de production, constate l'échec de ses tests (RED),
restaure le fichier, constate leur succès (GREEN). Une mutation non détectée signale un test manquant.

Usage, depuis la racine du projet : .venv/Scripts/python tools/mutation_sweep.py
"""
import pathlib
import subprocess
import sys

PY = str(pathlib.Path(".venv/Scripts/python.exe").resolve())
MUTATIONS = [
    ("US-01 inscription : compte inactif avant vérification", "accounts/signup.py",
     "    user.is_active = False", "    user.is_active = True", "accounts/tests"),
    ("US-01 inscription : champ piège", "accounts/signup.py",
     'return bool(self.data.get("website"))', "return False", "accounts/tests"),
    ("US-02 connexion : verrouillage après 5 échecs", "accounts/throttling.py",
     ".count() >= settings.LOGIN_MAX_FAILURES", ".count() >= 10**6", "accounts/tests config/tests/test_intrusion.py"),
    ("US-04 rôles : formateur et admin deviennent staff", "accounts/models.py",
     "self.is_staff = self.is_superuser or self.role in (self.Role.TRAINER, self.Role.ADMIN)",
     "self.is_staff = self.is_superuser", "accounts/tests"),
    ("US-13 code de promotion : code inactif refusé", "catalog/services.py",
     "join_code=code, join_code_active=True)", "join_code=code)", "catalog/tests accounts/tests"),
    ("US-14 formation fermée : inscription refusée", "catalog/views.py",
     """    _require_learner(request.user)
    formation = get_object_or_404(Formation, public_id=public_id, is_open=True)""",
     """    _require_learner(request.user)
    formation = get_object_or_404(Formation, public_id=public_id)""", "catalog/tests/test_catalog.py"),
    ("US-10 catalogue : seules les formations ouvertes", "catalog/views.py",
     "for f in Formation.objects.filter(is_open=True)]", "for f in Formation.objects.all()]", "catalog/tests"),
    ("US-31 examen : déblocage après tous les modules", "progress/services.py",
     "return all(module_completed(user, m) for m in partie.modules.all())", "return True",
     "assessments/tests progress/tests courses/tests"),
    ("US-31 examen : 3 tentatives au plus", "assessments/services.py",
     "if assessment.max_attempts is not None and used >= assessment.max_attempts:", "if False:", "assessments/tests"),
    ("US-31 examen : seuil de 70 %", "assessments/models.py",
     "return self.score_pct is not None and self.score_pct >= self.assessment.pass_threshold",
     "return self.score_pct is not None", "assessments/tests certificates/tests"),
    ("US-31 examen : temps écoulé, réponse refusée", "assessments/services.py",
     "if attempt.submitted_at is not None or (attempt.deadline and now >= attempt.deadline):",
     "if attempt.submitted_at is not None:", "assessments/tests"),
    ("US-33 QCM multiple : plancher à zéro", "assessments/scoring.py",
     "return max(Fraction(0), Fraction(good - bad, len(correct_ids)))", "return Fraction(good - bad, len(correct_ids))",
     "assessments/tests"),
    ("US-40 badges : badge de module", "certificates/services.py",
     "Badge.objects.get_or_create(user=user, kind=Badge.Kind.MODULE, module=module)", "pass", "certificates/tests"),
    ("US-41 certificat : le score ne baisse jamais", "certificates/services.py",
     "if best.score_pct > certificate.score_pct:", "if True:", "certificates/tests"),
    ("US-43 PDF : accès réservé", "certificates/views.py",
     "    if user.pk == certificate.user_id or user.is_platform_admin:\n        return True",
     "    return True", "certificates/tests"),
    ("US-42 vérification publique : numéro inconnu = 404", "certificates/views.py",
     'certificate = get_object_or_404(Certificate.objects.select_related("partie__formation"), public_id=public_id)\n'
     '    # US-42 : score',
     'certificate = Certificate.objects.filter(public_id=public_id).first()\n'
     '    # US-42 : score',
     "certificates/tests"),
    ("US-53 export CSV : formules neutralisées", "progress/views.py",
     'FORMULA_PREFIXES = ("=", "+", "-", "@", "\\t", "\\r")', "FORMULA_PREFIXES = ()", "progress/tests"),
    ("US-50 formateur : limité à ses promotions", "progress/views.py",
     "    promotions = Promotion.objects.visible_to(user).select_related(\"formation\")",
     "    promotions = Promotion.objects.all().select_related(\"formation\")", "progress/tests catalog/tests"),
    ("US-63 plan : parent = plus long préfixe existant (caractérisation)", "referentiel/models.py",
     'self.parent = SyscohadaAccount.objects.filter(code__in=prefixes).order_by("-level").first()',
     'self.parent = SyscohadaAccount.objects.filter(code__in=prefixes).order_by("level").first()', "referentiel/tests"),
    ("US-26 formules : arrondi au franc (caractérisation)", "referentiel/calculs.py",
     'return value.quantize(Decimal("1"), rounding=ROUND_HALF_UP)',
     'return value.quantize(Decimal("1"), rounding=ROUND_DOWN)', "referentiel/tests"),
    ("US-01 lien de vérification : jeton contrôlé", "accounts/views.py",
     "if user is None or not email_verification_token.check_token(user, token):", "if user is None:", "accounts/tests"),
    ("US-03 mot de passe oublié : lien valable 24 h", "config/settings.py",
     "PASSWORD_RESET_TIMEOUT = 3600 * 24", "PASSWORD_RESET_TIMEOUT = 3600 * 24 * 365", "accounts/tests"),
    ("US-05 langues : FR et EN", "config/settings.py",
     'LANGUAGES = [("fr", _("Français")), ("en", _("English"))]', 'LANGUAGES = [("fr", _("Français"))]',
     "accounts/tests catalog/tests"),
    ("US-12 inscription libre : source catalogue", "catalog/services.py",
     'defaults={"source": Enrollment.Source.CATALOG}', 'defaults={"source": Enrollment.Source.ADMIN}', "catalog/tests"),
    ("US-22 parcours guidé : première section non lue", "progress/services.py",
     'return {"section": section, "started": bool(viewed)}', 'return {"quiz": True}',
     "progress/tests courses/tests catalog/tests"),
    ("US-54 échéances : marqueur en retard", "progress/services.py",
     "return [d for d in passed if not _deadline_met(user, d.assessment)]", "return []", "progress/tests"),
    ("US-30 quiz corrigé, examen sans correction", "assessments/views.py",
     '"show_correction": not is_exam,', '"show_correction": True,', "assessments/tests"),
    ("US-28 bandeau de traduction", "courses/views.py",
     '"fallback_fr": lang != "fr" and not getattr(section, f"body_md_{lang}", ""),', '"fallback_fr": False,',
     "courses/tests"),
    ("US-55 import CSV : identifiants existants ignorés", "accounts/importing.py",
     "        if User.objects.filter(username=username).exists():", "        if False:", "accounts/tests catalog/tests"),
    ("US-64 sauvegarde quotidienne", "progress/middleware.py",
     "                backup.backup_if_due(settings.BACKUP_DIR)", "                pass", "progress/tests"),
    ("US-52 statistiques par question", "progress/views.py",
     "        scores.setdefault(aq.question, []).append(aq.score(correct, [c.pk for c in aq.selected_choices.all()]))",
     "        pass", "progress/tests catalog/tests"),
    ("US-26 moteur JS : arrondi au franc (caractérisation)", "static/acad/js/calc-core.js",
     "function franc(x) { return Math.floor(x + 0.5 + 1e-9); }", "function franc(x) { return Math.floor(x); }",
     "referentiel/tests/test_calculs_parity.py"),
    ("US-21 lecteur : non-inscrit renvoyé vers le programme", "courses/views.py",
     '    return redirect("formation_detail", public_id=formation.public_id)', "    raise Http404", "courses/tests"),
    ("US-03 mot de passe oublié : compte sans e-mail renvoyé au formateur", "templates/accounts/password_reset_form.html",
     "Demandez un nouveau mot de passe à votre formateur.", "", "accounts/tests"),
    ("US-53 export CSV : BOM pour Excel", "progress/views.py",
     'response.write("﻿")', "pass", "progress/tests"),
    ("US-15 prérequis indicatif affiché sur le programme", "templates/catalog/formation_detail.html",
     "{{ row.formation.prerequisite_note }}</p>", "</p>", "catalog/tests"),
]


def pytest(targets):
    run = subprocess.run([PY, "-m", "pytest", "-p", "no:cacheprovider", "-o", "addopts=", "-q", "--tb=no", *targets.split()],
                         capture_output=True, text=True)
    summary = [line for line in run.stdout.splitlines() if "passed" in line or "failed" in line or "error" in line]
    return run.returncode, (summary[-1] if summary else run.stdout[-200:])


failures = 0
for story, path, old, new, targets in MUTATIONS:
    file = pathlib.Path(path)
    original = file.read_text(encoding="utf-8")
    if original.count(old) != 1:
        print(f"!! {story} : motif introuvable ou ambigu dans {path}")
        failures += 1
        continue
    try:
        file.write_text(original.replace(old, new), encoding="utf-8")
        red, red_summary = pytest(targets)
    finally:
        file.write_text(original, encoding="utf-8")
    green, green_summary = pytest(targets)
    ok = red != 0 and green == 0
    failures += not ok
    print(f"{'OK ' if ok else 'KO '} {story}\n     RED   : {red_summary}\n     GREEN : {green_summary}")
print("\nmutations non détectées ou en erreur :", failures)
sys.exit(1 if failures else 0)
