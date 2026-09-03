"""Genera un sample sintetico de partido de ultimate, con la misma forma que un
export real ya anonimizado, mientras el equipo no ha podido grabar un partido
real (ver TEAM_ROTATION.md / MAKERS_REVIEW.md, respuesta 2026-09-01).

    python generate_synthetic_sample.py
"""

import json
from pathlib import Path

from src.ingest.synthetic import generar_export_sintetico_partido

OUT_PATH = Path("data/samples/partido_sintetico_2026-09-01.json")


def main():
    export = generar_export_sintetico_partido()
    OUT_PATH.write_text(json.dumps(export, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Escrito {OUT_PATH}: duracion_seg={export['duracion_seg']}, "
          f"{len(export['heart_rate'])} muestras FC, {len(export['route_speed'])} muestras velocidad")


if __name__ == "__main__":
    main()
