import json
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from src.ingest.apple_health_xml import (WorkoutMeta, agrupar_tramos, iter_workouts_elegibles,
                                         onboarding)
from src.ingest.health_auto_export import load_session

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


# --- Onboarding ------------------------------------------------------------
_DISC = "HKWorkoutActivityTypeDiscSports"


def _w(inicio, fin, tipo=_DISC, fuente="Watch"):
    return (f'<Workout workoutActivityType="{tipo}" duration="0" sourceName="{fuente}" '
            f'startDate="2026-09-04 {inicio} -0500" endDate="2026-09-04 {fin} -0500"/>')


def _fc(hora, bpm, fuente="Watch"):
    return (f'<Record type="HKQuantityTypeIdentifierHeartRate" sourceName="{fuente}" unit="count/min" '
            f'startDate="2026-09-04 {hora} -0500" endDate="2026-09-04 {hora} -0500" value="{bpm}"/>')


def _dist(inicio, fin, valor, fuente="Watch", unidad="km"):
    return (f'<Record type="HKQuantityTypeIdentifierDistanceWalkingRunning" sourceName="{fuente}" '
            f'unit="{unidad}" startDate="2026-09-04 {inicio} -0500" '
            f'endDate="2026-09-04 {fin} -0500" value="{valor}"/>')


def _export_zip(tmp_path, *elementos):
    """Zip con la misma estructura que el de Apple Salud. Los <Record> van antes
    que los <Workout>, como en el export real."""
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<HealthData>\n' + "\n".join(elementos) + "\n</HealthData>"
    path = tmp_path / "export.zip"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("apple_health_export/export.xml", xml)
        z.writestr("apple_health_export/export_cda.xml", "<ClinicalDocument/>")
    return path


def _meta(inicio_min, fin_min, tipo=_DISC, fuente="Watch"):
    base = datetime(2026, 9, 4, 17, 0, tzinfo=timezone(timedelta(hours=-5)))
    return WorkoutMeta(tipo, base + timedelta(minutes=inicio_min),
                       base + timedelta(minutes=fin_min), fin_min - inicio_min, fuente)


def test_agrupar_une_tramos_con_pausa_corta_y_separa_el_calentamiento():
    calentamiento, parte1, parte2 = _meta(-50, -40), _meta(0, 19), _meta(19.5, 51)
    partidos = agrupar_tramos([parte2, calentamiento, parte1], pausa_max_seg=300)
    assert [len(p.tramos) for p in partidos] == [1, 2]
    assert partidos[1].duracion_min == pytest.approx(51)


def test_agrupar_no_une_workouts_de_otro_reloj():
    partidos = agrupar_tramos([_meta(0, 19), _meta(19.5, 51, fuente="Otro reloj")], pausa_max_seg=300)
    assert len(partidos) == 2


def test_onboarding_devuelve_solo_partidos_y_cuenta_lo_descartado(tmp_path):
    path = _export_zip(
        tmp_path,
        _fc("17:00:05", 150), _fc("17:10:00", 170), _fc("17:40:00", 160),
        _w("07:00:00", "07:40:00", tipo="HKWorkoutActivityTypeRunning"),
        _w("08:00:00", "09:00:00", tipo="HKWorkoutActivityTypeCycling"),
        _w("16:10:00", "16:19:00"),                         # calentamiento: corto
        _w("17:00:00", "17:19:00"), _w("17:19:20", "17:51:00"),
    )
    r = onboarding(path)
    assert len(r["partidos"]) == 1
    assert len(r["partidos"][0]["partido"].tramos) == 2
    assert r["descartados"] == {"no_son_partidos": 2, "demasiado_cortos": 1,
                                "sin_frecuencia_cardiaca": 0}


def test_onboarding_arma_la_serie_anonimizada(tmp_path):
    path = _export_zip(
        tmp_path,
        _fc("17:00:10", 150), _fc("17:20:00", 170),
        _fc("17:10:00", 199, fuente="iPhone"),              # otro dispositivo: fuera
        _fc("12:00:00", 80),                                # fuera del partido
        _dist("17:00:00", "17:01:00", 0.1),
        _dist("17:01:00", "17:02:00", 200, unidad="m"),
        _dist("17:00:00", "17:02:00", 0.5, fuente="iPhone"),  # duplicaria la distancia
        _w("17:00:00", "17:30:00"),
    )
    sesion = onboarding(path)["partidos"][0]["sesion"]
    assert sesion["duracion_seg"] == 1800
    assert sesion["heart_rate"] == [{"t": 10, "bpm": 150.0}, {"t": 1200, "bpm": 170.0}]
    assert sesion["distance_km"] == [{"t": 60, "km": 0.1}, {"t": 120, "km": 0.2}]
    # sin fechas absolutas ni nombres de dispositivo
    texto = json.dumps(sesion)
    assert "2026" not in texto and "Watch" not in texto


def test_la_sesion_del_onboarding_la_lee_load_session(tmp_path):
    path = _export_zip(tmp_path, _fc("17:00:00", 150), _fc("17:30:00", 160),
                       _dist("17:00:00", "17:01:00", 0.1), _dist("17:01:00", "17:02:00", 0.2),
                       _w("17:00:00", "17:30:00"))
    sesion = onboarding(path)["partidos"][0]["sesion"]
    archivo = tmp_path / "partido.json"
    archivo.write_text(json.dumps(sesion), encoding="utf-8")
    df = load_session(archivo)
    assert df["t"].iloc[-1] == 1800
    assert df.loc[df["t"] == 120, "v"].item() == pytest.approx(12.0)  # 0,2 km en 60 s


def test_onboarding_rechaza_un_archivo_que_no_es_el_export(tmp_path):
    path = tmp_path / "otra_cosa.zip"
    path.write_bytes(b"no soy un zip")
    with pytest.raises(ValueError):
        onboarding(path)
    sin_xml = tmp_path / "vacio.zip"
    with zipfile.ZipFile(sin_xml, "w") as z:
        z.writestr("fotos/uno.jpg", b"")
    with pytest.raises(ValueError):
        onboarding(sin_xml)
