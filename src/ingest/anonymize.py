"""Convierte un export crudo de Health Auto Export (JSON, version V2) en una
version segura para versionar: sin lat/lon absolutas, sin identificadores de
dispositivo/usuario, con timestamps relativos al inicio de la sesion en vez de
fecha/hora real. Ver README (seccion Privacidad) y el plan de datos (Fase 0)."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


def _seg(date_str: str, inicio: datetime) -> int:
    dt = datetime.strptime(date_str[:19], "%Y-%m-%d %H:%M:%S")
    return int((dt - inicio).total_seconds())


def anonymize_dict(raw: dict) -> dict:
    """Toma el JSON crudo ya parseado (formato Health Auto Export V2, con el
    wrapper {"data": {"workouts": [...]}}) y devuelve el dict anonimizado del
    primer workout."""
    w = raw["data"]["workouts"][0]
    inicio = datetime.strptime(w["start"][:19], "%Y-%m-%d %H:%M:%S")

    heart_rate = [
        {"t": _seg(m["date"], inicio), "bpm": round(m.get("Avg", m.get("qty")), 1)}
        for m in w.get("heartRateData", [])
    ]
    # Solo velocidad, nunca lat/lon: la posicion absoluta no hace falta para
    # detectar bloques de esfuerzo y es informacion sensible.
    route_speed = [
        {"t": _seg(p["timestamp"], inicio), "speed_kmh": round(p.get("speed", 0) * 3.6, 2)}
        for p in w.get("route", [])
        if p.get("speed") is not None
    ]
    distance_km = [
        {"t": _seg(p["date"], inicio), "km": round(p.get("qty", 0), 5)}
        for p in w.get("walkingAndRunningDistance", [])
    ]

    # El campo `duration` de Health Auto Export es tiempo "activo" (excluye
    # Auto-Pausa), no el rango real de la sesion — puede quedar muy por debajo
    # del ultimo timestamp real si hubo tramos parado (frecuente en deportes de
    # parada-arranque como ultimate). Se usa el maximo timestamp observado en
    # cualquier señal como duracion real para no truncar datos.
    todos_los_t = ([m["t"] for m in heart_rate] + [p["t"] for p in route_speed]
                    + [p["t"] for p in distance_km])
    duracion_real = max(todos_los_t) if todos_los_t else int(w.get("duration", 0))

    return {
        "tipo_sesion": w.get("name"),
        "duracion_seg": duracion_real,
        "duracion_activa_seg": int(w.get("duration", 0)),
        "es_outdoor": not w.get("isIndoor", True),
        "heart_rate": heart_rate,
        "route_speed": route_speed,
        "distance_km": distance_km,
    }


def anonymize_workout(raw_path: str | Path, out_path: str | Path) -> dict:
    """Lee un export crudo desde disco y escribe la version anonimizada en `out_path`."""
    raw = json.loads(Path(raw_path).read_text(encoding="utf-8"))
    anon = anonymize_dict(raw)
    Path(out_path).write_text(json.dumps(anon, ensure_ascii=False, indent=2), encoding="utf-8")
    return anon
