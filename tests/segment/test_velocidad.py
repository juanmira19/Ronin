from src.segment.blocks import detectar_bloques
from src.segment.velocidad import (
    FUENTE_DERIVADA,
    patron_de_sesion,
    perfil_velocidad,
    solape_sprint_bloques,
    tiene_velocidad,
)
from tests.conftest import _serie, _serie_v


def test_tiene_velocidad_false_sin_columna_v(serie_un_bloque):
    assert tiene_velocidad(serie_un_bloque) is False


def test_tiene_velocidad_true_con_gps(serie_intermitente_con_sprints):
    assert tiene_velocidad(serie_intermitente_con_sprints) is True


def test_tiene_velocidad_false_si_la_fuente_es_derivada_de_distancia():
    # la velocidad derivada de distancia no resuelve sprints de 3-5s
    df = _serie_v((60, 100, 5.0), fuente_velocidad=FUENTE_DERIVADA)
    assert tiene_velocidad(df) is False


def test_perfil_velocidad_none_sin_velocidad(serie_un_bloque):
    assert perfil_velocidad(serie_un_bloque) is None


def test_perfil_sesion_continua_no_tiene_sprints(serie_continua_sin_sprints):
    perfil = perfil_velocidad(serie_continua_sin_sprints)
    assert perfil["frac_sprint"] == 0.0
    assert perfil["frac_movimiento"] == 1.0  # 10 km/h esta sobre el umbral de movimiento


def test_perfil_sesion_intermitente_tiene_sprints(serie_intermitente_con_sprints):
    perfil = perfil_velocidad(serie_intermitente_con_sprints)
    assert perfil["frac_sprint"] > 0.02


def test_patron_sin_velocidad(serie_un_bloque):
    perfil = perfil_velocidad(serie_un_bloque)
    assert patron_de_sesion(perfil, None) == "sin_velocidad"


def test_patron_no_evaluable_con_fuente_derivada():
    df = _serie_v((60, 100, 5.0), fuente_velocidad=FUENTE_DERIVADA)
    assert patron_de_sesion(perfil_velocidad(df), FUENTE_DERIVADA) == "no_evaluable"


def test_patron_continuo(serie_continua_sin_sprints):
    perfil = perfil_velocidad(serie_continua_sin_sprints)
    assert patron_de_sesion(perfil, "route_speed") == "continuo"


def test_patron_intermitente(serie_intermitente_con_sprints):
    perfil = perfil_velocidad(serie_intermitente_con_sprints)
    assert patron_de_sesion(perfil, "route_speed") == "intermitente"


def test_solape_none_cuando_no_hay_sprints(serie_continua_sin_sprints, fc_max):
    bloques = detectar_bloques(serie_continua_sin_sprints, fc_max)
    assert solape_sprint_bloques(serie_continua_sin_sprints, bloques) is None


def test_solape_none_sin_velocidad(serie_un_bloque, fc_max):
    bloques = detectar_bloques(serie_un_bloque, fc_max)
    assert solape_sprint_bloques(serie_un_bloque, bloques) is None


def test_solape_alto_cuando_los_sprints_caen_en_bloques(serie_intermitente_con_sprints, fc_max):
    bloques = detectar_bloques(serie_intermitente_con_sprints, fc_max)
    assert solape_sprint_bloques(serie_intermitente_con_sprints, bloques) > 0.5


def test_solape_bajo_cuando_los_sprints_caen_fuera_de_los_bloques(fc_max):
    # sprints donde la FC esta baja, y FC alta donde no hay sprint: no coinciden
    df = _serie_v((60, 100, 20.0), (60, 185, 1.0), (60, 100, 20.0))
    bloques = detectar_bloques(df, fc_max)
    assert solape_sprint_bloques(df, bloques) < 0.5
