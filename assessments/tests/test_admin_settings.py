import pytest

from accounts.models import User
from assessments.models import Assessment


@pytest.mark.django_db
def test_admin_can_change_exam_settings(client, partie):
    exam = Assessment.exam_for(partie)
    client.force_login(User.objects.create_user(username="chef", password="x-Secret-123", role=User.Role.ADMIN))
    response = client.post(f"/fr/admin/assessments/assessment/{exam.pk}/change/", {
        "kind": "part_exam", "partie": partie.pk, "pass_threshold": 80, "max_attempts": 2,
        "duration_minutes": 45, "questions_per_module": 5, "shuffle": "on",
    })
    assert response.status_code == 302
    exam.refresh_from_db()
    assert (exam.pass_threshold, exam.max_attempts, exam.duration_minutes, exam.questions_per_module) == (80, 2, 45, 5)


@pytest.mark.django_db
def test_trainer_cannot_change_exam_settings(client, partie):
    exam = Assessment.exam_for(partie)
    client.force_login(User.objects.create_user(username="macaire", password="x-Secret-123", role=User.Role.TRAINER))
    assert client.get(f"/fr/admin/assessments/assessment/{exam.pk}/change/").status_code == 403
