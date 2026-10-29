import json
import os
import subprocess
import sys

import pytest
from django.conf import settings

from config.storage import VersionedStaticFilesStorage


@pytest.fixture
def static_dir(tmp_path, settings):
    src = tmp_path / "src"
    (src / "acad").mkdir(parents=True)
    settings.STATICFILES_DIRS = [src]
    return src


def test_dev_static_url_carries_a_content_version(static_dir):
    (static_dir / "acad" / "app.css").write_text("body { color: red; }", encoding="utf-8")
    url = VersionedStaticFilesStorage().url("acad/app.css")
    assert url.startswith("/static/acad/app.css?v=")
    assert len(url.split("?v=")[1]) == 10


def test_dev_static_version_changes_when_the_file_changes(static_dir):
    css = static_dir / "acad" / "app.css"
    css.write_text("body { color: red; }", encoding="utf-8")
    before = VersionedStaticFilesStorage().url("acad/app.css")
    css.write_text("body { color: blue; }", encoding="utf-8")
    os.utime(css, (css.stat().st_atime, css.stat().st_mtime + 5))
    after = VersionedStaticFilesStorage().url("acad/app.css")
    assert before != after


def test_unknown_static_file_gets_a_plain_url(static_dir):
    assert VersionedStaticFilesStorage().url("acad/missing.js") == "/static/acad/missing.js"


@pytest.mark.django_db
def test_pages_reference_versioned_css_and_js(client):
    html = client.get("/fr/connexion/").content.decode()
    assert "/static/acad/css/app.css?v=" in html


def test_production_collectstatic_hashes_css_and_js_file_names(tmp_path):
    env = {**os.environ, "DJANGO_DEBUG": "0", "DJANGO_SECRET_KEY": "x7#Kq!p2@Zr9$wM4%" * 4, "DJANGO_STATIC_ROOT": str(tmp_path)}
    subprocess.run([sys.executable, "manage.py", "collectstatic", "--noinput", "-v0"], cwd=settings.BASE_DIR, env=env, check=True)
    paths = json.loads((tmp_path / "staticfiles.json").read_text())["paths"]
    for name in ("acad/css/app.css", "acad/js/attempt.js", "vendor/htmx.min.js"):
        hashed = paths[name]
        assert hashed != name and hashed.rsplit(".", 2)[1].isalnum()
        assert (tmp_path / hashed).exists()
