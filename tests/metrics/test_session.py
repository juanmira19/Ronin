import pytest

from src.segment.blocks import detectar_bloques
from src.metrics.session import calcular_metricas, comparar_historial, divergencia


def test_calcular_metricas_requiere_al_menos_dos_bloques(serie_un_bloque, fc_max):
    bloques = detectar_bloques(serie_un_bloque, fc_max)
    assert len(bloques) == 1
    with pytest.raises(ValueError):
        calcular_metricas(serie_un_bloque, bloques, fc_max)


def test_calcular_metricas_degradacion_y_conclusiones(serie_dos_mitades, fc_max):
    bloques = detectar_bloques(serie_dos_mitades, fc_max)
    m = calcular_metricas(serie_dos_mitades, bloques, fc_max)

    assert m["bloques_esfuerzo"]["cantidad"] == 2
    dist = m["bloques_esfuerzo"]["distribucion"]
    assert sum(dist.values()) == m["bloques_esfuerzo"]["cantidad"]

    # pico baja de 190 (1a mitad) a 170 (2a mitad) -> degradacion negativa
    assert m["degradacion"]["pico_pct"] < -2
    assert m["conclusiones"]["pico"] == "perdio intensidad en la segunda mitad"
    assert m["conclusiones"]["recuperacion"] == "recupero peor hacia el final"


def test_divergencia_sin_bloques_es_alineada(serie_plana):
    assert divergencia(5, [], serie_plana) == ("alineado", 1.0)


def test_divergencia_rpe_muy_alto_es_percibio_mas(serie_dos_mitades, fc_max):
    bloques = detectar_bloques(serie_dos_mitades, fc_max)
    etiqueta, esperado = divergencia(9, bloques, serie_dos_mitades)
    assert etiqueta == "percibio_mas"
    assert 9 - esperado > 2


def test_divergencia_rpe_muy_bajo_es_percibio_menos(serie_dos_mitades, fc_max):
    bloques = detectar_bloques(serie_dos_mitades, fc_max)
    etiqueta, esperado = divergencia(1, bloques, serie_dos_mitades)
    assert etiqueta == "percibio_menos"
    assert 1 - esperado < -2


def test_divergencia_rpe_alineado(serie_dos_mitades, fc_max):
    bloques = detectar_bloques(serie_dos_mitades, fc_max)
    _, esperado = divergencia(5, bloques, serie_dos_mitades)
    etiqueta, _ = divergencia(round(esperado), bloques, serie_dos_mitades)
    assert etiqueta == "alineado"


def test_comparar_historial_con_menos_de_dos_sesiones_es_none():
    metricas = {"degradacion": {"pico_pct": 0.0, "recuperacion_pct": 0.0}}
    assert comparar_historial(metricas, []) is None
    assert comparar_historial(metricas, [{"pico_pct": 1.0, "recuperacion_pct": 1.0}]) is None


def test_comparar_historial_detecta_direccion_peor():
    historial = [{"pico_pct": 0.0, "recuperacion_pct": 0.0},
                 {"pico_pct": 0.0, "recuperacion_pct": 0.0}]
    # la recuperacion actual empeoro mucho mas que el pico -> dato_mas_movido = recuperacion
    metricas = {"degradacion": {"pico_pct": 1.0, "recuperacion_pct": 20.0}}
    resultado = comparar_historial(metricas, historial)
    assert resultado["sesiones_comparadas"] == 2
    assert resultado["dato_mas_movido"] == "recuperacion_entre_bloques"
    assert resultado["direccion"] == "peor"


def test_comparar_historial_direccion_igual_si_cambio_es_chico():
    historial = [{"pico_pct": 0.0, "recuperacion_pct": 0.0},
                 {"pico_pct": 0.0, "recuperacion_pct": 0.0}]
    metricas = {"degradacion": {"pico_pct": 1.0, "recuperacion_pct": 1.0}}
    resultado = comparar_historial(metricas, historial)
    assert resultado["direccion"] == "igual"
