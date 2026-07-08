"""État courant de la course, en mémoire + persistance atomique dans current.json.

Snapshot uniquement (pas d'historique). L'API lit `get_state()` ; le feed
appelle `set_state()` à chaque mise à jour.
"""
from __future__ import annotations

import json
import os
import threading
import time

from .config import CURRENT_JSON, DATA_DIR

_lock = threading.Lock()
_current: dict = {
    "live": False,
    "stage": None,
    "kmToFinish": None,
    "groups": [],
    "updatedAt": None,
}
_last_write = 0.0
_WRITE_THROTTLE = 3.0  # écriture disque au plus toutes les 3 s


def get_state() -> dict:
    with _lock:
        return dict(_current)


def set_state(state: dict, force_write: bool = False) -> None:
    global _last_write
    with _lock:
        _current.clear()
        _current.update(state)
        now = time.time()
        if force_write or now - _last_write >= _WRITE_THROTTLE:
            _write(state)
            _last_write = now


def _write(state: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    tmp = CURRENT_JSON.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, CURRENT_JSON)  # remplacement atomique
