from pathlib import Path

from src.ingest.apple_health_xml import iter_workouts_elegibles

FIXTURE = Path(__file__).parent / "fixtures" / "mini_export.xml"


def test_filtra_solo_tipos_elegibles():
    resultados = list(iter_workouts_elegibles(FIXTURE))
    tipos = [w.tipo for w in resultados]
    assert tipos == ["HKWorkoutActivityTypeRunning", "HKWorkoutActivityTypeDiscSports"]


def test_descarta_ciclismo_fuerza_y_caminata():
    resultados = list(iter_workouts_elegibles(FIXTURE))
    assert all(w.tipo in {"HKWorkoutActivityTypeRunning", "HKWorkoutActivityTypeDiscSports"}
               for w in resultados)
    assert len(resultados) == 2


def test_campos_del_workout():
    resultados = list(iter_workouts_elegibles(FIXTURE))
    running = resultados[0]
    assert running.duracion_min == 15.5
    assert running.fuente == "Test Watch"
    assert running.inicio.isoformat() == "2026-01-02T07:00:00-05:00"
    assert running.fin.isoformat() == "2026-01-02T07:15:30-05:00"
