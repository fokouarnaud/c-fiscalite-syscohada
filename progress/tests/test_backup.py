import sqlite3

import pytest
from django.core.management import call_command


@pytest.mark.django_db(transaction=True)
def test_backup_writes_a_readable_copy_of_the_database(tmp_path, django_user_model):
    django_user_model.objects.create_user(username="awa", password="x-Secret-123")
    call_command("backup_db", str(tmp_path), verbosity=0)
    [backup] = tmp_path.glob("db-*.sqlite3")
    with sqlite3.connect(backup) as conn:
        assert conn.execute("select username from accounts_user").fetchall() == [("awa",)]


@pytest.mark.django_db(transaction=True)
def test_backup_keeps_only_the_new_copy(tmp_path):
    for i in range(3):
        old = tmp_path / f"db-2026010{i}-000000.sqlite3"
        old.write_bytes(b"old")
    call_command("backup_db", str(tmp_path), verbosity=0)
    [kept] = tmp_path.glob("db-*.sqlite3")
    assert kept.read_bytes() != b"old"  # la nouvelle copie remplace les anciennes


@pytest.mark.django_db(transaction=True)
def test_a_failed_backup_keeps_the_previous_copy(tmp_path, monkeypatch):
    previous = tmp_path / "db-20260101-000000.sqlite3"
    previous.write_bytes(b"old")

    def boom(*args, **kwargs):
        raise OSError("disque plein")

    monkeypatch.setattr("progress.management.commands.backup_db.sqlite3.connect", boom)
    with pytest.raises(OSError):
        call_command("backup_db", str(tmp_path), verbosity=0)
    assert previous.read_bytes() == b"old"
