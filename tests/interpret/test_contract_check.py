from src.interpret.prototype import contract_check


def _output_valido(**overrides):
    base = {
        "lectura_sesion": "Buen partido, bajaste intensidad en la segunda mitad.",
        "bloques_esfuerzo": {"cantidad": 2, "duracion_media_seg": 50,
                              "distribucion": {"bajo": 0, "moderado": 1, "maximo": 1}},
        "degradacion": {"pico_pct": -10.5, "recuperacion_pct": 22.2},
        "comparacion_historial": None,
        "divergencia_percepcion": "alineado",
        "recomendacion_semana": "Prioriza recuperacion activa esta semana.",
        "alertas": [],
        "requiere_revision": False,
    }
    base.update(overrides)
    return base


def test_contract_check_output_valido_cumple_contrato():
    resultado = contract_check(_output_valido())
    assert resultado["cumple_contrato"] is True
    assert resultado["faltantes"] == []
    assert resultado["extras"] == []


def test_contract_check_output_con_error():
    resultado = contract_check({"error": ["Sesion demasiado corta"]})
    assert resultado["cumple_contrato"] is False
    assert resultado["campos_recibidos"] == ["error"]
    assert resultado["motivo"] == ["Sesion demasiado corta"]


def test_contract_check_distribucion_no_suma_cantidad_falla():
    output = _output_valido(bloques_esfuerzo={
        "cantidad": 2, "duracion_media_seg": 50,
        "distribucion": {"bajo": 0, "moderado": 1, "maximo": 0},  # suma 1, no 2
    })
    resultado = contract_check(output)
    assert resultado["distribucion_suma"] is False
    assert resultado["cumple_contrato"] is False


def test_contract_check_revision_incoherente_falla():
    output = _output_valido(
        alertas=[{"tipo": "molestia_fisica", "mensaje": "dolor", "severidad": "alta"}],
        requiere_revision=False,  # deberia ser True si hay alerta severidad alta
    )
    resultado = contract_check(output)
    assert resultado["revision_coherente"] is False
    assert resultado["cumple_contrato"] is False


def test_contract_check_pico_fuera_de_rango_falla():
    output = _output_valido(degradacion={"pico_pct": 150.0, "recuperacion_pct": 0.0})
    resultado = contract_check(output)
    assert resultado["pico_en_rango"] is False
    assert resultado["cumple_contrato"] is False


def test_contract_check_divergencia_invalida_falla():
    output = _output_valido(divergencia_percepcion="algo_raro")
    resultado = contract_check(output)
    assert resultado["divergencia_valida"] is False
    assert resultado["cumple_contrato"] is False


def test_contract_check_severidad_invalida_falla():
    output = _output_valido(alertas=[{"tipo": "molestia_fisica", "mensaje": "x", "severidad": "critica"}],
                             requiere_revision=False)
    resultado = contract_check(output)
    assert resultado["severidades_validas"] is False
    assert resultado["cumple_contrato"] is False


def test_contract_check_campo_faltante_falla():
    output = _output_valido()
    del output["recomendacion_semana"]
    resultado = contract_check(output)
    assert resultado["faltantes"] == ["recomendacion_semana"]
    assert resultado["cumple_contrato"] is False


def test_contract_check_campo_faltante_usado_en_reglas_no_revienta():
    # antes de la correccion, borrar un campo que `reglas` lee directamente
    # (como "alertas") tiraba KeyError en vez de reportarlo en "faltantes".
    output = _output_valido()
    del output["alertas"]
    resultado = contract_check(output)
    assert resultado["faltantes"] == ["alertas"]
    assert resultado["cumple_contrato"] is False


def test_contract_check_campo_extra_no_reconocido_falla():
    output = _output_valido(campo_inventado="algo")
    resultado = contract_check(output)
    assert resultado["extras"] == ["campo_inventado"]
    assert resultado["cumple_contrato"] is False
