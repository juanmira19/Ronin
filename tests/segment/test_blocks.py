import pandas as pd

from src.segment.blocks import detectar_bloques, hrr60


def test_serie_plana_no_detecta_bloques(serie_plana, fc_max):
    assert detectar_bloques(serie_plana, fc_max) == []


def test_bloque_claro_se_detecta_con_intensidad_correcta(serie_un_bloque, fc_max):
    bloques = detectar_bloques(serie_un_bloque, fc_max)
    assert len(bloques) == 1
    b = bloques[0]
    assert b["duracion_seg"] >= 30
    assert b["fc_pico"] == 175.0
    assert b["pct_fcmax"] == 87.5
    assert b["intensidad"] == "moderado"  # 0.85 <= 0.875 < 0.92


def test_bloque_corto_se_descarta_por_duracion_minima(serie_bloque_corto, fc_max):
    assert detectar_bloques(serie_bloque_corto, fc_max) == []


def test_bloques_con_hueco_chico_se_fusionan(serie_dos_bloques_gap_chico, fc_max):
    bloques = detectar_bloques(serie_dos_bloques_gap_chico, fc_max)
    assert len(bloques) == 1


def test_bloques_con_hueco_grande_quedan_separados(serie_dos_bloques_gap_grande, fc_max):
    bloques = detectar_bloques(serie_dos_bloques_gap_grande, fc_max)
    assert len(bloques) == 2


def test_intensidad_bajo_moderado_maximo(fc_max):
    # tramos de 60s a 82%, 88% y 96% de fc_max -> bajo / moderado / maximo
    from tests.conftest import _serie
    df = _serie((60, 100), (60, 0.82 * fc_max), (60, 100),
                (60, 0.88 * fc_max), (60, 100),
                (60, 0.96 * fc_max), (60, 100))
    bloques = detectar_bloques(df, fc_max)
    assert [b["intensidad"] for b in bloques] == ["bajo", "moderado", "maximo"]


def test_hrr60_con_datos_suficientes(fc_max):
    from tests.conftest import _serie
    df = _serie((60, 100), (60, 180), (120, 100))
    bloque = detectar_bloques(df, fc_max)[0]
    valor = hrr60(df, bloque)
    assert valor is not None
    assert valor > 0  # la FC baja despues del bloque


def test_hrr60_sin_60s_de_cola_devuelve_none(fc_max):
    from tests.conftest import _serie
    df = _serie((60, 100), (60, 180))  # el bloque termina al final de la serie
    bloque = detectar_bloques(df, fc_max)[0]
    assert hrr60(df, bloque) is None
