"""Publication du snapshot vers le Worker Cloudflare (accès hors réseau local).

Fire-and-forget : appelé après chaque mise à jour d'état, non bloquant. Si
`TDF_PUBLISH_URL` / `TDF_PUBLISH_TOKEN` ne sont pas configurés, ne fait rien.
Voir cloudflare/README.md.
"""
from __future__ import annotations

import json

import httpx

from . import config

# Client réutilisé (connexions gardées) ; créé paresseusement dans la boucle.
_client: httpx.AsyncClient | None = None


def enabled() -> bool:
    return bool(config.PUBLISH_URL and config.PUBLISH_TOKEN)


async def publish(state: dict) -> None:
    if not enabled():
        return
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=15)
    try:
        r = await _client.put(
            config.PUBLISH_URL,
            content=json.dumps(state, ensure_ascii=False),
            headers={
                "Authorization": f"Bearer {config.PUBLISH_TOKEN}",
                "Content-Type": "application/json",
            },
        )
        if r.status_code != 200:
            print(f"[publish] réponse {r.status_code} du Worker: {r.text[:200]}")
    except Exception as e:  # réseau, timeout… on n'interrompt jamais le poll
        print(f"[publish] échec de publication: {e!r}")


async def aclose() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None
