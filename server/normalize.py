"""Transformation de la télémétrie brute en état de course exploitable.

Entrée : un snapshot `telemetryCompetitor` (enveloppe avec `Riders[]`).
Sortie : un dict compact { stage, live, kmToFinish, groups[...] } que l'app poll.

Champs par coureur (confirmés depuis la source de racecenter) :
  Bib, kmToFinish, secToFirstRider, kph, kphAvg, Latitude, Longitude
"""
from __future__ import annotations

from datetime import datetime, timezone

from .config import GROUP_GAP_THRESHOLD
from .metadata import Metadata


def _fmt_gap(sec: float) -> str:
    sec = int(round(sec))
    if sec <= 0:
        return "0:00"
    m, s = divmod(sec, 60)
    if m >= 60:
        h, m = divmod(m, 60)
        return f"+{h}:{m:02d}:{s:02d}"
    return f"+{m}:{s:02d}"


def build_groups(riders: list, meta: Metadata, threshold: float = GROUP_GAP_THRESHOLD) -> list:
    """Clusterise les coureurs par `secToFirstRider` en groupes avec écarts."""
    valid = [r for r in riders if r.get("secToFirstRider") is not None]
    valid.sort(key=lambda r: r["secToFirstRider"])

    clusters: list[list] = []
    cur: list = []
    for r in valid:
        if cur and r["secToFirstRider"] - cur[-1]["secToFirstRider"] > threshold:
            clusters.append(cur)
            cur = []
        cur.append(r)
    if cur:
        clusters.append(cur)

    if not clusters:
        return []

    # Le plus gros paquet est étiqueté "Peloton" ; le premier (écart ~0) "Tête".
    biggest = max(range(len(clusters)), key=lambda i: len(clusters[i]))

    groups = []
    for i, cl in enumerate(clusters):
        gap = cl[0]["secToFirstRider"]
        if i == 0 and gap <= threshold:
            label = "Tête"
        elif i == biggest:
            label = "Peloton"
        else:
            label = f"Groupe {i + 1}"

        riders_out = []
        for r in cl:
            info = meta.rider(r.get("Bib"))
            riders_out.append({
                "bib": info["bib"],
                "name": info["name"],
                "team": info.get("team"),
                "kph": r.get("kph"),
            })

        groups.append({
            "label": label,
            "gap": round(gap),
            "gapText": _fmt_gap(gap),
            "count": len(cl),
            "riders": riders_out,
        })
    return groups


def build_race_state(telemetry: dict, meta: Metadata) -> dict:
    riders = telemetry.get("Riders") or []
    live = bool(telemetry.get("RaceStatus"))

    kms = [r["kmToFinish"] for r in riders if r.get("kmToFinish") is not None]
    distance = round(min(kms), 1) if kms else None  # leader = plus petit kmToFinish

    return {
        "stage": telemetry.get("StageIndex"),
        "live": live,
        "updatedAt": datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z"),
        "sourceTimeStamp": telemetry.get("TimeStamp"),
        "kmToFinish": distance,
        "riderCount": len(riders),
        "jerseys": telemetry.get("YGPW"),  # [jaune, vert, pois, blanc]
        "groups": build_groups(riders, meta) if riders else [],
    }
