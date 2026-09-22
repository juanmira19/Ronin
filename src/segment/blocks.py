"""Segmentacion deterministica de bloques de esfuerzo. Extraido de la celda 16
del notebook (19y1_20_Makers_AI_Product_Ronin_1-2.ipynb). La IA no calcula
estos numeros: el sistema si."""

import numpy as np
import pandas as pd

from src.common.constants import LATENCIA_FC_SEG, SAMPLE_DT, UMBRAL_MOVIMIENTO_KMH


def _adelantar_inicios(tramos, v, latencia_fc_seg, umbral_mov):
    """La FC llega tarde: cuando cruza el umbral el esfuerzo ya habia empezado.
    Si justo antes del bloque el jugador YA se estaba moviendo, el inicio real
    es antes. Se adelanta como maximo `latencia_fc_seg` y nunca por encima del
    fin del bloque anterior.

    Solo hacia atras: la FC tambien baja tarde, pero extender el final inflaria
    la duracion sin ninguna senal que lo respalde."""
    max_pasos = int(latencia_fc_seg / SAMPLE_DT)
    salida, limite = [], -1
    for a, b in tramos:
        nuevo_a, pasos = a, 0
        while (nuevo_a - 1 > limite and pasos < max_pasos
               and v[nuevo_a - 1] >= umbral_mov):
            nuevo_a -= 1
            pasos += 1
        salida.append([nuevo_a, b])
        limite = b
    return salida


def detectar_bloques(df, fc_max, umbral_pct=0.80, dur_min_seg=30, gap_max_seg=20,
                     usar_velocidad=True, latencia_fc_seg=LATENCIA_FC_SEG,
                     umbral_movimiento_kmh=UMBRAL_MOVIMIENTO_KMH):
    """Bloque = FC suavizada sobre el 80% de FCmax, minimo 30 s, fusionando huecos < 20 s.

    Si la serie trae velocidad, se usa solo para corregir el inicio de cada
    bloque (ver `_adelantar_inicios`). La velocidad nunca cambia la cantidad de
    bloques, ni `fc_pico`, ni la intensidad: en eso manda la FC."""
    w = max(int(15 / SAMPLE_DT), 1)
    fc_s = pd.Series(df["fc"]).rolling(w, center=True, min_periods=1).mean().to_numpy()
    encima = fc_s >= umbral_pct * fc_max

    tramos, ini = [], None
    for i, v in enumerate(encima):
        if v and ini is None:
            ini = i
        elif not v and ini is not None:
            tramos.append([ini, i - 1]); ini = None
    if ini is not None:
        tramos.append([ini, len(encima) - 1])

    fus = []
    for tr in tramos:
        if fus and (tr[0] - fus[-1][1]) * SAMPLE_DT <= gap_max_seg:
            fus[-1][1] = tr[1]
        else:
            fus.append(tr)

    # El filtro de duracion minima se aplica sobre la duracion MEDIDA POR FC.
    # La velocidad no rescata bloques descartados: si lo hiciera, estaria
    # creando bloques que la FC nunca vio, o sea fabricando la metrica.
    fus = [tr for tr in fus if (tr[1] - tr[0] + 1) * SAMPLE_DT >= dur_min_seg]

    if usar_velocidad and "v" in df.columns:
        fus = _adelantar_inicios(fus, df["v"].to_numpy(),
                                 latencia_fc_seg, umbral_movimiento_kmh)

    raw = df["fc"].to_numpy()
    bloques = []
    for a, b in fus:
        dur = (b - a + 1) * SAMPLE_DT
        pico = float(raw[a:b + 1].max())
        p = pico / fc_max
        bloques.append({"inicio_seg": int(df["t"].iloc[a]), "fin_seg": int(df["t"].iloc[b]),
                        "duracion_seg": int(dur), "fc_pico": pico,
                        "pct_fcmax": round(100 * p, 1),
                        "intensidad": "bajo" if p < 0.85 else ("moderado" if p < 0.92 else "maximo")})
    return bloques


def numero_efectivo_bloques(bloques) -> float:
    """Inverso del indice de Herfindahl sobre las duraciones: `(sum d)^2 / sum d^2`.

    Adimensional, se lee como "cuantos esfuerzos distintos hubo". No depende de
    la velocidad del jugador ni de la duracion tipica del deporte: 20 puntos de
    30 s y 6 tramos de 400 s dan 20 y 6 respectivamente.

    Pondera por duracion, que es la razon de usar esto en vez de `len(bloques)`:
    una corrida continua con un blip corto al lado ([500, 30]) da 1.12 — un solo
    esfuerzo con ruido —, mientras que contar bloques diria 2.

    Nota: opera sobre duraciones ya refinadas por velocidad (`_adelantar_inicios`),
    pero el adelanto es de a lo sumo LATENCIA_FC_SEG, asi que mueve el resultado
    en decimas. Sin bloques -> 0.0."""
    if not bloques:
        return 0.0
    d = np.array([b["duracion_seg"] for b in bloques], dtype=float)
    suma_cuadrados = float((d ** 2).sum())
    if suma_cuadrados == 0:
        return 0.0
    return float(d.sum() ** 2 / suma_cuadrados)


def patron_de_sesion(bloques) -> str:
    """`intermitente` | `continuo` | `sin_bloques`.

    El criterio no es una constante calibrable sino una definicion: redondeado a
    esfuerzos enteros, ¿hubo al menos dos? Para dos bloques la frontera cae en
    una razon de duraciones de 3.73x, o sea que cuentan como dos esfuerzos salvo
    que uno sea casi cuatro veces el otro.

    No mira la velocidad: el patron de arranque-parada esta en la forma del
    esfuerzo, no en que tan rapido corra el jugador."""
    if not bloques:
        return "sin_bloques"
    return "intermitente" if round(numero_efectivo_bloques(bloques)) >= 2 else "continuo"


def hrr60(df, bloque):
    """Ppm que baja la FC en los 60 s posteriores al bloque."""
    fc, t = df["fc"].to_numpy(), df["t"].to_numpy()
    i0 = int(np.searchsorted(t, bloque["fin_seg"]))
    i1 = int(np.searchsorted(t, bloque["fin_seg"] + 60))
    return None if i1 >= len(fc) else float(fc[i0] - fc[i1])
