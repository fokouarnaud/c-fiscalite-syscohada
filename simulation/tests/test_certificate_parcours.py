"""US-94 : le certificat d'un parcours de la simulation nomme la formation et le parcours, sur la page publique de
vérification comme dans le PDF (le parcours est le titre de sa partie, S11)."""
import pytest
from django.utils import timezone

from assessments.models import Assessment, Attempt
from certificates.models import Certificate
from courses.models import Formation, Partie


@pytest.fixture
def parcours_certificate(learner):
    formation = Formation.objects.create(title_fr="Simulation Compta et Fisca", slug="simulation", icon="briefcase")
    partie = Partie.objects.create(formation=formation, slug="a", order=1,
                                   title_fr="Parcours A : boutique de vêtements (Ngono Mode SARL)")
    exam = Assessment.exam_for(partie)
    attempt = Attempt.objects.create(user=learner, assessment=exam, number=1, score_pct=82,
                                     started_at=timezone.now(), submitted_at=timezone.now())
    return Certificate.objects.create(user=learner, partie=partie, attempt=attempt, holder_name="Brice Mvondo",
                                      score_pct=82)


@pytest.mark.django_db
def test_the_public_verification_names_the_parcours(client, parcours_certificate):
    html = client.get(f"/fr/verify/{parcours_certificate.public_id}/").content.decode()

    assert "Simulation Compta et Fisca" in html
    assert "Parcours A : boutique de vêtements (Ngono Mode SARL)" in html


@pytest.mark.django_db
def test_the_pdf_names_the_formation_and_the_parcours(client, parcours_certificate):
    client.force_login(parcours_certificate.user)

    pdf = client.get(f"/fr/certificats/{parcours_certificate.public_id}/pdf/").content

    assert b"Simulation Compta et Fisca : Parcours A" in pdf
