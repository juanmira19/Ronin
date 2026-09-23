"""La FCmax del perfil es un dato medido, no una hipotesis. Estos tests fijan
las tres propiedades que lo hacen usable: robustez ante picos del sensor,
compatibilidad con el perfil declarado, y honestidad cuando hay pocas sesiones."""

import numpy as np
import pandas as pd
import pytest

from src.perfil.fcmax import (MIN_SESIONES_CONFIABLE, estimar_fcmax, fcmax_observada,
                              resolver_fcmax)
from src.segment.blocks import detectar_bloques


def _serie(valores):
    return pd.DataFrame({"t": np.arange(len(valores)) * 5, "fc": [float(v) for v in valores]})


def test_un_pico_espurio_del_sensor_no_fija_la_fcmax():
    """Una sola muestra de 210 en alguien que llega a 180 inflaria el umbral un
    12% y borraria bloques reales. El suavizado tiene que absorberla."""
    limpia = _serie([180] * 40)
    con_pico = _serie([180] * 20 + [210] + [180] * 19)
    dos_picos = _serie([180] * 20 + [210, 208] + [180] * 18)
    assert con_pico["fc"].max() == 210  # el maximo crudo si se contamina
    assert fcmax_observada(con_pico) == fcmax_observada(limpia)
    assert fcmax_observada(dos_picos) == fcmax_observada(limpia)


def test_la_fcmax_observada_sube_con_el_esfuerzo_real_sostenido():
    """Lo contrario del test anterior: un esfuerzo real (no un pico de una
    muestra) si tiene que mover la FCmax del perfil."""
    antes = fcmax_observada(_serie([160] * 40))
    despues = fcmax_observada(_serie([160] * 20 + [195] * 20))  # 100 s a 195
    assert despues > antes + 25


def test_con_pocas_sesiones_la_estimacion_se_marca_provisional():
    assert estimar_fcmax([185.0]) ["provisional"] is True
    assert estimar_fcmax([185.0] * MIN_SESIONES_CONFIABLE)["provisional"] is False


def test_la_fcmax_es_el_maximo_del_historial_no_el_promedio():
    r = estimar_fcmax([170.0, 188.0, 175.0])
    assert r["fc_max"] == 188.0 and r["fuente"] == "observada" and r["sesiones"] == 3


def test_sin_ninguna_observacion_falla_explicito_en_vez_de_inventar_un_numero():
    with pytest.raises(ValueError):
        estimar_fcmax([])


def test_el_perfil_que_declara_fcmax_manda_sobre_la_derivada():
    """Compatibilidad: los evals fijan fc_max a proposito para que el umbral no
    se mueva entre corridas."""
    df = _serie([150] * 40)
    r = resolver_fcmax({"fc_max": 192}, df)
    assert r == {"fc_max": 192.0, "fuente": "declarada", "sesiones": None, "provisional": False}


def test_sin_fcmax_declarada_se_deriva_del_historial_mas_la_sesion_actual():
    df = _serie([150] * 20 + [196] * 20)
    r = resolver_fcmax({"fcmax_observadas": [180.0, 182.0]}, df)
    assert r["fuente"] == "observada" and r["sesiones"] == 3
    assert r["fc_max"] > 190  # la sesion actual aporta el nuevo techo


def test_una_fcmax_equivocada_por_arriba_borra_bloques_reales():
    """Documenta por que esto importa: es la razon de ser del modulo."""
    serie = _serie(([100] * 12 + [170] * 12) * 8)
    assert len(detectar_bloques(serie, 190)) > len(detectar_bloques(serie, 215))
