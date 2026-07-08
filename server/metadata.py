"""Chargement des métadonnées statiques : coureurs, équipes, étapes.

Ces trois endpoints sont des snapshots qui changent rarement : on les charge
au démarrage (et on peut rafraîchir 1x/jour). Ils servent à enrichir la
télémétrie (qui ne contient que des dossards) avec noms et équipes.
"""
from __future__ import annotations

from datetime import datetime, timezone

import httpx

from .config import COMPETITORS_URL, STAGE_URL, TEAM_URL, USER_AGENT

HEADERS = {"User-Agent": USER_AGENT}


class Metadata:
    def __init__(self, riders: dict, teams: dict, stages: list):
        self.riders = riders          # bib(int) -> dict coureur
        self.teams = teams            # team_id(str) -> dict équipe
        self.stages = stages          # liste brute des étapes

    def rider(self, bib) -> dict:
        """Retourne les infos d'un coureur, avec repli si dossard inconnu."""
        try:
            bib = int(bib)
        except (TypeError, ValueError):
            return {"bib": bib, "name": f"#{bib}", "team": None}
        return self.riders.get(bib, {"bib": bib, "name": f"#{bib}", "team": None})

    def current_stage(self):
        """Étape la plus proche d'aujourd'hui (par date)."""
        today = datetime.now(timezone.utc).date()
        best, best_delta = None, None
        for s in self.stages:
            raw = s.get("date")
            if not raw:
                continue
            try:
                d = datetime.fromisoformat(raw).date()
            except ValueError:
                continue
            delta = abs((d - today).days)
            if best_delta is None or delta < best_delta:
                best, best_delta = s, delta
        return best


async def _fetch_json(client: httpx.AsyncClient, url: str):
    r = await client.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return r.json()


async def load_metadata() -> Metadata:
    async with httpx.AsyncClient() as client:
        competitors = await _fetch_json(client, COMPETITORS_URL)
        teams_raw = await _fetch_json(client, TEAM_URL)
        stages = await _fetch_json(client, STAGE_URL)

    teams = {
        t["_id"]: {
            "name": t.get("name"),
            "code": t.get("code"),
            "color": t.get("color"),
        }
        for t in teams_raw
        if t.get("_id")
    }

    riders: dict[int, dict] = {}
    for c in competitors:
        bib = c.get("bib")
        if bib is None:
            continue
        team_id = (c.get("$team") or "").split(":")[-1]
        team = teams.get(team_id, {})
        riders[int(bib)] = {
            "bib": int(bib),
            "name": c.get("lastnameshort") or c.get("lastname") or f"#{bib}",
            "firstname": c.get("firstname"),
            "team": team.get("name"),
            "teamCode": team.get("code"),
            "nationality": c.get("nationality"),
        }

    return Metadata(riders, teams, stages)


if __name__ == "__main__":
    import asyncio

    async def _main():
        meta = await load_metadata()
        print(f"{len(meta.riders)} coureurs, {len(meta.teams)} équipes, {len(meta.stages)} étapes")
        stage = meta.current_stage()
        if stage:
            arr = (stage.get("arrivalCity") or {}).get("label")
            print(f"Étape courante : n°{stage.get('stage')} → {arr} ({stage.get('length')} km)")
        # échantillon
        for bib in list(meta.riders)[:3]:
            r = meta.riders[bib]
            print(f"  #{bib} {r['name']} ({r['team']})")

    asyncio.run(_main())
