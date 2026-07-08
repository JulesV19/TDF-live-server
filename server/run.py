"""Point d'entrée : lance le serveur (API + feed) dans un seul process.

    python -m server.run            # poll réel de l'API letour
    python -m server.run --mock     # télémétrie synthétique (test hors course)
    python -m server.run --port 9000
"""
from __future__ import annotations

import argparse
import os


def main() -> None:
    parser = argparse.ArgumentParser(description="Serveur live Tour de France")
    parser.add_argument("--mock", action="store_true", help="télémétrie synthétique de test")
    parser.add_argument("--mock-idle", action="store_true",
                        help="mock 'hors course' : simule qu'aucune étape n'est en cours")
    parser.add_argument("--port", type=int, default=None, help="port HTTP (défaut 8000)")
    args = parser.parse_args()

    # Les variables d'env doivent être posées AVANT l'import de config.
    if args.mock or args.mock_idle:
        os.environ["TDF_MOCK"] = "1"
    if args.mock_idle:
        os.environ["TDF_MOCK_LIVE"] = "0"
    if args.port:
        os.environ["TDF_PORT"] = str(args.port)

    import uvicorn

    from . import config

    uvicorn.run("server.api:app", host=config.HOST, port=config.PORT, log_level="info")


if __name__ == "__main__":
    main()
