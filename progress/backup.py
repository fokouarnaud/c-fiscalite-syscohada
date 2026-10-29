"""Sauvegarde quotidienne déclenchée par les requêtes (US-20).

Le plan gratuit de PythonAnywhere n'offre pas de tâche planifiée : la première requête
qui suit les 24 h écoulées depuis la dernière copie lance `backup_db`.
"""
import time
from pathlib import Path

from django.core.management import call_command

INTERVAL = 24 * 3600

_last_backup = None  # heure de la dernière copie connue de ce processus (évite de relire le dossier)


def reset():
    global _last_backup
    _last_backup = None


def _latest_backup_time(directory):
    times = [p.stat().st_mtime for p in Path(directory).glob("db-*.sqlite3")]
    return max(times, default=0.0)


def backup_if_due(directory):
    """Sauvegarde la base si la dernière copie a plus de 24 h ; renvoie True si une copie a été faite."""
    global _last_backup
    now = time.time()
    if _last_backup is not None and now - _last_backup < INTERVAL:
        return False
    _last_backup = _latest_backup_time(directory)
    if now - _last_backup < INTERVAL:
        return False
    call_command("backup_db", str(directory), verbosity=0)
    _last_backup = now
    return True
