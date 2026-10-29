"""US-74, US-75, US-76, US-80 et US-81 (formation `fisca`) : règles backend vérifiées sur des données de la forme de
`fisca`, avant le contenu réel (livraisons 2 à 5), dont les garde-fous sont dans test_content_files.py."""
import io
import json
from fractions import Fraction

import pytest
from django.core.management import call_command

from accounts.models import Promotion, User
from assessments.models import Assessment, Question
from assessments.services import save_answer, start_attempt
from catalog.models import Enrollment
from courses.models import Formation, Module, Partie, Section

PARTS = (
    ("p1", "Sécurité, schémas et distribution", ("La sécurité électrique", "Lire les schémas", "Transformateurs et distribution")),
    ("p2", "Les fisca électriques", ("Appareils de commande et capteurs", "Fisca à courant continu", "Fisca à courant alternatif")),
    ("p3", "Contacteurs, relais et circuits de commande", ("Contacteurs et démarreurs", "Relais et temporisations", "Circuits de commande")),
    ("p4", "Comptabilité SYSCOHADA de puissance, variateurs et automates", ("Comptabilité SYSCOHADA de puissance", "Variateurs de vitesse", "Automates programmables")),
)
LOCKOUT = ("Prévenir", "Séparer", "Condamner", "Identifier", "Vérifier l'absence de tension", "Mettre à la terre")
RANKS = ("1re", "2e", "3e", "4e", "5e", "6e")


@pytest.fixture
def fisca(db):
    formation = Formation.objects.create(title_fr="Fiscalité CGI Cameroun", slug="fisca", order=2, is_open=True, icon="receipt")
    for order, (slug, title, modules) in enumerate(PARTS, start=1):
        partie = Partie.objects.create(formation=formation, title_fr=title, order=order, slug=slug)
        for rank, module_title in enumerate(modules, start=1):
            Module.objects.create(partie=partie, title_fr=module_title, order=rank, duration_hours=8)
    return formation


@pytest.fixture
def m1(fisca):
    return Module.objects.get(partie__formation=fisca, title_fr="La sécurité électrique")


@pytest.fixture
def fisca_learner(fisca):
    user = User.objects.create_user(username="ebode", password="x-Secret-123")
    Enrollment.objects.create(user=user, formation=fisca, source=Enrollment.Source.CATALOG)
    return user


def published(module, qtype, **fields):
    q = Question.objects.create(module=module, qtype=qtype, prompt_fr="Q ?", prompt_en="Q?", reviewed_fr=True, reviewed_en=True, **fields)
    return q


# --- US-75 : une séquence posée en appariement étape → rang ----------------------------------------------------------


@pytest.fixture
def lockout_sequence(m1):
    q = published(m1, "matching")
    for i, (step, rank) in enumerate(zip(LOCKOUT, RANKS)):
        q.pairs.create(left_fr=step, left_en=step, right_fr=rank, right_en=rank, order=i)
    q.publish()
    return q


def test_a_sequence_scores_the_share_of_steps_put_at_their_rank(fisca_learner, m1, lockout_sequence):
    pairs = {p.left_fr: str(p.public_id) for p in lockout_sequence.pairs.all()}
    attempt = start_attempt(fisca_learner, Assessment.quiz_for(m1))
    answer = {pairs[step]: pairs[step] for step in LOCKOUT}
    answer[pairs["Séparer"]], answer[pairs["Condamner"]] = pairs["Condamner"], pairs["Séparer"]  # deux étapes inversées

    save_answer(attempt, lockout_sequence.public_id, [], pairs=answer)

    aq = attempt.attempt_questions.get()
    assert aq.score([], []) == Fraction(4, 6)


# --- US-76 : question sur schéma, tout ou rien ----------------------------------------------------------------------

SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 100"><rect width="200" height="100"/></svg>'


@pytest.fixture
def isolator_hotspot(m1):
    q = published(m1, "hotspot", hotspot_svg=SVG)
    q.choices.create(text_fr="Sectionneur", text_en="Isolator", is_correct=True, shape={"x": 10, "y": 10, "w": 30, "h": 30}, order=0)
    q.choices.create(text_fr="Contacteur", text_en="Contactor", shape={"x": 80, "y": 10, "w": 30, "h": 30}, order=1)
    q.choices.create(text_fr="Relais thermique", text_en="Overload relay", shape={"x": 150, "y": 10, "w": 30, "h": 30}, order=2)
    q.publish()
    return q


@pytest.mark.parametrize("clicked, score", [("Sectionneur", 1), ("Contacteur", 0), ("Relais thermique", 0)])
def test_clicking_the_device_to_padlock_is_all_or_nothing(fisca_learner, m1, isolator_hotspot, clicked, score):
    attempt = start_attempt(fisca_learner, Assessment.quiz_for(m1))
    choice = isolator_hotspot.choices.get(text_fr=clicked)

    save_answer(attempt, isolator_hotspot.public_id, [choice.public_id])

    aq = attempt.attempt_questions.get()
    correct = list(isolator_hotspot.choices.filter(is_correct=True).values_list("pk", flat=True))
    assert aq.score(correct, list(aq.selected_choices.values_list("pk", flat=True))) == score


# --- US-74 : le mini-projet s'ouvre sur la consigne de sécurité -----------------------------------------------------


