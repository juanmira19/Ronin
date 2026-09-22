"""Lectura de la senal de velocidad.

Este modulo sabe leer la *senal* (de donde viene, si tiene resolucion
suficiente); `src/segment/calidad.py` es el que decide la *politica* de
confianza.

La velocidad NO decide si la sesion es intermitente: eso se mide con la forma
del esfuerzo (`numero_efectivo_bloques` en blocks.py), que es adimensional y no
penaliza al jugador lento. Aca solo queda lo que la velocidad sí puede
responder: si hay senal utilizable, y si los tramos rapidos coinciden con los
bloques de FC."""

import numpy as np

from src.common.constants import PERCENTIL_VELOZ

FUENTE_DERIVADA = "distance_km (derivada)"


def tiene_velocidad(df) -> bool:
    """True si la serie trae velocidad utilizable.

    Devuelve False cuando la fuente es `distance_km (derivada)`: esa velocidad
    sale de diferencias de distancia acumulada (muestras gruesas, ~una por
    minuto) y no resuelve cambios de ritmo cortos."""
    if "v" not in df.columns:
        return False
    return df.attrs.get("fuente_velocidad") != FUENTE_DERIVADA


def solape_veloz_bloques(df, bloques, percentil=PERCENTIL_VELOZ):
    """De las muestras mas rapidas de la propia sesion, que fraccion cae dentro
    de algun bloque de FC.

    El umbral es relativo (un percentil de esta misma sesion) y no absoluto:
    "rapido" solo tiene sentido comparado con el resto de la sesion del mismo
    jugador. Un umbral fijo en km/h penalizaria al jugador lento.

    Devuelve None si no hay velocidad utilizable, o si la velocidad es casi
    constante (GPS trabado): ahi "lo rapido" no discrimina nada."""
    if not tiene_velocidad(df):
        return None
    v, t = df["v"].to_numpy(), df["t"].to_numpy()
    if len(v) == 0:
        return None
    umbral = float(np.percentile(v, percentil))
    if np.isclose(umbral, v.min()):
        return None
    rapidas = v >= umbral
    dentro = np.zeros(len(t), dtype=bool)
    for b in bloques:
        dentro |= (t >= b["inicio_seg"]) & (t <= b["fin_seg"])
    return float(dentro[rapidas].mean())
