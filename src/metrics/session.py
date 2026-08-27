"""Degradacion, recuperacion, divergencia percepcion-vs-carga y comparacion con
historial. Extraido de la celda 16 del notebook. Todo deterministico."""

import numpy as np

from src.segment.blocks import hrr60


def calcular_metricas(df, bloques, fc_max):
    if len(bloques) < 2:
        raise ValueError("Segmentacion insuficiente: menos de 2 bloques detectados")
    mitad = df["t"].iloc[-1] / 2
    b1 = [b for b in bloques if b["inicio_seg"] < mitad]
    b2 = [b for b in bloques if b["inicio_seg"] >= mitad]

    if b1 and b2:
        p1 = float(np.mean([b["fc_pico"] for b in b1]))
        p2 = float(np.mean([b["fc_pico"] for b in b2]))
        pico_pct = round(100 * (p2 - p1) / p1, 1)
    else:
        pico_pct = 0.0

    r1 = [v for v in (hrr60(df, b) for b in b1) if v is not None]
    r2 = [v for v in (hrr60(df, b) for b in b2) if v is not None]
    rec_pct = (round(100 * (np.mean(r1) - np.mean(r2)) / np.mean(r1), 1)
               if r1 and r2 and np.mean(r1) > 0 else 0.0)

    dist = {"bajo": 0, "moderado": 0, "maximo": 0}
    for b in bloques:
        dist[b["intensidad"]] += 1

    pico_pct, rec_pct = float(pico_pct), float(rec_pct)
    return {"bloques_esfuerzo": {"cantidad": len(bloques),
                                 "duracion_media_seg": int(np.mean([b["duracion_seg"] for b in bloques])),
                                 "distribucion": dist},
            "degradacion": {"pico_pct": pico_pct, "recuperacion_pct": rec_pct},
            "duracion_sesion_min": int(df["t"].iloc[-1] / 60),
            # El sistema resuelve el sentido de cada cifra. El modelo no interpreta
            # signos: solo redacta a partir de estas conclusiones ya resueltas.
            "conclusiones": {
                "pico": ("perdio intensidad en la segunda mitad" if pico_pct < -2
                         else "subio la intensidad en la segunda mitad" if pico_pct > 2
                         else "mantuvo la intensidad toda la sesion"),
                "recuperacion": ("recupero peor hacia el final" if rec_pct > 5
                                 else "recupero mejor hacia el final" if rec_pct < -5
                                 else "recupero igual toda la sesion"),
            }}


def divergencia(rpe, bloques, df):
    """Normalizada por intensidad y densidad, no por cantidad de bloques."""
    if not bloques:
        return "alineado", 1.0
    inten = float(np.clip((np.mean([b["pct_fcmax"] for b in bloques]) - 75) / 20, 0, 1))
    dens = float(np.clip(sum(b["duracion_seg"] for b in bloques) / max(df["t"].iloc[-1], 1) / 0.65, 0, 1))
    esperado = 1 + 9 * (0.65 * inten + 0.35 * dens)
    d = rpe - esperado
    et = "percibio_mas" if d > 2 else ("percibio_menos" if d < -2 else "alineado")
    return et, round(esperado, 1)


def comparar_historial(metricas, historial):
    if len(historial) < 2:
        return None
    rec_prev = float(np.mean([h["recuperacion_pct"] for h in historial]))
    pico_prev = float(np.mean([h["pico_pct"] for h in historial]))
    rec, pico = metricas["degradacion"]["recuperacion_pct"], metricas["degradacion"]["pico_pct"]
    d_rec, d_pico = abs(rec - rec_prev), abs(pico - pico_prev)
    dato = "recuperacion_entre_bloques" if d_rec >= d_pico else "pico_de_esfuerzo"
    if max(d_rec, d_pico) < 3:
        direccion = "igual"
    elif dato == "recuperacion_entre_bloques":
        direccion = "peor" if rec > rec_prev else "mejor"
    else:
        direccion = "peor" if pico < pico_prev else "mejor"
    return {"sesiones_comparadas": len(historial), "dato_mas_movido": dato,
            "direccion": direccion}
