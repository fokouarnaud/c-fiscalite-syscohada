import os

from config.env import load_env_file


def test_env_file_values_are_loaded(tmp_path, monkeypatch):
    monkeypatch.delenv("ACAD_TEST_KEY", raising=False)
    env = tmp_path / ".env"
    env.write_text("# commentaire\nACAD_TEST_KEY=valeur=avec=egal\n\nACAD_TEST_QUOTED=\"entre guillemets\"\n", encoding="utf-8")
    load_env_file(env)
    assert os.environ["ACAD_TEST_KEY"] == "valeur=avec=egal"
    assert os.environ["ACAD_TEST_QUOTED"] == "entre guillemets"


def test_existing_environment_variables_win(tmp_path, monkeypatch):
    monkeypatch.setenv("ACAD_TEST_KEY", "deja-defini")
    env = tmp_path / ".env"
    env.write_text("ACAD_TEST_KEY=du-fichier\n", encoding="utf-8")
    load_env_file(env)
    assert os.environ["ACAD_TEST_KEY"] == "deja-defini"


def test_missing_env_file_is_ignored(tmp_path):
    load_env_file(tmp_path / "absent.env")  # ne doit pas lever d'erreur
