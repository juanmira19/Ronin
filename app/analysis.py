"""Orquesta el pipeline para la demo y arma el payload que consume la pagina.

No calcula ninguna metrica de producto: todas vienen de `src/`. Lo unico que
agrega son (a) las estadisticas estilo reloj, que existen justamente para
mostrar el contraste con lo que Ronin ve, y (b) el remuestreo de la serie para
dibujarla."""

import functools
import json
from typing import Callable

import numpy as np

from app.llm_cache import InterpretacionNoDisponible, interpretar as interpretar_cache
from app.presets import ESCALA, HISTORIAL, NOTAS, PERFIL, SESIONES, ruta
from src.common.constants import SAMPLE_DT
from src.ingest.health_auto_export import load_session
from src.interpret.prototype import contract_check, run_prototype

MAX_PUNTOS_GRAFICA = 700


@functools.lru_cache(maxsize=8)
def _cargar(archivo: str):
    return load_session(archivo)


def serie_de(sesion_id: str):
    sesion = SESIONES[sesion_id]
    df = _cargar(str(ruta(sesion))).copy()
    df.attrs = _cargar(str(ruta(sesion))).attrs
    if sesion["recorte_seg"]:
        attrs = dict(df.attrs)
        df = df[df["t"] <= sesion["recorte_seg"]].reset_index(drop=True)
        df.attrs = attrs  # pandas pierde attrs al filtrar
    return df


def _distancia_del_export(sesion: dict, hasta_seg=None):
    """Distancia que reporta el propio export, cuando la trae. Se prefiere sobre
    integrar la velocidad: la idea de la pantalla es mostrar la cifra del reloj
    tal cual, no una reconstruccion nuestra. `distance_km` viene por incrementos."""
    datos = json.loads(ruta(sesion).read_text(encoding="utf-8"))
    tramos = datos.get("distance_km") or []
    if not tramos:
        return None
    return sum(x["km"] for x in tramos
               if hasta_seg is None or x["t"] <= hasta_seg)


def estadisticas_reloj(df, sesion: dict | None = None) -> dict:
    """Lo que muestra el reloj al terminar: distancia, ritmo medio, FC media.

    Es exactamente el promedio que el README acusa de borrar la informacion, asi
    que la demo lo calcula de verdad en vez de citarlo de memoria."""
    dur_seg = float(df["t"].iloc[-1] - df["t"].iloc[0])
    fila = {"duracion_min": round(dur_seg / 60, 1),
            "fc_media": round(float(df["fc"].mean())),
            "fc_max": round(float(df["fc"].max()))}
    km = _distancia_del_export(sesion, df["t"].iloc[-1]) if sesion else None
    fila["fuente_distancia"] = "export" if km is not None else None
    if km is None and "v" in df.columns:
        # sin distancia en el export: integrar velocidad (km/h) sobre la malla
        km = float(np.nansum(df["v"].to_numpy()) * SAMPLE_DT / 3600)
        fila["fuente_distancia"] = "integrada"
    if km is not None:
        fila["distancia_km"] = round(km, 2)
        if km > 0:
            min_por_km = (dur_seg / 60) / km
            fila["ritmo_medio"] = f"{int(min_por_km)}:{round((min_por_km % 1) * 60):02d}"
    return fila


def serie_grafica(df, bloques) -> dict:
    """Serie remuestreada para dibujar, mas los bloques en segundos."""
    paso = max(1, len(df) // MAX_PUNTOS_GRAFICA)
    sub = df.iloc[::paso]
    datos = {"t": [int(x) for x in sub["t"]],
             "fc": [float(x) for x in sub["fc"]],
             "duracion_seg": int(df["t"].iloc[-1])}
    if "v" in df.columns:
        datos["v"] = [float(x) for x in sub["v"]]
    datos["bloques"] = [{"inicio_seg": b["inicio_seg"], "fin_seg": b["fin_seg"],
                         "intensidad": b["intensidad"], "pct_fcmax": b["pct_fcmax"],
                         "duracion_seg": b["duracion_seg"]}
                        for b in (bloques or [])]
    return datos


def analizar(sesion_id: str, rpe: int, nota: str, modo: str = "auto",
             interpretar: Callable | None = None) -> dict:
    """Corre el pipeline real y devuelve todo lo que la pagina necesita pintar.

    Si el modelo no esta disponible y no hay cache, NO se inventa la
    interpretacion: se devuelve la capa deterministica completa y una bandera
    que la pagina muestra como tal."""
    sesion = SESIONES[sesion_id]
    df = serie_de(sesion_id)
    detalle: dict = {}

    interpretar = interpretar or (lambda payload: interpretar_cache(payload, modo=modo))
    real_input = {"perfil": PERFIL, "serie": df, "tipo_sesion": sesion["tipo_sesion"],
                  "esfuerzo_percibido": rpe, "nota": nota, "historial": HISTORIAL}

    base = {"sesion": {k: v for k, v in sesion.items() if k != "archivo"},
            "reloj": estadisticas_reloj(df, sesion),
            "perfil": PERFIL}

    try:
        salida = run_prototype(real_input, detalle=detalle, interpretar=interpretar)
        interpretacion_disponible = True
        motivo_sin_interpretacion = None
    except InterpretacionNoDisponible as exc:
        # La capa deterministica ya corrio y quedo en `detalle`: se muestra igual.
        salida = None
        interpretacion_disponible = False
        motivo_sin_interpretacion = str(exc)

    base["grafica"] = serie_grafica(df, detalle.get("bloques"))
    base["calidad"] = detalle.get("calidad")
    base["metricas"] = detalle.get("metricas")
    base["verificacion"] = {
        "ejecutada": "cifras_intrusas" in detalle,
        "cifras_intrusas": detalle.get("cifras_intrusas", []),
        "texto_descartado": detalle.get("texto_descartado", False),
    }
    base["fcmax"] = detalle.get("fcmax")
    base["fuente_interpretacion"] = detalle.get("fuente_interpretacion")
    base["interpretacion_disponible"] = interpretacion_disponible
    base["motivo_sin_interpretacion"] = motivo_sin_interpretacion
    base["etapa_fallida"] = detalle.get("etapa_fallida")

    if salida is None:
        base["estado"] = "sin_interpretacion"
        base["salida"] = None
        base["contract_check"] = None
    elif "error" in salida:
        base["estado"] = "rechazada"
        base["salida"] = salida
        base["contract_check"] = contract_check(salida)
    else:
        base["estado"] = "ok"
        base["salida"] = salida
        base["contract_check"] = contract_check(salida)
    return base


def catalogo() -> dict:
    return {"sesiones": list(SESIONES.values()), "notas": NOTAS,
            "escala": ESCALA, "perfil": PERFIL}
