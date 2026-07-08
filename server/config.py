"""Configuration centrale du serveur TDF live.

Toutes les valeurs sont surchargeables par variable d'environnement, ce qui
permet de changer l'année ou les intervalles sans toucher au code.
"""
import os
from pathlib import Path

# --- Source de données -------------------------------------------------------
YEAR = int(os.getenv("TDF_YEAR", "2026"))
BASE_URL = "https://racecenter.letour.fr"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)

# --- Serveur HTTP ------------------------------------------------------------
HOST = os.getenv("TDF_HOST", "0.0.0.0")      # 0.0.0.0 = joignable via Tailscale
PORT = int(os.getenv("TDF_PORT", "8000"))

# --- Cadence de poll (secondes) ---------------------------------------------
# Volontairement sobre pour ne PAS se faire rate-limiter : 1x/min en course.
POLL_INTERVAL_LIVE = int(os.getenv("TDF_POLL_LIVE", "60"))    # course en direct
POLL_INTERVAL_IDLE = int(os.getenv("TDF_POLL_IDLE", "300"))   # hors course (5 min)

# --- Regroupement ------------------------------------------------------------
# Nouveau groupe dès que l'écart (s) au coureur précédent dépasse ce seuil.
GROUP_GAP_THRESHOLD = float(os.getenv("TDF_GROUP_THRESHOLD", "5"))

# --- Mode ---------------------------------------------------------------------
MOCK = os.getenv("TDF_MOCK") == "1"

# --- Fichiers ----------------------------------------------------------------
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CURRENT_JSON = DATA_DIR / "current.json"


def _api(resource: str) -> str:
    return f"{BASE_URL}/api/{resource}-{YEAR}"


STAGE_URL = _api("stage")
COMPETITORS_URL = _api("allCompetitors")
TEAM_URL = _api("team")
TELEMETRY_URL = _api("telemetryCompetitor")  # renvoie le dernier snapshot live
