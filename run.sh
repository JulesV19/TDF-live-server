#!/usr/bin/env bash
# Lance le serveur en gardant le Mac éveillé pendant l'étape (caffeinate).
# Usage : ./run.sh            (poll réel)
#         ./run.sh --mock     (test hors course)
set -euo pipefail
cd "$(dirname "$0")"

PY=.venv/bin/python
[ -x "$PY" ] || PY=python3

exec caffeinate -dimsu "$PY" -m server.run "$@"
