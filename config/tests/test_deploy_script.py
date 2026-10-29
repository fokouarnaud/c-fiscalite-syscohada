"""US-74 : deploy.sh charge les référentiels (plan SYSCOHADA, taux du CGI) avant le contenu, sur le compte comptafisca.

Le script est lancé dans un bac à sable : git, python et pip y sont des doubles qui journalisent leurs arguments.
"""
import os
import shutil
import subprocess

import pytest
from django.conf import settings

BASH = shutil.which("bash")
FAKE = '#!/usr/bin/env bash\necho "{name} $*" >> "$DEPLOY_LOG"\n'


@pytest.fixture
def sandbox(tmp_path):
    shutil.copy(settings.BASE_DIR / "deploy.sh", tmp_path / "deploy.sh")
    (tmp_path / "content" / "compta").mkdir(parents=True)
    (tmp_path / "content" / "compta" / "formation.json").write_text("{}", encoding="utf-8")
    bin_dir, venv_bin = tmp_path / "fakebin", tmp_path / "venv" / "bin"
    bin_dir.mkdir()
    venv_bin.mkdir(parents=True)
    for folder, name in ((bin_dir, "git"), (venv_bin, "python"), (venv_bin, "pip")):
        (folder / name).write_text(FAKE.format(name=name), encoding="utf-8", newline="\n")
        (folder / name).chmod(0o755)
    return tmp_path


@pytest.mark.skipif(BASH is None, reason="bash absent")
def test_deploy_loads_the_chart_of_accounts_and_the_rates_before_the_content(sandbox):
    log = sandbox / "deploy.log"
    env = {**os.environ, "DEPLOY_LOG": str(log), "VENV": str(sandbox / "venv"), "WSGI_FILE": str(sandbox / "wsgi.py"),
           "PATH": f"{sandbox / 'fakebin'}{os.pathsep}{os.environ['PATH']}"}

    subprocess.run([BASH, "deploy.sh"], cwd=sandbox, env=env, check=True, capture_output=True)

    commands = [line.split()[2] for line in log.read_text(encoding="utf-8").splitlines() if line.startswith("python manage.py")]
    assert commands == ["migrate", "import_syscohada", "import_parameters", "import_content", "publish_reviewed",
                        "collectstatic", "check"]
    assert "python manage.py import_syscohada content/referentiel/syscohada.csv" in log.read_text(encoding="utf-8")
    assert "python manage.py import_parameters content/referentiel/parametres.csv" in log.read_text(encoding="utf-8")
    assert (sandbox / "wsgi.py").exists()  # application rechargée
