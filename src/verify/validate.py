"""Validacion de input y verificacion de que el texto generado por el modelo
no cite cifras que el sistema no calculo. Extraido de la celda 16 del notebook
(funcion `validar` y el bloque de verificacion dentro de `run_prototype`)."""

import re

from src.common.constants import SAMPLE_DT


def validar(df, rpe, tipo_sesion, fc_max, cobertura_min=0.90):
    """Si algo falla, error explicito. No se procesa a medias."""
    errores = []
    dur = df["t"].iloc[-1] - df["t"].iloc[0]
    if dur / 60 < 15:
        errores.append(f"Sesion de {dur/60:.1f} min: minimo 15")
    if not (1 <= rpe <= 10):
        errores.append(f"Esfuerzo percibido {rpe} fuera del rango 1-10")
    if df["fc"].max() > fc_max:
        errores.append(f"FC maxima {df.fc.max():.0f} supera la del perfil ({fc_max})")
    cob = len(df) / (dur / SAMPLE_DT + 1)
    if cob < cobertura_min:
        errores.append(f"Serie incompleta: cobertura {cob:.0%}, minimo {cobertura_min:.0%}")
    if tipo_sesion not in {"partido", "entrenamiento", "gimnasio"}:
        errores.append(f"Tipo de sesion invalido: {tipo_sesion}")
    return errores


def cifras_permitidas(metricas, df, rpe, rpe_esperado, historial) -> set[int]:
    """Cifras que el sistema si calculo y por lo tanto el modelo puede citar en su texto."""
    crudos = [metricas["bloques_esfuerzo"]["cantidad"],
              metricas["bloques_esfuerzo"]["duracion_media_seg"],
              *metricas["bloques_esfuerzo"]["distribucion"].values(),
              *[abs(v) for v in metricas["degradacion"].values()],
              len(historial), rpe, rpe_esperado,
              metricas["duracion_sesion_min"], df["t"].iloc[-1],
              1, 10]   # limites de la escala RPE: "8/10" no es una cifra inventada
    for h in historial:
        crudos += [abs(h["pico_pct"]), abs(h["recuperacion_pct"])]
    return {round(abs(float(x))) for x in crudos}


def verificar_cifras(texto: str, permitidos: set[int]) -> list[float]:
    """Devuelve las cifras del texto que no vienen de `permitidos` (tolerancia +-1).
    Lista vacia = el texto no cito nada que el sistema no haya calculado."""
    return [float(m.replace(",", ".")) for m in
            re.findall(r"\d+(?:[.,]\d+)?", texto)
            if not any(abs(float(m.replace(",", ".")) - p) <= 1 for p in permitidos)]
