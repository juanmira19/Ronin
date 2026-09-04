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


# --- Refinamiento de limites con velocidad ---------------------------------


def test_sin_columna_v_el_resultado_es_identico(serie_dos_mitades, fc_max):
    """Invariante 1: sin velocidad, el comportamiento no cambia."""
    assert (detectar_bloques(serie_dos_mitades, fc_max)
            == detectar_bloques(serie_dos_mitades, fc_max, usar_velocidad=False))


def test_velocidad_previa_adelanta_el_inicio(serie_bloque_con_arranque_previo, fc_max):
    con_v = detectar_bloques(serie_bloque_con_arranque_previo, fc_max)
    sin_v = detectar_bloques(serie_bloque_con_arranque_previo, fc_max, usar_velocidad=False)
    assert con_v[0]["inicio_seg"] < sin_v[0]["inicio_seg"]
    assert con_v[0]["duracion_seg"] > sin_v[0]["duracion_seg"]


def test_sin_movimiento_previo_el_adelanto_es_minimo(serie_bloque_sin_arranque_previo,
                                                      serie_bloque_con_arranque_previo, fc_max):
    """Sin movimiento sostenido antes, solo se recupera la muestra de borde que
    el suavizado recorto (5s), no la latencia completa (20s)."""
    def adelanto(df):
        con_v = detectar_bloques(df, fc_max)
        sin_v = detectar_bloques(df, fc_max, usar_velocidad=False)
        return sin_v[0]["inicio_seg"] - con_v[0]["inicio_seg"]

    assert adelanto(serie_bloque_sin_arranque_previo) == 5
    assert adelanto(serie_bloque_con_arranque_previo) == 20


def test_adelanto_acotado_por_la_latencia(fc_max):
    """Aunque haya 200s de movimiento previo, el adelanto se topa en la latencia."""
    from tests.conftest import _serie_v
    df = _serie_v((200, 100, 8.0), (60, 175, 8.0), (60, 100, 0.5))
    con_v = detectar_bloques(df, fc_max, latencia_fc_seg=20)
    sin_v = detectar_bloques(df, fc_max, usar_velocidad=False)
    assert sin_v[0]["inicio_seg"] - con_v[0]["inicio_seg"] <= 20


def test_refinar_no_cambia_pico_ni_intensidad(serie_bloque_con_arranque_previo, fc_max):
    """Invariante 2: el tramo refinado solo agrega muestras con FC bajo el umbral."""
    con_v = detectar_bloques(serie_bloque_con_arranque_previo, fc_max)
    sin_v = detectar_bloques(serie_bloque_con_arranque_previo, fc_max, usar_velocidad=False)
    assert [b["fc_pico"] for b in con_v] == [b["fc_pico"] for b in sin_v]
    assert [b["intensidad"] for b in con_v] == [b["intensidad"] for b in sin_v]


def test_refinar_no_cambia_la_cantidad_de_bloques(serie_intermitente_con_sprints, fc_max):
    con_v = detectar_bloques(serie_intermitente_con_sprints, fc_max)
    sin_v = detectar_bloques(serie_intermitente_con_sprints, fc_max, usar_velocidad=False)
    assert len(con_v) == len(sin_v)


def test_bloques_refinados_no_se_solapan(serie_intermitente_con_sprints, fc_max):
    bloques = detectar_bloques(serie_intermitente_con_sprints, fc_max)
    for anterior, siguiente in zip(bloques, bloques[1:]):
        assert siguiente["inicio_seg"] > anterior["fin_seg"]


def test_velocidad_no_rescata_bloque_bajo_la_duracion_minima(fc_max):
    """La velocidad refina limites, no crea bloques que la FC no vio."""
    from tests.conftest import _serie_v
    df = _serie_v((60, 100, 8.0), (15, 175, 8.0), (60, 100, 0.5))
    assert detectar_bloques(df, fc_max) == []


def test_usar_velocidad_false_ignora_la_columna_v(serie_bloque_con_arranque_previo, fc_max):
    sin_v = detectar_bloques(serie_bloque_con_arranque_previo, fc_max, usar_velocidad=False)
    solo_fc = detectar_bloques(
        serie_bloque_con_arranque_previo[["t", "fc"]].copy(), fc_max)
    assert sin_v == solo_fc
