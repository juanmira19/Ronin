"""Lee una sesion (cruda o anonimizada) de Health Auto Export y la convierte al
mismo formato que consume el resto del pipeline (`generar_sesion()` en
src/ingest/synthetic.py): un DataFrame con columnas `t` (segundos, malla
regular cada SAMPLE_DT) y `fc`. Agrega `v` (km/h) cuando hay velocidad
disponible, por GPS (`route`) o derivada de distancia."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.common.constants import SAMPLE_DT
from src.ingest.anonymize import anonymize_dict

GAP_AVISO_SEG = 60  # huecos mas grandes que esto en el crudo se interpolan igual, pero se avisan


def _es_crudo(data: dict) -> bool:
    return "data" in data and "workouts" in data.get("data", {})


def _a_malla_regular(muestras_t: list[int], muestras_v: list[float], duracion_seg: int) -> np.ndarray:
    """Interpola muestras irregulares (t, v) sobre una malla cada SAMPLE_DT segundos."""
    grid = np.arange(0, duracion_seg + SAMPLE_DT, SAMPLE_DT)
    if not muestras_t:
        return np.full(grid.shape, np.nan)
    return np.interp(grid, muestras_t, muestras_v)


def load_session(path: str | Path) -> pd.DataFrame:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    anon = anonymize_dict(data) if _es_crudo(data) else data

    duracion = anon["duracion_seg"]

    hr_t = [m["t"] for m in anon["heart_rate"]]
    hr_v = [m["bpm"] for m in anon["heart_rate"]]
    if hr_t:
        gaps = np.diff(sorted(hr_t))
        if len(gaps) and gaps.max() > GAP_AVISO_SEG:
            print(f"Aviso: hueco de {int(gaps.max())}s en heart_rate — se interpola igual, "
                  f"revisar si el export vino agregado en vez de raw.")

    grid = np.arange(0, duracion + SAMPLE_DT, SAMPLE_DT)
    fc = _a_malla_regular(hr_t, hr_v, duracion)

    df = pd.DataFrame({"t": grid.astype(int), "fc": np.round(fc, 1)})

    velocidad = anon.get("route_speed") or []
    fuente_v = "route_speed"
    if not velocidad and anon.get("distance_km"):
        # sin GPS: derivar velocidad km/h por diferencia entre muestras de distancia
        dist = anon["distance_km"]
        velocidad = [
            {"t": dist[i]["t"],
             "speed_kmh": max(0.0, (dist[i]["km"] - dist[i - 1]["km"])
                               / max(dist[i]["t"] - dist[i - 1]["t"], 1) * 3600)}
            for i in range(1, len(dist))
        ]
        fuente_v = "distance_km (derivada)"

    if velocidad:
        v_t = [p["t"] for p in velocidad]
        v_v = [p["speed_kmh"] for p in velocidad]
        df["v"] = np.round(_a_malla_regular(v_t, v_v, duracion), 2)

    df.attrs["tipo_sesion"] = anon.get("tipo_sesion")
    df.attrs["fuente_velocidad"] = fuente_v if velocidad else None
    return df
