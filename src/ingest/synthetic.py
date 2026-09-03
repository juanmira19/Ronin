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


def generar_export_sintetico_partido(
    n_puntos=18, fc_max=192, fc_base=95,
    dur_punto=(20, 90), dur_descanso=(25, 150),
    medio_tiempo_seg=300, seed=7,
):
    """Genera un partido de ultimate sintetico, pero con la misma forma que un
    export real ya anonimizado (`src/ingest/anonymize.py`): timestamps
    irregulares (no una malla perfecta cada 5 s), velocidad GPS con picos de
    sprint durante los puntos y casi cero en los descansos, y un medio tiempo
    largo a la mitad. Sirve de proxy mientras el equipo no ha podido grabar un
    partido real (ver TEAM_ROTATION.md / MAKERS_REVIEW.md).

    A diferencia de `generar_sesion()` (grilla regular de FC, sin velocidad),
    esto pasa por el mismo camino que un export real: se lee con
    `src/ingest/health_auto_export.load_session()`.
    """
    rng = np.random.default_rng(seed)
    dt_fino = 0.5  # grilla fina interna para simular la fisiologia, no lo que se muestrea
    fase = []  # lista de (duracion_seg, objetivo_fc_pct, es_punto)
    for punto in range(n_puntos):
        fase.append((rng.uniform(*dur_punto), rng.uniform(0.85, 0.97), True))
        if punto == n_puntos // 2:
            fase.append((medio_tiempo_seg, 0.0, False))
        fase.append((rng.uniform(*dur_descanso), 0.0, False))

    duracion_total = sum(d for d, _, _ in fase)
    n = int(duracion_total / dt_fino) + 1
    fc_fino = np.zeros(n)
    v_fino = np.zeros(n)
    t_actual, i, hr_actual = 0.0, 0, fc_base
    progreso_fatiga = 0.0
    for dur, objetivo_pct, es_punto in fase:
        n_pasos = max(int(dur / dt_fino), 1)
        objetivo_fc = fc_max * (objetivo_pct - 0.05 * progreso_fatiga) if es_punto else fc_base
        # Recuperar cuesta mas a medida que avanza el partido (fatiga acumulada).
        tau = (2.5 if es_punto else 6.0 * (1 + 1.1 * progreso_fatiga))
        for paso in range(n_pasos):
            if i >= n:
                break
            hr_actual += (objetivo_fc - hr_actual) * (1 - np.exp(-dt_fino / tau))
            fc_fino[i] = hr_actual
            if es_punto:
                # dentro de un punto: sprints cortos intercalados con jog/posicionamiento
                ciclo = (paso * dt_fino) % 12
                v_obj = 19 + rng.normal(0, 2.5) if ciclo < 3 else 6 + rng.normal(0, 1.5)
            else:
                v_obj = rng.normal(1.2, 0.6)  # caminando de vuelta / parado
            v_fino[i] = max(v_obj, 0.0)
            i += 1
        t_actual += dur
        progreso_fatiga = min(t_actual / duracion_total, 1.0)

    fc_fino = np.clip(fc_fino[:i] + rng.normal(0, 1.8, i), 60, fc_max)
    v_fino = np.clip(v_fino[:i] + rng.normal(0, 0.8, i), 0, None)
    t_fino = np.arange(i) * dt_fino
    duracion_seg = int(t_fino[-1])

    # Sub-muestreo a intervalos irregulares, como un sensor real (no una malla
    # perfecta): FC cada ~2 s con jitter, velocidad GPS cada ~1 s con jitter.
    def _muestrear(t_fino, y_fino, intervalo):
        muestras_t, t = [], 0.0
        while t < t_fino[-1]:
            muestras_t.append(t)
            t += intervalo + rng.uniform(-0.3, 0.3) * intervalo
        muestras_t = np.array(muestras_t)
        return muestras_t, np.interp(muestras_t, t_fino, y_fino)

    hr_t, hr_v = _muestrear(t_fino, fc_fino, 2.0)
    sp_t, sp_v = _muestrear(t_fino, v_fino, 1.0)

    heart_rate = [{"t": int(round(t)), "bpm": round(float(v), 1)} for t, v in zip(hr_t, hr_v)]
    route_speed = [{"t": int(round(t)), "speed_kmh": round(float(v), 2)} for t, v in zip(sp_t, sp_v)]

    return {
        "tipo_sesion": "Partido Ultimate (sintetico realista)",
        "duracion_seg": duracion_seg,
        "duracion_activa_seg": duracion_seg,
        "es_outdoor": True,
        "heart_rate": heart_rate,
        "route_speed": route_speed,
        "distance_km": [],
    }
