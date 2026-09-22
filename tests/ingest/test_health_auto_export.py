import json

import numpy as np

from src.common.constants import SAMPLE_DT
from src.ingest.health_auto_export import _es_crudo, load_session
from src.ingest.synthetic import generar_export_sintetico_partido


def test_es_crudo_detecta_formato_health_auto_export():
    assert _es_crudo({"data": {"workouts": [{}]}}) is True


def test_es_crudo_false_para_dict_ya_anonimizado():
    assert _es_crudo({"tipo_sesion": "partido", "heart_rate": []}) is False


def test_load_session_malla_regular_con_export_sintetico_realista(tmp_path):
    export = generar_export_sintetico_partido(seed=11)
    path = tmp_path / "export.json"
    path.write_text(json.dumps(export), encoding="utf-8")

    df = load_session(path)

    assert list(df.columns[:2]) == ["t", "fc"]
    # malla regular cada SAMPLE_DT segundos, desde 0 hasta la duracion
    assert np.array_equal(df["t"].to_numpy(), np.arange(0, export["duracion_seg"] + SAMPLE_DT, SAMPLE_DT))
    assert "v" in df.columns
    assert df["v"].min() >= 0
    assert df.attrs["tipo_sesion"] == export["tipo_sesion"]
    assert df.attrs["fuente_velocidad"] == "route_speed"


def test_load_session_deriva_velocidad_de_distancia_sin_gps(tmp_path):
    anon = {
        "tipo_sesion": "partido",
        "duracion_seg": 120,
        "heart_rate": [{"t": 0, "bpm": 100}, {"t": 120, "bpm": 140}],
        "route_speed": [],
        "distance_km": [{"t": 0, "km": 0.0}, {"t": 60, "km": 0.5}, {"t": 120, "km": 1.0}],
    }
    path = tmp_path / "export.json"
    path.write_text(json.dumps(anon), encoding="utf-8")

    df = load_session(path)

    assert "v" in df.columns
    assert df.attrs["fuente_velocidad"] == "distance_km (derivada)"
    assert (df["v"] >= 0).all()


def test_load_session_reporta_huecos_interpolados(tmp_path):
    """La FC de un hueco se sigue interpolando, pero el pipeline debe saber que
    ese tramo es reconstruido y no medido."""
    anon = {
        "tipo_sesion": "partido",
        "duracion_seg": 600,
        # un solo hueco largo: 180s entre t=60 y t=240. El resto va cada 60s,
        # que no supera GAP_INTERPOLADO_SEG.
        "heart_rate": [{"t": t, "bpm": 140} for t in
                       (0, 60, 240, 300, 360, 420, 480, 540, 600)],
        "route_speed": [],
        "distance_km": [],
    }
    path = tmp_path / "export.json"
    path.write_text(json.dumps(anon), encoding="utf-8")

    df = load_session(path)

    assert df.attrs["huecos_interpolados"] == [{"t": 60, "dur_seg": 180}]
    assert df.attrs["frac_interpolada"] == 180 / 600


def test_load_session_sin_huecos_reporta_fraccion_cero(tmp_path):
    export = generar_export_sintetico_partido(seed=11)
    path = tmp_path / "export.json"
    path.write_text(json.dumps(export), encoding="utf-8")

    df = load_session(path)

    assert df.attrs["huecos_interpolados"] == []
    assert df.attrs["frac_interpolada"] == 0.0


def test_load_session_sin_velocidad_no_agrega_columna_v(tmp_path):
    anon = {
        "tipo_sesion": "partido",
        "duracion_seg": 60,
        "heart_rate": [{"t": 0, "bpm": 100}, {"t": 60, "bpm": 120}],
        "route_speed": [],
        "distance_km": [],
    }
    path = tmp_path / "export.json"
    path.write_text(json.dumps(anon), encoding="utf-8")

    df = load_session(path)

    assert "v" not in df.columns
    assert df.attrs["fuente_velocidad"] is None
