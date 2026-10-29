#!/usr/bin/env bash
# Mise à jour de ComptaFisca Acad Ventisax sur PythonAnywhere : bash ~/comptafiscaventisax/deploy.sh
set -euo pipefail
cd "$(dirname "$0")"
VENV="${VENV:-$HOME/.virtualenvs/comptafisca}"
PY="$VENV/bin/python"

git pull --ff-only
"$VENV/bin/pip" install --quiet -r requirements.txt
"$PY" manage.py migrate --noinput
# Référentiels d'abord (US-74) : le contenu cite des comptes SYSCOHADA et des taux du CGI.
"$PY" manage.py import_syscohada content/referentiel/syscohada.csv
"$PY" manage.py import_parameters content/referentiel/parametres.csv
# Toutes les formations du dépôt (content/<slug>/formation.json), par ordre alphabétique.
"$PY" manage.py import_content content/*/formation.json
# Publie les questions relues en FR et en EN (drapeaux « reviewed » du contenu versionné) ; les autres restent en brouillon.
"$PY" manage.py publish_reviewed
"$PY" manage.py collectstatic --noinput --verbosity 0
"$PY" manage.py check --deploy --fail-level ERROR
# Recharge l'application web (le fichier WSGI de PythonAnywhere).
touch "${WSGI_FILE:-/var/www/${PA_DOMAIN:-comptafiscaventisax_pythonanywhere_com}_wsgi.py}"
echo "Déploiement terminé."
