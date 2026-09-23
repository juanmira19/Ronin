"""Las preguntas sugeridas no llaman al modelo en los tests: se inyecta un
redactor falso, igual que en la lectura."""

from src.interpret.preguntas import PREGUNTAS, entrada_pregunta, responder_pregunta

PAYLOAD = {"METRICAS": {"bloques_esfuerzo": {"cantidad": 13}},
           "REPORTE_DEL_JUGADOR": {"esfuerzo_percibido": 8, "nota": "me costo al final"}}


def test_la_entrada_es_el_mismo_paquete_mas_lectura_y_pregunta():
    e = entrada_pregunta(PAYLOAD, "lectura", "proximo")
    assert e["METRICAS"] == PAYLOAD["METRICAS"]
    assert e["LECTURA_YA_MOSTRADA"] == "lectura"
    assert e["PREGUNTA_DEL_JUGADOR"] == PREGUNTAS["proximo"]


def test_respuesta_con_cifras_del_sistema_se_muestra():
    r = responder_pregunta(PAYLOAD, "lectura", "entreno", {13},
                           responder=lambda e: {"respuesta": "Hiciste 13 esfuerzos."})
    assert r["respuesta"] == "Hiciste 13 esfuerzos."
    assert r["descartada"] is False
    assert r["pregunta"] == PREGUNTAS["entreno"]


def test_respuesta_con_una_cifra_inventada_se_descarta_entera():
    r = responder_pregunta(PAYLOAD, "lectura", "proximo", {13},
                           responder=lambda e: {"respuesta": "Haz 8 series de 30 segundos."})
    assert r["respuesta"] is None
    assert r["descartada"] is True
    assert r["cifras_intrusas"]
