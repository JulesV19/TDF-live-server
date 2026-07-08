# TDF Live — serveur

Petit serveur qui récupère la télémétrie live du Tour de France depuis l'API publique
`racecenter.letour.fr`, calcule la distance restante et regroupe les coureurs par écart, puis
expose le résultat en HTTP pour l'app et le widget iOS.

> L'app / le widget iOS vivent dans un [dépôt séparé](https://github.com/JulesV19/TDF-live-widget).

## Mise en route

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python -m server.run           # poll réel de l'API letour
python -m server.run --mock    # télémétrie synthétique (test hors course)
python -m server.run --port 9000
```

Ou via le script, qui garde le Mac éveillé pendant l'étape (`caffeinate`) :

```sh
./run.sh            # poll réel
./run.sh --mock     # test hors course
```

## API HTTP

| Méthode | Route            | Description                                         |
|---------|------------------|-----------------------------------------------------|
| `GET`   | `/race/current`  | État de course courant (distance, groupes, écarts). |
| `GET`   | `/health`        | Sonde : `{ ok, riders, mock }`.                     |

L'app fait du polling sur `/race/current`. Le serveur écoute sur `0.0.0.0:8000` par défaut
(joignable via Tailscale).

## Fonctionnement

Un seul process (`server.run`) lance l'API FastAPI/uvicorn et, en tâche de fond, une boucle de
poll :

- au démarrage, chargement des métadonnées (coureurs, équipes, étapes) ;
- poll de la télémétrie toutes les **60 s** en course, **300 s** hors course (cadence sobre pour
  ne pas se faire rate-limiter) ;
- chaque snapshot est normalisé : distance restante + regroupement des coureurs (nouveau groupe
  dès que l'écart au coureur précédent dépasse le seuil) ;
- le dernier état est gardé en mémoire et servi tel quel sur `/race/current`.

## Configuration

Tout est surchargeable par variable d'environnement (voir [server/config.py](server/config.py)) :

| Variable              | Défaut  | Rôle                                          |
|-----------------------|---------|-----------------------------------------------|
| `TDF_YEAR`            | `2026`  | Année de l'édition (construit les URLs API).  |
| `TDF_HOST`            | `0.0.0.0` | Interface d'écoute.                         |
| `TDF_PORT`            | `8000`  | Port HTTP.                                     |
| `TDF_POLL_LIVE`       | `60`    | Intervalle de poll en course (s).             |
| `TDF_POLL_IDLE`       | `300`   | Intervalle de poll hors course (s).           |
| `TDF_GROUP_THRESHOLD` | `5`     | Seuil d'écart (s) créant un nouveau groupe.   |
| `TDF_MOCK`            | —       | `1` → télémétrie synthétique, aucun appel API.|

## Structure

```
server/
  run.py        point d'entrée (API + boucle de poll)
  api.py        endpoints FastAPI, cycle de vie
  config.py     configuration (env-overridable)
  feed.py       boucles de poll réel / mock
  metadata.py   chargement coureurs / équipes / étapes
  normalize.py  distance restante + regroupement par écart
  mock.py       génération de télémétrie synthétique
  state.py      dernier état en mémoire
```

## Dépendances

`httpx`, `fastapi`, `uvicorn` — voir [requirements.txt](requirements.txt).
