"""API HTTP : expose l'état de course courant à l'app (polling).

Un seul process : au démarrage on charge les métadonnées puis on lance en tâche
de fond la boucle de poll (ou la boucle mock). L'app interroge GET /race/current.
"""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from . import config, feed, normalize, state
from .metadata import load_metadata

_meta = None  # métadonnées chargées au démarrage


def _handle_telemetry(telemetry: dict) -> None:
    state.set_state(normalize.build_race_state(telemetry, _meta))


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _meta
    _meta = await load_metadata()
    print(
        f"[api] métadonnées : {len(_meta.riders)} coureurs, "
        f"{len(_meta.teams)} équipes, {len(_meta.stages)} étapes"
    )
    if config.MOCK:
        print("[api] MODE MOCK — télémétrie synthétique (pas d'appel à l'API letour)")
        task = asyncio.create_task(feed.mock_loop(_handle_telemetry, lambda: _meta))
    else:
        print(
            f"[api] poll réel toutes les {config.POLL_INTERVAL_LIVE}s "
            f"(course) / {config.POLL_INTERVAL_IDLE}s (repos)"
        )
        task = asyncio.create_task(feed.poll_loop(_handle_telemetry))
    try:
        yield
    finally:
        task.cancel()


app = FastAPI(title="TDF Live Server", lifespan=lifespan)


@app.get("/race/current")
async def race_current():
    return JSONResponse(state.get_state())


@app.get("/health")
async def health():
    return {"ok": True, "riders": len(_meta.riders) if _meta else 0, "mock": config.MOCK}
