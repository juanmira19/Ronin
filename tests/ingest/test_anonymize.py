import json

from src.ingest.anonymize import anonymize_dict


def _raw_workout(**overrides):
    base = {
        "start": "2026-01-01 10:00:00",
        "name": "Partido Ultimate",
        "duration": 3000,  # tiempo activo, excluye auto-pausa
        "isIndoor": False,
        "heartRateData": [
            {"date": "2026-01-01 10:00:00", "Avg": 100},
            {"date": "2026-01-01 10:01:00", "Avg": 150},
        ],
        "route": [
            {"timestamp": "2026-01-01 10:00:00", "speed": 2.0, "lat": 19.4, "lon": -99.1},
            {"timestamp": "2026-01-01 10:01:00", "speed": 5.0, "lat": 19.5, "lon": -99.2},
        ],
        "walkingAndRunningDistance": [
            {"date": "2026-01-01 10:00:00", "qty": 0.0},
            # timestamp mas alla del "duration" activo: hubo auto-pausa
            {"date": "2026-01-01 11:00:00", "qty": 1.2},
        ],
    }
    base.update(overrides)
    return {"data": {"workouts": [base]}}


def test_anonymize_quita_lat_lon():
    anon = anonymize_dict(_raw_workout())
    assert "lat" not in json.dumps(anon["route_speed"])
    assert "lon" not in json.dumps(anon["route_speed"])
    assert anon["route_speed"] == [{"t": 0, "speed_kmh": 7.2}, {"t": 60, "speed_kmh": 18.0}]


def test_anonymize_timestamps_relativos_al_inicio():
    anon = anonymize_dict(_raw_workout())
    assert anon["heart_rate"] == [{"t": 0, "bpm": 100.0}, {"t": 60, "bpm": 150.0}]


def test_anonymize_duracion_usa_maximo_timestamp_no_duration_activo():
    anon = anonymize_dict(_raw_workout())
    # el ultimo timestamp real (distancia, tras auto-pausa) es 3600s, muy por
    # encima del "duration" activo (3000s) reportado por Health Auto Export
    assert anon["duracion_activa_seg"] == 3000
    assert anon["duracion_seg"] == 3600


def test_anonymize_es_outdoor():
    anon_outdoor = anonymize_dict(_raw_workout(isIndoor=False))
    anon_indoor = anonymize_dict(_raw_workout(isIndoor=True))
    assert anon_outdoor["es_outdoor"] is True
    assert anon_indoor["es_outdoor"] is False
