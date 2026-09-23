"""La API expone exactamente lo que la pagina necesita, y valida su entrada."""

import pytest
from fastapi.testclient import TestClient

from app import presets
from app.server import app
from tests.test_apple_health_xml import _export_zip, _fc, _w

cliente = TestClient(app)


def test_catalogo_lista_las_tres_sesiones_y_las_notas_de_los_evals():
    r = cliente.get("/api/catalogo")
    assert r.status_code == 200
    d = r.json()
    # subconjunto: los partidos que el jugador importo tambien entran al catalogo
    assert {"partido", "corrida", "incompleta"} <= {s["id"] for s in d["sesiones"]}
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


@pytest.fixture
def importadas_en_tmp(tmp_path, monkeypatch):
    """Lo importado va a tmp y sale del catalogo al terminar: el test no toca
    data/raw ni deja sesiones colgadas para los demas tests."""
    monkeypatch.setattr(presets, "IMPORTADAS", tmp_path / "importadas")
    antes = dict(presets.SESIONES)
    yield tmp_path
    presets.SESIONES.clear()
    presets.SESIONES.update(antes)


def test_onboarding_agrega_solo_los_partidos_al_catalogo(importadas_en_tmp):
    fc = [_fc(f"17:{m:02d}:00", 120 + (m % 5) * 12) for m in range(0, 50)]
    path = _export_zip(importadas_en_tmp, *fc,
                       _w("07:00:00", "07:40:00", tipo="HKWorkoutActivityTypeRunning"),
                       _w("17:00:00", "17:20:00"), _w("17:20:30", "17:50:00"))
    r = cliente.post("/api/onboarding", content=path.read_bytes(),
                     headers={"Content-Type": "application/zip"})
    assert r.status_code == 200
    d = r.json()
    assert [p["id"] for p in d["partidos"]] == ["real_20260904_1700"]
    assert d["partidos"][0]["fecha"] == "viernes 4 sep, 5:00 p. m."
    assert d["descartados"]["no_son_partidos"] == 1
    assert "archivo" not in d["partidos"][0]  # la ruta local no es asunto de la pagina

    ids = {s["id"] for s in cliente.get("/api/catalogo").json()["sesiones"]}
    assert "real_20260904_1700" in ids
    r = cliente.post("/api/analizar", json={"sesion_id": "real_20260904_1700", "modo": "cache"})
    assert r.status_code == 200


def test_onboarding_rechaza_lo_que_no_es_un_export(importadas_en_tmp):
    r = cliente.post("/api/onboarding", content=b"no soy un zip",
                     headers={"Content-Type": "application/zip"})
    assert r.status_code == 400


def test_pregunta_desconocida_devuelve_404():
    r = cliente.post("/api/preguntar", json={"sesion_id": "partido", "pregunta_id": "no_existe"})
    assert r.status_code == 404


def test_pregunta_sin_modelo_ni_cache_no_inventa_respuesta(monkeypatch, tmp_path):
    from app import llm_cache
    monkeypatch.setattr(llm_cache, "CACHE_DIR", tmp_path)  # cache vacia
    r = cliente.post("/api/preguntar", json={"sesion_id": "partido", "pregunta_id": "proximo",
                                             "nota": "x", "modo": "cache"})
    assert r.status_code == 200
    assert r.json()["disponible"] is False


def test_el_catalogo_trae_las_preguntas_sugeridas():
    d = cliente.get("/api/catalogo").json()
    assert {q["id"] for q in d["preguntas"]} == {"proximo", "cancha", "entreno"}
