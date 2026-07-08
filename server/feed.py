"""Récupération de la télémétrie.

On POLL le endpoint `telemetryCompetitor-<year>` (qui renvoie le dernier
snapshot) plutôt que de parser le flux SSE : plus simple, plus robuste, et
suffisant à 1 poll/minute. Cadence sobre = aucun risque de rate-limit.
"""
from __future__ import annotations

import asyncio
from typing import Callable

import httpx

from .config import (
    MOCK_INTERVAL,
    MOCK_LIVE,
    POLL_INTERVAL_IDLE,
    POLL_INTERVAL_LIVE,
    TELEMETRY_URL,
    USER_AGENT,
)

HEADERS = {"User-Agent": USER_AGENT}


async def _fetch_telemetry(client: httpx.AsyncClient):
    r = await client.get(TELEMETRY_URL, headers=HEADERS, timeout=20)
    if r.status_code == 200:
        data = r.json()
        if isinstance(data, list) and data:
            return data[0]
    return None  # 204 = pas de snapshot dispo


async def poll_loop(on_telemetry: Callable[[dict], None]):
    """Poll réel de l'API. Cadence adaptative : 60 s en course, 5 min sinon."""
    backoff = 5
    async with httpx.AsyncClient() as client:
        while True:
            interval = POLL_INTERVAL_IDLE
            try:
                tel = await _fetch_telemetry(client)
                if tel is not None:
                    on_telemetry(tel)
                    interval = (
                        POLL_INTERVAL_LIVE if tel.get("RaceStatus") else POLL_INTERVAL_IDLE
                    )
                backoff = 5
            except Exception as e:  # réseau, 4xx/5xx, JSON…
                print(f"[feed] erreur: {e!r} — nouvelle tentative dans {backoff}s")
                interval = backoff
                backoff = min(backoff * 2, 120)
            await asyncio.sleep(interval)


async def mock_loop(on_telemetry: Callable[[dict], None], meta_getter: Callable[[], object]):
    """Boucle de démo : télémétrie synthétique qui évolue à la cadence MOCK_INTERVAL.

    Si MOCK_LIVE est faux, émet un état 'hors course' figé (pour tester le message
    'pas d'étape en cours')."""
    from .mock import make_offrace, make_telemetry

    if not MOCK_LIVE:
        while True:
            on_telemetry(make_offrace())
            await asyncio.sleep(MOCK_INTERVAL)

    step = 0
    while True:
        on_telemetry(make_telemetry(meta_getter(), step))
        step = (step + 1) % 40          # 40 pas de scénario, puis rejoue
        await asyncio.sleep(MOCK_INTERVAL)
