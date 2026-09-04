from src.segment.blocks import detectar_bloques
from src.segment.calidad import (
    MOTIVO_CONTINUO,
    MOTIVO_HUECOS,
    MOTIVO_SIN_VELOCIDAD,
    calidad_segmentacion,
    diagnostico_no_intermitente,
)
from src.segment.velocidad import FUENTE_DERIVADA
from tests.conftest import _serie_v


def _calidad(df, fc_max):
    return calidad_segmentacion(df, detectar_bloques(df, fc_max))


def test_sin_velocidad_la_confianza_nunca_es_alta(serie_dos_mitades, fc_max):
    calidad = _calidad(serie_dos_mitades, fc_max)
    assert calidad["patron"] == "sin_velocidad"
    assert calidad["confianza"] == "media"
    assert MOTIVO_SIN_VELOCIDAD in calidad["motivos"]


def test_sesion_continua_da_confianza_baja(serie_continua_sin_sprints, fc_max):
    calidad = _calidad(serie_continua_sin_sprints, fc_max)
    assert calidad["patron"] == "continuo"
    assert calidad["confianza"] == "baja"
    assert MOTIVO_CONTINUO in calidad["motivos"]


def test_sesion_intermitente_limpia_da_confianza_alta(serie_intermitente_con_sprints, fc_max):
    df = serie_intermitente_con_sprints
    df.attrs["frac_interpolada"] = 0.0
    calidad = _calidad(df, fc_max)
    assert calidad["patron"] == "intermitente"
    assert calidad["confianza"] == "alta"
    assert calidad["motivos"] == []


def test_muchos_huecos_interpolados_dan_confianza_baja(serie_intermitente_con_sprints, fc_max):
    df = serie_intermitente_con_sprints
    df.attrs["frac_interpolada"] = 0.16  # el caso real de outdoor_run
    calidad = _calidad(df, fc_max)
    assert calidad["continuidad_senal"] == "con_huecos"
    assert calidad["confianza"] == "baja"
    assert MOTIVO_HUECOS in calidad["motivos"]


def test_attrs_ausentes_degradan_sin_reventar(serie_dos_mitades, fc_max):
    serie_dos_mitades.attrs.clear()
    calidad = _calidad(serie_dos_mitades, fc_max)
    assert calidad["continuidad_senal"] == "desconocida"
    assert calidad["confianza"] in {"media", "baja"}


def test_velocidad_derivada_de_distancia_no_da_confianza_alta(fc_max):
    df = _serie_v((60, 100, 0.5), (60, 185, 18.0), (60, 100, 0.5),
                  (60, 185, 18.0), (60, 100, 0.5), fuente_velocidad=FUENTE_DERIVADA)
    calidad = _calidad(df, fc_max)
    assert calidad["patron"] == "no_evaluable"
    assert calidad["confianza"] == "media"


def test_calidad_no_expone_cifras_al_prompt(serie_intermitente_con_sprints, fc_max):
    """Guardian del diseno: si alguien expone una cifra aca, hay que agregarla a
    cifras_permitidas o el verificador descartara el texto del modelo."""
    calidad = _calidad(serie_intermitente_con_sprints, fc_max)
    for clave, valor in calidad.items():
        if isinstance(valor, list):
            assert all(isinstance(x, str) for x in valor), clave
        else:
            assert valor is None or isinstance(valor, str), clave


def test_diagnostico_no_intermitente_explica_la_causa(serie_continua_sin_sprints, fc_max):
    df = serie_continua_sin_sprints
    bloques = detectar_bloques(df, fc_max)
    frases = diagnostico_no_intermitente(df, bloques, calidad_segmentacion(df, bloques))
    assert any("no intermitente" in f for f in frases)
    assert any("arranque-parada" in f for f in frases)
