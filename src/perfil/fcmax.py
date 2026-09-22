"""Resolucion de la FC maxima del perfil.

Por que existe: el umbral de bloque es 80% de FCmax, asi que TODA la
segmentacion hereda el error de ese numero. Pedirselo al usuario no funciona
(no lo sabe) y estimarlo por edad tampoco (220-edad da ~200 para un jugador de
20 anos; con ese valor la segmentacion del partido de prueba pierde la mitad de
los bloques y la conclusion de degradacion se invierte).

La alternativa que se usa aqui es medirlo: la FCmax del perfil es la mayor que
el propio jugador ha alcanzado en sus sesiones. Es un dato observado, no una
hipotesis, y es coherente con el principio de que ningun umbral compara al
jugador con otro.

Dos cuidados:

- Se toma el maximo de la **mediana movil**, no el maximo crudo ni el de la
  media movil. Un pico espurio del sensor (una muestra de 210 en alguien que
  llega a 180) fijaria una FCmax inflada, lo que sube el umbral y borra bloques
  reales. La media movil no alcanza: con ventana de 15 s solo atenua ese pico a
  190, o sea 10 ppm de error que se propagan al umbral. La mediana con ventana
  de 25 s lo descarta por completo, y aguanta hasta dos muestras malas
  seguidas, mientras que un esfuerzo maximo real —que por definicion dura mas
  que un bloque, o sea >=30 s— la atraviesa intacto.
- Con pocas sesiones el maximo observado todavia es un piso, no la FCmax real:
  el jugador aun no ha llegado a su techo. Mientras eso pase, la estimacion se
  marca `provisional` y la confianza de la segmentacion no puede ser `alta`.
"""

import pandas as pd

from src.common.constants import SAMPLE_DT

MIN_SESIONES_CONFIABLE = 3  # por debajo de esto, el maximo observado es un piso
VENTANA_MEDIANA_SEG = 25  # descarta hasta 2 muestras malas seguidas; < dur_min_seg de un bloque


def fcmax_observada(df) -> float:
    """Mayor FC sostenida de una sesion. Ver el modulo: mediana movil, no el
    maximo crudo — un pico de una o dos muestras es ruido del sensor, no el
    techo del jugador."""
    w = max(int(VENTANA_MEDIANA_SEG / SAMPLE_DT), 1)
    estable = pd.Series(df["fc"]).rolling(w, center=True, min_periods=1).median()
    return float(estable.max())


def estimar_fcmax(observadas, minimo_sesiones: int = MIN_SESIONES_CONFIABLE) -> dict:
    """`observadas`: FCmax observadas en cada sesion del jugador, la actual incluida."""
    validas = [float(v) for v in observadas if v and v > 0]
    if not validas:
        raise ValueError("No hay ninguna FC observada de la que derivar la FCmax")
    return {"fc_max": max(validas),
            "fuente": "observada",
            "sesiones": len(validas),
            "provisional": len(validas) < minimo_sesiones}


def resolver_fcmax(perfil: dict, df) -> dict:
    """Decide con que FCmax trabajar esta sesion.

    Si el perfil declara `fc_max` se respeta tal cual (compatibilidad: los evals
    y los tests la fijan a proposito para que el umbral no se mueva). Si no, se
    deriva del historial de FCmax observadas del jugador mas esta sesion."""
    declarada = perfil.get("fc_max")
    if declarada:
        return {"fc_max": float(declarada), "fuente": "declarada",
                "sesiones": None, "provisional": False}

    observadas = list(perfil.get("fcmax_observadas") or [])
    observadas.append(fcmax_observada(df))
    return estimar_fcmax(observadas)
