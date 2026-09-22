"""Interprete con cache para la demo.

Por que existe: en una demo en vivo la red es el punto de falla mas probable.
La capa deterministica no necesita red, pero la interpretacion si. Este modulo
intenta el modelo real y, si falla, sirve una respuesta que YA salio del modelo
en una corrida anterior, marcada como tal.

Regla que no se rompe: la cache solo guarda salidas reales del modelo. Nunca se
escribe a mano una interpretacion para que la demo "se vea bien" — si no hay
modelo ni cache, la demo lo dice y muestra solo lo deterministico."""

import hashlib
import json
from pathlib import Path

from src.interpret.preguntas import _responder_con_modelo
from src.interpret.prototype import _interpretar_con_modelo

CACHE_DIR = Path(__file__).resolve().parent / "cache"


class InterpretacionNoDisponible(RuntimeError):
    """No hubo modelo (sin red / sin API key) ni entrada en cache."""


def clave(payload: dict) -> str:
    """Hash del payload exacto que recibiria el modelo. Cambiar el RPE o la nota
    cambia la clave: la cache nunca devuelve la lectura de otra sesion."""
    canon = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()[:20]


def _leer(k: str, campo: str = "interpretacion"):
    f = CACHE_DIR / f"{k}.json"
    if not f.exists():
        return None
    return json.loads(f.read_text(encoding="utf-8")).get(campo)


def _guardar(k: str, datos: dict):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    (CACHE_DIR / f"{k}.json").write_text(
        json.dumps({"clave": k, **datos}, ensure_ascii=False, indent=2), encoding="utf-8")


def _con_cache(k: str, llamar, campo: str, meta: dict, modo: str, que: str) -> dict:
    """`modo`: auto (modelo y si falla cache) | vivo (solo modelo) | cache (solo cache).
    Agrega `_fuente` (`modelo` | `cache`) para que la pantalla lo pueda decir."""
    if modo == "cache":
        guardado = _leer(k, campo)
        if guardado is None:
            raise InterpretacionNoDisponible(
                f"No hay {que} en cache para esta combinacion de RPE y nota. "
                "Corre `python -m scripts.precalentar_cache` con red para generarla.")
        return {**guardado, "_fuente": "cache"}

    try:
        r = llamar()
        _guardar(k, {**meta, campo: r})
        return {**r, "_fuente": "modelo"}
    except Exception as exc:  # noqa: BLE001 — cualquier fallo de red/API cae a cache
        if modo == "vivo":
            raise
        guardado = _leer(k, campo)
        if guardado is None:
            raise InterpretacionNoDisponible(
                f"El modelo no respondio ({type(exc).__name__}) y no hay {que} en cache "
                "para esta combinacion de RPE y nota.") from exc
        return {**guardado, "_fuente": "cache"}


def _meta(payload: dict) -> dict:
    return {"nota": payload["REPORTE_DEL_JUGADOR"]["nota"],
            "esfuerzo_percibido": payload["REPORTE_DEL_JUGADOR"]["esfuerzo_percibido"]}


def interpretar(payload: dict, modo: str = "auto") -> dict:
    """La lectura de la sesion, con cache. `run_prototype` saca `_fuente` del
    dict antes de usarlo para que no contamine el contrato."""
    return _con_cache(clave(payload), lambda: _interpretar_con_modelo(payload),
                      "interpretacion", _meta(payload), modo, "interpretacion")


def responder(entrada: dict, modo: str = "auto") -> dict:
    """La respuesta a una pregunta sugerida, con cache. La clave incluye la
    pregunta y la lectura ya mostrada: nunca se sirve la respuesta de otra."""
    meta = {**_meta(entrada), "pregunta": entrada["PREGUNTA_DEL_JUGADOR"]}
    return _con_cache(clave(entrada), lambda: _responder_con_modelo(entrada),
                      "respuesta", meta, modo, "respuesta")
