"""Sesion sintetica mientras no haya exportacion real (Fase 0 del plan de datos).
Extraido de la celda 16 del notebook. Guarda los bloques reales para poder
validar la segmentacion contra la verdad conocida."""

import numpy as np
import pandas as pd

from src.common.constants import SAMPLE_DT


def generar_sesion(duracion_min=68, fc_max=192, fc_base=100,
                    dur_bloque=(60, 140), dur_descanso=(70, 130),
                    fatiga=0.10, fatiga_recuperacion=0.8, seed=42):
    rng = np.random.default_rng(seed)
    n = int(duracion_min * 60 / SAMPLE_DT)
    fc = np.zeros(n)
    verdad = []
    i, actual = 0, fc_base
    while i < n:
        prog = i / n
        n_b = max(int(rng.integers(*dur_bloque) / SAMPLE_DT), 1)
        pico = fc_max * (0.94 - fatiga * prog) + rng.normal(0, 2.5)
        ini = i
        for _ in range(n_b):
            if i >= n: break
            actual += (pico - actual) * (1 - np.exp(-1 / 2.5))
            fc[i] = actual; i += 1
        if i > ini:
            verdad.append({"inicio_seg": ini * SAMPLE_DT, "fin_seg": (i - 1) * SAMPLE_DT})
        n_d = max(int(rng.integers(*dur_descanso) / SAMPLE_DT), 1)
        tau = 6.0 * (1 + fatiga_recuperacion * prog)
        for _ in range(n_d):
            if i >= n: break
            actual += (fc_base - actual) * (1 - np.exp(-1 / tau))
            fc[i] = actual; i += 1
    fc = np.clip(fc + rng.normal(0, 1.8, n), 60, fc_max)
    return pd.DataFrame({"t": np.arange(n) * SAMPLE_DT, "fc": np.round(fc, 1)}), verdad