def test_the_mini_project_page_shows_the_safety_rule_before_both_variants(client, fisca_learner, m1):
    body = ("## Sécurité\n\nTout se câble en 24 V, alimenté par un adaptateur mural.\n\n"
            "## Variante oscilloscope\n\nObservez la tension.\n\n## Variante multimètre seul\n\nMesurez la tension.")
    practical = Section.objects.create(module=m1, title_fr="Mini-projet", order=7, kind=Section.Kind.PRACTICAL, body_md_fr=body)
    client.force_login(fisca_learner)

    html = client.get(f"/fr/sections/{practical.public_id}/").content.decode()

    assert 0 < html.index("Sécurité</h2>") < html.index("Variante oscilloscope</h2>") < html.index("Variante multimètre seul</h2>")
    assert "24 V" in html


# --- US-80 : les 81 questions relues d'une partie sont publiées au déploiement ---------------------------------------


def question(qid, section, usage, reviewed=True):
    return {
        "id": qid, "type": "single", "usage": usage, "section": section,
        "prompt": {"fr": "Q ?", "en": "Q?"}, "explanation": {"fr": "Parce que.", "en": "Because."},
        "reviewed": {"fr": reviewed, "en": reviewed},
        "choices": [{"text": {"fr": "Oui", "en": "Yes"}, "correct": True}, {"text": {"fr": "Non", "en": "No"}, "correct": False}],
    }


@pytest.fixture
def fisca_p1_dir(tmp_path):
    """Partie 1 de `fisca` rédigée : trois modules de 15 questions de quiz et 12 d'examen, relues (E39)."""
    modules = []
    for n, title in enumerate(PARTS[0][2], start=1):
        folder = tmp_path / "p1" / f"m{n}"
        folder.mkdir(parents=True)
        (folder / "01-intro.fr.md").write_text("Texte.", encoding="utf-8")
        (folder / "01-intro.en.md").write_text("Text.", encoding="utf-8")
        questions = [question(f"m-p1-m{n}-q{i:02d}", "01-intro", "quiz" if i <= 15 else "exam") for i in range(1, 28)]
        (folder / "questions.json").write_text(json.dumps(questions), encoding="utf-8")
        modules.append({"order": n, "dir": f"p1/m{n}", "duration_hours": 8, "title": {"fr": title, "en": title},
                        "sections": [{"order": 1, "file": "01-intro", "title": {"fr": "Intro", "en": "Intro"}}]})
    manifest = {"slug": "fisca", "icon": "receipt", "open": False,
                "title": {"fr": "Fiscalité CGI Cameroun", "en": "Electric motors and control"},
                "parties": [{"slug": "p1", "order": 1, "title": {"fr": PARTS[0][1], "en": "Safety, diagrams and distribution"},
                             "modules": modules}]}
    (tmp_path / "formation.json").write_text(json.dumps(manifest), encoding="utf-8")
    return tmp_path


@pytest.mark.django_db
def test_publish_reviewed_publishes_the_81_reviewed_questions_of_a_fisca_part(fisca_p1_dir):
    call_command("import_content", str(fisca_p1_dir / "formation.json"), verbosity=0)
    out = io.StringIO()

    call_command("publish_reviewed", stdout=out)

    published_questions = Question.objects.published().filter(module__partie__formation__slug="fisca")
    assert published_questions.count() == 81
    assert published_questions.filter(usage="exam").count() == 36
    assert "fisca : 81 question(s) publiée(s)." in out.getvalue().splitlines()


@pytest.mark.django_db
def test_an_unreviewed_fisca_question_stays_a_draft(fisca_p1_dir):
    path = fisca_p1_dir / "p1" / "m1" / "questions.json"
    questions = json.loads(path.read_text(encoding="utf-8"))
    questions[0]["reviewed"] = {"fr": True, "en": False}
    path.write_text(json.dumps(questions), encoding="utf-8")
    call_command("import_content", str(fisca_p1_dir / "formation.json"), verbosity=0)

    call_command("publish_reviewed", stdout=io.StringIO())

    assert Question.objects.get(external_id="m-p1-m1-q01").status == "draft"
    assert Question.objects.published().count() == 80


# --- US-81 : l'espace formateur couvre les 12 modules et les 4 examens, sans code propre à `fisca` -----------------


@pytest.fixture
def fisca_trainer(fisca, fisca_learner):
    trainer = User.objects.create_user(username="ngono", password="x-Secret-123", role=User.Role.TRAINER)
    promotion = Promotion.objects.create(name="Électrotechnique 2026", formation=fisca)
    promotion.trainers.add(trainer)
    Enrollment.objects.filter(user=fisca_learner).update(promotion=promotion)
    return trainer


def test_trainer_table_lists_the_twelve_modules_and_four_part_exams(client, fisca_trainer):
    client.force_login(fisca_trainer)

    response = client.get("/fr/formateur/")

    [table] = response.context["tables"]
    assert [m.title for m in table["modules"]] == [title for _, _, modules in PARTS for title in modules]
    html = response.content.decode()
    assert all(f">Examen P{n}</th>" in html for n in (1, 2, 3, 4))
    assert "P4 : Comptabilité SYSCOHADA de puissance, variateurs et automates" in html
    assert "M12 : Automates programmables" in html


def test_deadline_page_offers_the_twelve_quizzes_and_four_exams(client, fisca_trainer):
    client.force_login(fisca_trainer)

    [target] = client.get("/fr/formateur/echeances/").context["targets"]

    modules = list(target["modules"])
    assert len(modules) == 12 and modules[-1].title == "Automates programmables"
    assert [p.slug for p in target["parties"]] == ["p1", "p2", "p3", "p4"]


def test_csv_export_has_a_column_per_fisca_module_and_part_exam(client, fisca_trainer, fisca_learner):
    client.force_login(fisca_trainer)

    header, *rows = client.get("/fr/formateur/export.csv").content.decode("utf-8-sig").splitlines()

    assert header.count(";") == 2 + 12 + 2 * 4
    assert any(fisca_learner.username in row for row in rows)
