#!/usr/bin/env bash
# Lance le serveur en gardant le Mac éveillé pendant l'étape (caffeinate).
# Usage : ./run.sh            (poll réel)
#         ./run.sh --mock     (test hors course)
set -euo pipefail
cd "$(dirname "$0")"

# Charge les variables d'env (URL/token de publication…) depuis .env s'il existe.
[ -f .env ] && set -a && . ./.env && set +a

PY=.venv/bin/python
[ -x "$PY" ] || PY=python3

exec caffeinate -dimsu "$PY" -m server.run "$@"
