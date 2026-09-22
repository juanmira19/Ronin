import pandas as pd

from src.verify.validate import cifras_permitidas, validar, verificar_cifras


def _df_valido(minutos=20):
    n = minutos * 12  # SAMPLE_DT=5s -> 12 muestras/min
    return pd.DataFrame({"t": [i * 5 for i in range(n)], "fc": [140.0] * n})


def test_validar_sesion_corta_da_error():
    df = _df_valido(10)
    errores = validar(df, rpe=5, tipo_sesion="partido", fc_max=190)
    assert any("minimo 15" in e for e in errores)


def test_validar_rpe_fuera_de_rango_da_error():
    df = _df_valido()
    errores = validar(df, rpe=11, tipo_sesion="partido", fc_max=190)
    assert any("fuera del rango 1-10" in e for e in errores)


def test_validar_fc_supera_perfil_da_error():
    df = _df_valido()
    df.loc[0, "fc"] = 250
    errores = validar(df, rpe=5, tipo_sesion="partido", fc_max=190)
    assert any("supera la del perfil" in e for e in errores)


def test_validar_cobertura_insuficiente_da_error():
    df = _df_valido()
    df = df.iloc[::3].reset_index(drop=True)  # deja solo 1 de cada 3 muestras
    errores = validar(df, rpe=5, tipo_sesion="partido", fc_max=190)
    assert any("cobertura" in e for e in errores)


def test_validar_tipo_sesion_invalido_da_error():
    df = _df_valido()
    errores = validar(df, rpe=5, tipo_sesion="siesta", fc_max=190)
    assert any("Tipo de sesion invalido" in e for e in errores)


def test_validar_caso_valido_no_da_errores():
    df = _df_valido()
    assert validar(df, rpe=5, tipo_sesion="partido", fc_max=190) == []


def test_cifras_permitidas_incluye_metricas_rpe_e_historial():
    metricas = {
        "bloques_esfuerzo": {"cantidad": 3, "duracion_media_seg": 45,
                              "distribucion": {"bajo": 1, "moderado": 1, "maximo": 1}},
        "degradacion": {"pico_pct": -5.0, "recuperacion_pct": 10.0},
        "duracion_sesion_min": 60,
    }
    df = pd.DataFrame({"t": [0, 3600], "fc": [100, 150]})
    historial = [{"pico_pct": 2.0, "recuperacion_pct": 3.0}]
    permitidos = cifras_permitidas(metricas, df, rpe=7, rpe_esperado=6.5, historial=historial)
    for esperado in {3, 45, 1, 5, 10, 1, 7, 7, 60, 3600, 2, 3}:
        assert esperado in permitidos


def test_verificar_cifras_texto_limpio_no_reporta_nada():
    permitidos = {3, 45, 60}
    texto = "Hiciste 3 bloques de unos 45 segundos en 60 minutos."
    assert verificar_cifras(texto, permitidos) == []


def test_verificar_cifras_detecta_numero_ajeno():
    permitidos = {3, 45, 60}
    texto = "Hiciste 3 bloques pero corriste 12 km."
    intrusas = verificar_cifras(texto, permitidos)
    assert 12.0 in intrusas


def test_verificar_cifras_tolera_diferencia_de_uno():
    permitidos = {45}
    texto = "El bloque duro 44 segundos."
    assert verificar_cifras(texto, permitidos) == []
