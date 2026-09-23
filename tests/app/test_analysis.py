"""Tests de la capa de demo. No llaman al modelo: inyectan un interprete falso,
igual que hace `run_prototype` con el parametro `interpretar`."""

import pytest

from app.analysis import analizar, estadisticas_reloj, serie_de, serie_grafica
from app.llm_cache import InterpretacionNoDisponible, clave
from app.presets import SESIONES
from src.interpret.prototype import contract_check
from src.segment.blocks import detectar_bloques


def interprete_falso(payload):
    return {"lectura_sesion": "Hiciste varios bloques y perdiste intensidad al final.",
            "recomendacion_semana": "Repeticiones cortas con descanso completo.",
            "alertas": [], "_fuente": "prueba"}


def interprete_que_inventa_cifras(payload):
    return {"lectura_sesion": "Corriste 7,4 km a ritmo 7:12.",
            "recomendacion_semana": "Descansa.", "alertas": [], "_fuente": "prueba"}


def test_partido_produce_salida_que_cumple_el_contrato():
    r = analizar("partido", 8, "Me senti fuerte al inicio.", interpretar=interprete_falso)
    assert r["estado"] == "ok"
    assert r["contract_check"]["cumple_contrato"] is True
    assert r["metricas"]["bloques_esfuerzo"]["cantidad"] >= 2


def test_corrida_real_se_rechaza_en_segmentacion_sin_llamar_al_modelo():
    def explota(payload):
        raise AssertionError("el modelo no deberia llamarse en una sesion rechazada")

    r = analizar("corrida", 6, "corrida de prueba", interpretar=explota)
    assert r["estado"] == "rechazada"
    assert r["etapa_fallida"] == "segmentacion"


def test_sesion_corta_se_rechaza_en_validacion():
    def explota(payload):
        raise AssertionError("el modelo no deberia llamarse")

    r = analizar("incompleta", 8, "corta", interpretar=explota)
    assert r["estado"] == "rechazada"
    assert r["etapa_fallida"] == "validacion"
    assert "15" in r["salida"]["error"][0]


def test_la_verificacion_de_cifras_descarta_texto_con_numeros_ajenos():
    r = analizar("partido", 8, "nota", interpretar=interprete_que_inventa_cifras)
    assert r["verificacion"]["texto_descartado"] is True
    assert r["verificacion"]["cifras_intrusas"]
    assert "descartado" in r["salida"]["lectura_sesion"]


def test_sin_modelo_y_sin_cache_no_se_inventa_interpretacion():
    def sin_modelo(payload):
        raise InterpretacionNoDisponible("sin red y sin cache")

    r = analizar("partido", 8, "nota", interpretar=sin_modelo)
    assert r["estado"] == "sin_interpretacion"
    assert r["salida"] is None
    assert r["metricas"] is not None  # lo deterministico sigue disponible


def test_la_clave_de_cache_depende_del_rpe_y_de_la_nota():
    base = {"REPORTE_DEL_JUGADOR": {"esfuerzo_percibido": 8, "nota": "a"}}
    otra_nota = {"REPORTE_DEL_JUGADOR": {"esfuerzo_percibido": 8, "nota": "b"}}
    otro_rpe = {"REPORTE_DEL_JUGADOR": {"esfuerzo_percibido": 9, "nota": "a"}}
    assert clave(base) != clave(otra_nota) != clave(otro_rpe)


def test_estadisticas_reloj_usan_la_distancia_del_export_cuando_existe():
    df = serie_de("corrida")
    r = estadisticas_reloj(df, SESIONES["corrida"])
    assert r["fuente_distancia"] == "export"
    assert 0 < r["distancia_km"] < 10


def test_la_grafica_no_excede_el_tope_de_puntos_y_trae_los_bloques():
    df = serie_de("partido")
    bloques = detectar_bloques(df, 192)
    g = serie_grafica(df, bloques)
    assert len(g["t"]) == len(g["fc"]) <= 700
    assert len(g["bloques"]) == len(bloques)
    assert all(b["fin_seg"] > b["inicio_seg"] for b in g["bloques"])


@pytest.mark.parametrize("sesion_id", list(SESIONES))
def test_toda_sesion_del_catalogo_carga_y_responde(sesion_id):
    r = analizar(sesion_id, 7, "nota", interpretar=interprete_falso)
    assert r["estado"] in {"ok", "rechazada"}
    assert r["grafica"]["t"] and r["reloj"]["duracion_min"] > 0


def test_preguntar_parte_de_la_misma_lectura_y_las_mismas_cifras():
    from app.analysis import preguntar

    vistas = {}

    def responder_falso(entrada):
        vistas["entrada"] = entrada
        return {"respuesta": "Guarda tu ultimo corte para el final.", "_fuente": "prueba"}

    r = preguntar("partido", 8, "nota", "proximo",
                  interpretar=interprete_falso, responder=responder_falso)
    assert r["respuesta"] == "Guarda tu ultimo corte para el final."
    assert vistas["entrada"]["LECTURA_YA_MOSTRADA"] == interprete_falso({})["lectura_sesion"]
    assert "METRICAS" in vistas["entrada"]


def test_no_se_pregunta_sobre_una_sesion_rechazada():
    from app.analysis import preguntar

    with pytest.raises(InterpretacionNoDisponible):
        preguntar("incompleta", 8, "nota", "proximo", interpretar=interprete_falso,
                  responder=lambda e: {"respuesta": "no deberia llegar"})
