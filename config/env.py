"""Lecture minimale d'un fichier .env (KEY=VALUE), sans dépendance externe.

Les variables déjà présentes dans l'environnement ne sont jamais écrasées.
"""
import os
from pathlib import Path


def load_env_file(path):
    path = Path(path)
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        os.environ.setdefault(key.strip(), value)
