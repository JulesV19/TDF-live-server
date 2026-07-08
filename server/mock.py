"""Génération d'une télémétrie synthétique pour tester hors course.

Reproduit une situation resserrée : une échappée en tête, un groupe de contre,
puis le peloton — des écarts homogènes qui se réduisent peu à peu (pas de groupe
largué très loin derrière). Utilise de vrais dossards pour que les noms se
résolvent via les métadonnées.
"""
from __future__ import annotations


def _rider(bib: int, sec: float, km: float) -> dict:
    return {
        "Bib": bib,
        "kmToFinish": km,
        "secToFirstRider": round(sec),
        "kph": 42.0,
        "kphAvg": 41.0,
        "Latitude": 43.0,
        "Longitude": 1.0,
    }


def make_offrace() -> dict:
    """Télémétrie 'hors course' : aucune étape en direct (comme l'API letour
    hors épreuve — RaceStatus faux, Riders vide). Sert à tester le message
    'pas d'étape en cours' côté app."""
    return {
        "StageIndex": None,
        "RaceStatus": False,
        "TimeStamp": 0,
        "YGPW": [],
        "Riders": [],
    }


def make_telemetry(meta, step: int = 0) -> dict:
    """Scénario animé : à chaque `step`, la distance baisse et le peloton
    rattrape peu à peu l'échappée (écarts qui évoluent)."""
    bibs = list(meta.riders.keys()) if meta and meta.riders else list(range(1, 200))

    km = round(max(0.5, 45.0 - step * 0.4), 1)   # distance qui descend
    lead = max(0.0, 120.0 - step * 3.0)          # avance de l'échappée qui fond
    chase = lead * 0.45                          # groupe de contre, à mi-chemin

    riders = []
    for b in bibs[:3]:                           # échappée (tête)
        riders.append(_rider(b, 0, km))
    for b in bibs[3:9]:                          # contre-attaque (petit groupe)
        riders.append(_rider(b, chase, round(km + 0.3, 1)))
    for b in bibs[9:176]:                        # peloton (tout le reste, groupé)
        riders.append(_rider(b, lead, round(km + 0.6, 1)))

    return {
        "StageIndex": 5,
        "RaceStatus": True,
        "TimeStamp": 1783527316 + step,
        "YGPW": bibs[:4] if len(bibs) >= 4 else [],
        "Riders": riders,
    }
