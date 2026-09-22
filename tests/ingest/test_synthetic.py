import numpy as np

from src.ingest.synthetic import generar_export_sintetico_partido, generar_sesion


def test_generar_sesion_es_determinista_con_seed_fija():
    df1, verdad1 = generar_sesion(seed=1)
    df2, verdad2 = generar_sesion(seed=1)
    assert df1.equals(df2)
    assert verdad1 == verdad2


def test_generar_sesion_duracion_coherente():
    df, _ = generar_sesion(duracion_min=30, seed=1)
    assert df["t"].iloc[-1] <= 30 * 60
    assert df["t"].iloc[-1] > 29 * 60  # deberia usar casi toda la duracion pedida


def test_generar_sesion_fc_en_rango():
    fc_max = 190
    df, _ = generar_sesion(duracion_min=20, fc_max=fc_max, seed=1)
    assert df["fc"].min() >= 60
    assert df["fc"].max() <= fc_max


def test_generar_export_sintetico_es_determinista_con_seed_fija():
    export1 = generar_export_sintetico_partido(seed=3)
    export2 = generar_export_sintetico_partido(seed=3)
    assert export1 == export2


def test_generar_export_sintetico_timestamps_estrictamente_crecientes():
    export = generar_export_sintetico_partido(seed=3)
    hr_t = [m["t"] for m in export["heart_rate"]]
    sp_t = [p["t"] for p in export["route_speed"]]
    assert all(b > a for a, b in zip(hr_t, hr_t[1:]))
    assert all(b > a for a, b in zip(sp_t, sp_t[1:]))


def test_generar_export_sintetico_duracion_coherente_con_timestamps():
    export = generar_export_sintetico_partido(seed=3)
    max_hr = export["heart_rate"][-1]["t"]
    max_sp = export["route_speed"][-1]["t"]
    assert export["duracion_seg"] == max(max_hr, max_sp)
