"""Génération d'une télémétrie synthétique pour tester hors course.

Reproduit une situation classique : une échappée en tête, le peloton à ~2:15,
un groupe d'attardés à ~8:40. Utilise de vrais dossards pour que les noms se
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


def make_telemetry(meta, step: int = 0) -> dict:
    """Scénario animé : à chaque `step`, la distance baisse et le peloton
    rattrape peu à peu l'échappée (écarts qui évoluent)."""
    bibs = list(meta.riders.keys()) if meta and meta.riders else list(range(1, 200))

    km = round(max(0.5, 45.0 - step * 0.4), 1)   # distance qui descend
    lead = max(0.0, 180.0 - step * 5.0)          # avance de l'échappée qui fond
    chase = lead * 0.35                          # groupe de contre
    dropped = lead + 300.0 + step * 4.0          # attardés qui coulent

    riders = []
    for b in bibs[:3]:                           # échappée (tête)
        riders.append(_rider(b, 0, km))
    for b in bibs[3:9]:                          # contre-attaque (petit groupe)
        riders.append(_rider(b, chase, round(km + 0.3, 1)))
    for b in bibs[9:156]:                        # peloton (gros paquet)
        riders.append(_rider(b, lead, round(km + 0.6, 1)))
    for b in bibs[156:176]:                      # attardés
        riders.append(_rider(b, dropped, round(km + 1.2, 1)))

    return {
        "StageIndex": 5,
        "RaceStatus": True,
        "TimeStamp": 1783527316 + step,
        "YGPW": bibs[:4] if len(bibs) >= 4 else [],
        "Riders": riders,
    }
