"""Fixtures compartidas. Los DataFrames de segment/metrics se arman a mano
(no con generar_sesion) para que las aserciones sean legibles y no dependan
de otro modulo bajo test."""

import numpy as np
import pandas as pd
import pytest

from src.common.constants import SAMPLE_DT

FC_MAX = 200


def _serie(*tramos):
    """Concatena tramos (duracion_seg, fc_constante) en un DataFrame t/fc."""
    fc = []
    for dur_seg, valor in tramos:
        fc += [valor] * (dur_seg // SAMPLE_DT)
    t = np.arange(len(fc)) * SAMPLE_DT
    return pd.DataFrame({"t": t, "fc": fc})


@pytest.fixture
def fc_max():
    return FC_MAX


@pytest.fixture
def serie_plana():
    """Toda la sesion por debajo del umbral: 0 bloques esperados."""
    return _serie((300, 100))


@pytest.fixture
def serie_un_bloque():
    """Un tramo de 60s sobre el 80% de FCmax (moderado), rodeado de reposo."""
    return _serie((60, 100), (60, 175), (60, 100))


@pytest.fixture
def serie_bloque_corto():
    """Tramo sobre umbral pero de solo 15s: por debajo del minimo de 30s."""
    return _serie((60, 100), (15, 175), (60, 100))


@pytest.fixture
def serie_dos_bloques_gap_chico():
    """Dos tramos sobre umbral separados por un hueco de 5s: el suavizado (rolling
    de 15s) hace que el hueco efectivo tras el promedio no baje del umbral -> se
    fusionan en un solo bloque."""
    return _serie((60, 100), (60, 175), (5, 100), (60, 175), (60, 100))


@pytest.fixture
def serie_dos_bloques_gap_grande():
    """Dos tramos sobre umbral separados por un hueco de 30s: incluso con el
    suavizado, el hueco efectivo supera el maximo de fusion -> quedan separados."""
    return _serie((60, 100), (60, 175), (30, 100), (60, 175), (60, 100))


@pytest.fixture
def serie_dos_mitades():
    """Sesion con un bloque maximo en la primera mitad (t=60-115, pico 190) y uno
    moderado en la segunda (t=425-470, pico 170), para tests de calcular_metricas."""
    return _serie((60, 100), (60, 190), (300, 100), (60, 170), (60, 100))
