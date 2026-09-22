from src.segment.blocks import detectar_bloques
from src.segment.velocidad import (
    FUENTE_DERIVADA,
    solape_veloz_bloques,
    tiene_velocidad,
)
from tests.conftest import _serie_v


def test_tiene_velocidad_false_sin_columna_v(serie_un_bloque):
    assert tiene_velocidad(serie_un_bloque) is False


def test_tiene_velocidad_true_con_gps(serie_intermitente_con_sprints):
    assert tiene_velocidad(serie_intermitente_con_sprints) is True


def test_tiene_velocidad_false_si_la_fuente_es_derivada_de_distancia():
    # la velocidad derivada de distancia no resuelve cambios de ritmo cortos
    df = _serie_v((60, 100, 5.0), fuente_velocidad=FUENTE_DERIVADA)
    assert tiene_velocidad(df) is False


def test_solape_none_con_velocidad_constante(serie_continua_sin_sprints, fc_max):
    """Velocidad plana (GPS trabado o ritmo parejo): el percentil coincide con el
    minimo, asi que "lo rapido" no discrimina nada."""
    bloques = detectar_bloques(serie_continua_sin_sprints, fc_max)
    assert solape_veloz_bloques(serie_continua_sin_sprints, bloques) is None


def test_solape_none_sin_velocidad(serie_un_bloque, fc_max):
    bloques = detectar_bloques(serie_un_bloque, fc_max)
    assert solape_veloz_bloques(serie_un_bloque, bloques) is None


def test_solape_alto_cuando_lo_rapido_cae_en_bloques(serie_intermitente_con_sprints, fc_max):
    bloques = detectar_bloques(serie_intermitente_con_sprints, fc_max)
    assert solape_veloz_bloques(serie_intermitente_con_sprints, bloques) > 0.5


def test_solape_bajo_cuando_lo_rapido_cae_fuera_de_los_bloques(fc_max):
    # rapido donde la FC esta baja, y FC alta donde va lento: no coinciden
    df = _serie_v((60, 100, 20.0), (60, 185, 1.0), (60, 100, 20.0))
    bloques = detectar_bloques(df, fc_max)
    assert solape_veloz_bloques(df, bloques) < 0.5


def test_solape_es_relativo_no_absoluto(fc_max):
    """Un jugador lento y uno rapido con la MISMA forma de esfuerzo dan el mismo
    solape: el umbral sale de la propia sesion."""
    lento = _serie_v((60, 100, 0.5), (60, 185, 9.0), (60, 100, 0.5))
    rapido = _serie_v((60, 100, 1.0), (60, 185, 22.0), (60, 100, 1.0))
    assert (solape_veloz_bloques(lento, detectar_bloques(lento, fc_max))
            == solape_veloz_bloques(rapido, detectar_bloques(rapido, fc_max)))
