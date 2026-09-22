"""La API expone exactamente lo que la pagina necesita, y valida su entrada."""

from fastapi.testclient import TestClient

from app.server import app

cliente = TestClient(app)


def test_catalogo_lista_las_tres_sesiones_y_las_notas_de_los_evals():
    r = cliente.get("/api/catalogo")
    assert r.status_code == 200
    d = r.json()
    assert {s["id"] for s in d["sesiones"]} == {"partido", "corrida", "incompleta"}
    assert len(d["notas"]) == 4


def test_sesion_desconocida_devuelve_404():
    r = cliente.post("/api/analizar", json={"sesion_id": "no_existe"})
    assert r.status_code == 404


def test_rpe_fuera_de_rango_lo_rechaza_la_api_antes_del_pipeline():
    r = cliente.post("/api/analizar", json={"sesion_id": "partido", "esfuerzo_percibido": 42})
    assert r.status_code == 422


def test_sesion_rechazada_no_necesita_modelo_ni_cache():
    r = cliente.post("/api/analizar", json={"sesion_id": "incompleta", "nota": "x", "modo": "cache"})
    assert r.status_code == 200
    assert r.json()["estado"] == "rechazada"


def test_la_pagina_se_sirve_en_la_raiz():
    r = cliente.get("/")
    assert r.status_code == 200 and "RONIN" in r.text
