"""Sauvegarde quotidienne déclenchée par l'application (le plan gratuit n'a pas de tâche planifiée)."""
import os
import time

import pytest
from django.test import RequestFactory, override_settings

from progress import backup
from progress.middleware import DailyBackupMiddleware

DAY = 24 * 3600


@pytest.fixture(autouse=True)
def fresh_process_memory():
    backup.reset()
    yield
    backup.reset()


def backups_in(directory):
    return sorted(directory.glob("db-*.sqlite3"))


def age(path, seconds):
    then = time.time() - seconds
    os.utime(path, (then, then))


@pytest.mark.django_db(transaction=True)
def test_first_call_creates_a_backup_when_none_exists(tmp_path):
    assert backup.backup_if_due(tmp_path) is True
    assert len(backups_in(tmp_path)) == 1


@pytest.mark.django_db(transaction=True)
def test_no_new_backup_while_the_last_one_is_less_than_a_day_old(tmp_path):
    recent = tmp_path / "db-20261017-080000.sqlite3"
    recent.write_bytes(b"x")
    age(recent, DAY - 60)
    assert backup.backup_if_due(tmp_path) is False
    assert backups_in(tmp_path) == [recent]


@pytest.mark.django_db(transaction=True)
def test_new_backup_when_the_last_one_is_older_than_a_day(tmp_path):
    old = tmp_path / "db-20261015-080000.sqlite3"
    old.write_bytes(b"x")
    age(old, DAY + 60)
    assert backup.backup_if_due(tmp_path) is True
    [new] = backups_in(tmp_path)
    assert new != old


@pytest.mark.django_db(transaction=True)
def test_the_directory_is_not_reread_on_every_request(tmp_path, monkeypatch):
    backup.backup_if_due(tmp_path)
    monkeypatch.setattr(backup, "_latest_backup_time", lambda d: pytest.fail("relu"))
    assert backup.backup_if_due(tmp_path) is False


def call_middleware(view=lambda request: "réponse"):
    return DailyBackupMiddleware(view)(RequestFactory().get("/fr/"))


@pytest.mark.django_db(transaction=True)
def test_middleware_backs_up_into_the_configured_directory(tmp_path):
    with override_settings(BACKUP_DIR=str(tmp_path)):
        assert call_middleware() == "réponse"
    assert len(backups_in(tmp_path)) == 1


def test_middleware_does_nothing_without_a_backup_directory(monkeypatch):
    monkeypatch.setattr(backup, "backup_if_due", lambda d: pytest.fail("appelé"))
    with override_settings(BACKUP_DIR=""):
        assert call_middleware() == "réponse"


def test_a_failed_backup_never_breaks_the_page(tmp_path, monkeypatch):
    def boom(directory):
        raise OSError("disque plein")

    monkeypatch.setattr(backup, "backup_if_due", boom)
    with override_settings(BACKUP_DIR=str(tmp_path)):
        assert call_middleware() == "réponse"
