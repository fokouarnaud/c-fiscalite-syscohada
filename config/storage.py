"""Versionnement des fichiers statiques en développement.

En production, ManifestStaticFilesStorage met l'empreinte du contenu dans le nom du fichier
(app.3f9c1e2a7b.css). En développement, il n'y a pas de collectstatic : on ajoute donc
?v=<empreinte du contenu> à l'URL, pour qu'un CSS ou un JS modifié ne soit jamais servi depuis le cache.
"""
import hashlib
from pathlib import Path

from django.contrib.staticfiles import finders
from django.contrib.staticfiles.storage import StaticFilesStorage

_cache = {}


def _content_version(path):
    found = finders.find(path)
    if not found:
        return None
    file = Path(found)
    key = (str(file), file.stat().st_mtime_ns, file.stat().st_size)
    if key not in _cache:
        _cache[key] = hashlib.sha256(file.read_bytes()).hexdigest()[:10]
    return _cache[key]


class VersionedStaticFilesStorage(StaticFilesStorage):
    def url(self, name):
        url = super().url(name)
        version = _content_version(name)
        return f"{url}?v={version}" if version else url
