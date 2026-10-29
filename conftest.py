import pytest

from accounts.models import User
from courses.models import Formation, Module, Partie


def enroll(user, promotion):
    """Inscrit un utilisateur dans une promotion (et donc dans sa formation)."""
    from catalog.models import Enrollment

    Enrollment.objects.create(user=user, formation=promotion.formation, promotion=promotion)
    return user


@pytest.fixture(autouse=True)
def fast_password_hashing(settings):
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]


@pytest.fixture(autouse=True)
def default_language_after_each_test(settings):
    """Une requête en /en/ active l'anglais dans le fil d'exécution : on rend le français au test suivant."""
    from django.utils import translation

    yield
    translation.activate(settings.LANGUAGE_CODE)


@pytest.fixture
def partie(db):
    formation = Formation.objects.create(title_fr="Comptabilité SYSCOHADA", slug="compta")
    return Partie.objects.create(formation=formation, title_fr="Habilitation et sécurité", order=1, slug="p1")


@pytest.fixture
def module(partie):
    return Module.objects.create(partie=partie, title_fr="Sécurité dans les travaux", order=1, duration_hours=8)


@pytest.fixture
def learner(db):
    return User.objects.create_user(username="awa", password="x-Secret-123")


def make_question(module, usage="quiz", qtype="single", choices=((True, "Bon"), (False, "Faux")), publish=True):
    from assessments.models import Question

    q = Question.objects.create(
        module=module, qtype=qtype, usage=usage, prompt_fr="Q ?", prompt_en="Q?",
        explanation_fr="Parce que.", reviewed_fr=True, reviewed_en=True,
    )
    for i, (ok, text) in enumerate(choices):
        q.choices.create(text_fr=text, text_en=text, is_correct=ok, order=i)
    if publish:
        q.publish()
    return q


@pytest.fixture
def question_factory():
    return make_question


@pytest.fixture
def promotion(partie):
    from accounts.models import Promotion

    return Promotion.objects.create(name="Oct 2026", formation=partie.formation)


@pytest.fixture
def enrolled(learner, promotion):
    return enroll(learner, promotion)
