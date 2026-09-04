"""Lectura de la senal de velocidad. Hasta ahora `load_session()` construia la
columna `v` y nadie la consumia; aca se convierte en dos cosas concretas: un
perfil de la sesion (cuanto tiempo en sprint, cuanto en movimiento) y una medida
de si los bloques detectados por FC coinciden con los tramos rapidos.

Ojo con el principio del README ("Bloques, no sprints"): `frac_sprint` se usa
como discriminante del ARQUETIPO de sesion (intermitente vs continua), nunca
como un conteo de sprints que el jugador lea."""

import numpy as np

from src.common.constants import (
    FRAC_SPRINT_MIN_INTERMITENTE,
    UMBRAL_MOVIMIENTO_KMH,
    UMBRAL_SPRINT_KMH,
)

FUENTE_DERIVADA = "distance_km (derivada)"


def tiene_velocidad(df) -> bool:
    """True si la serie trae velocidad utilizable para razonar sobre sprints.

    Devuelve False cuando la fuente es `distance_km (derivada)`: esa velocidad
    sale de diferencias de distancia acumulada (muestras gruesas, ~una por
    minuto) y no resuelve un sprint de 3-5 s. Sirve para distinguir movimiento
    de reposo, no para medir picos."""
    if "v" not in df.columns:
        return False
    return df.attrs.get("fuente_velocidad") != FUENTE_DERIVADA


def perfil_velocidad(df, umbral_sprint=UMBRAL_SPRINT_KMH,
                      umbral_mov=UMBRAL_MOVIMIENTO_KMH):
    """Fracciones de tiempo por encima de cada umbral. None si no hay velocidad
    utilizable."""
    if not tiene_velocidad(df):
        return None
    v = df["v"].to_numpy()
    if len(v) == 0:
        return None
    return {"frac_sprint": float((v >= umbral_sprint).mean()),
            "frac_movimiento": float((v >= umbral_mov).mean()),
            "v_p95_kmh": float(np.percentile(v, 95))}


def patron_de_sesion(perfil, fuente_velocidad,
                      frac_min=FRAC_SPRINT_MIN_INTERMITENTE) -> str:
    """`sin_velocidad` | `no_evaluable` | `intermitente` | `continuo`.

    `no_evaluable` es el caso de la velocidad derivada de distancia: hay senal,
    pero no de la resolucion que haria falta para afirmar nada sobre sprints."""
    if fuente_velocidad == FUENTE_DERIVADA:
        return "no_evaluable"
    if perfil is None:
        return "sin_velocidad"
    return "intermitente" if perfil["frac_sprint"] >= frac_min else "continuo"


def solape_sprint_bloques(df, bloques, umbral_sprint=UMBRAL_SPRINT_KMH):
    """De las muestras en sprint, que fraccion cae dentro de algun bloque de FC.

    Mide si la FC y la velocidad estan hablando de lo mismo. Devuelve None (no
    0.0) cuando no hay muestras en sprint: un 0/0 no es un solape malo, es un
    solape inexistente."""
    if not tiene_velocidad(df):
        return None
    v, t = df["v"].to_numpy(), df["t"].to_numpy()
    en_sprint = v >= umbral_sprint
    if not en_sprint.any():
        return None
    dentro = np.zeros(len(t), dtype=bool)
    for b in bloques:
        dentro |= (t >= b["inicio_seg"]) & (t <= b["fin_seg"])
    return float(dentro[en_sprint].mean())
