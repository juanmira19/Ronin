"""Segmentacion deterministica de bloques de esfuerzo. Extraido de la celda 16
del notebook (19y1_20_Makers_AI_Product_Ronin_1-2.ipynb). La IA no calcula
estos numeros: el sistema si."""

import numpy as np
import pandas as pd

from src.common.constants import SAMPLE_DT


def detectar_bloques(df, fc_max, umbral_pct=0.80, dur_min_seg=30, gap_max_seg=20):
    """Bloque = FC suavizada sobre el 80% de FCmax, minimo 30 s, fusionando huecos < 20 s."""
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

    raw = df["fc"].to_numpy()
    bloques = []
    for a, b in fus:
        dur = (b - a + 1) * SAMPLE_DT
        if dur < dur_min_seg:
            continue
        pico = float(raw[a:b + 1].max())
        p = pico / fc_max
        bloques.append({"inicio_seg": int(df["t"].iloc[a]), "fin_seg": int(df["t"].iloc[b]),
                        "duracion_seg": int(dur), "fc_pico": pico,
                        "pct_fcmax": round(100 * p, 1),
                        "intensidad": "bajo" if p < 0.85 else ("moderado" if p < 0.92 else "maximo")})
    return bloques


def hrr60(df, bloque):
    """Ppm que baja la FC en los 60 s posteriores al bloque."""
    fc, t = df["fc"].to_numpy(), df["t"].to_numpy()
    i0 = int(np.searchsorted(t, bloque["fin_seg"]))
    i1 = int(np.searchsorted(t, bloque["fin_seg"] + 60))
    return None if i1 >= len(fc) else float(fc[i0] - fc[i1])
