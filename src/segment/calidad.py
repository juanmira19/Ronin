"""Senal deterministica de cuanto confiar en una segmentacion.

Existe para encender la alerta `segmentacion_dudosa`, que el contrato ya
preveia (ver el modelo `Alerta` en src/interpret/prototype.py) y que hasta
ahora ningun codigo emitia.

Devuelve SOLO etiquetas y frases, nunca cifras: si expusiera numeros habria que
ensancharlos en la whitelist de `src/verify/validate.cifras_permitidas`, y cada
numero agregado ahi debilita el verificador (tolerancia +-1) para todos los
demas. Ver `test_calidad_no_expone_cifras_al_prompt`."""

from src.common.constants import FRAC_INTERPOLADA_MAX, SOLAPE_MIN_CONFIABLE
from src.segment.velocidad import (
    patron_de_sesion,
    perfil_velocidad,
    solape_sprint_bloques,
)

MOTIVO_CONTINUO = "la sesion no muestra patron de arranque-parada"
MOTIVO_HUECOS = "hay tramos de frecuencia cardiaca reconstruidos por interpolacion"
MOTIVO_SIN_COINCIDENCIA = "los bloques de FC no coinciden con los tramos de velocidad alta"
MOTIVO_SIN_VELOCIDAD = "la sesion no trae velocidad utilizable: la segmentacion se apoya solo en FC"


def calidad_segmentacion(df, bloques) -> dict:
    """Etiquetas de calidad. `df.attrs` se lee siempre con .get(): pandas lo
    pierde en varias operaciones (los evals hacen slicing de la serie), asi que
    la ausencia de metadatos degrada a `desconocida`, no revienta."""
    fuente = df.attrs.get("fuente_velocidad")
    perfil = perfil_velocidad(df)
    patron = patron_de_sesion(perfil, fuente)

    frac_interpolada = df.attrs.get("frac_interpolada")
    if frac_interpolada is None:
        continuidad = "desconocida"
    elif frac_interpolada > FRAC_INTERPOLADA_MAX:
        continuidad = "con_huecos"
    else:
        continuidad = "ok"

    solape = solape_sprint_bloques(df, bloques)
    if solape is None:
        coincidencia = "no_evaluable"
    else:
        coincidencia = "alta" if solape >= SOLAPE_MIN_CONFIABLE else "baja"

    # Los motivos se acumulan aunque no sean los que deciden la confianza.
    motivos = []
    if patron == "continuo":
        motivos.append(MOTIVO_CONTINUO)
    if continuidad == "con_huecos":
        motivos.append(MOTIVO_HUECOS)
    if coincidencia == "baja":
        motivos.append(MOTIVO_SIN_COINCIDENCIA)
    if patron in ("sin_velocidad", "no_evaluable"):
        motivos.append(MOTIVO_SIN_VELOCIDAD)

    # Primera regla que aplica manda. Nota: `alta` exige velocidad GPS, asi que
    # una serie sin velocidad nunca pasa de `media` — es honesto, y como la
    # alerta solo se dispara en `baja`, los evals sinteticos no cambian.
    if patron == "continuo" or continuidad == "con_huecos":
        confianza = "baja"
    elif coincidencia == "baja" or patron in ("sin_velocidad", "no_evaluable"):
        confianza = "media"
    else:
        confianza = "alta"

    return {"patron": patron,
            "fuente_velocidad": fuente,
            "coincidencia_fc_velocidad": coincidencia,
            "continuidad_senal": continuidad,
            "confianza": confianza,
            "motivos": motivos}


def diagnostico_no_intermitente(df, bloques, calidad) -> list[str]:
    """Frases que explican POR QUE se rechazo la sesion, para acompanar el error
    de `calcular_metricas`. Hoy ese error solo dice el sintoma ('menos de 2
    bloques'); esto agrega la causa."""
    frases = []
    if calidad["patron"] == "continuo":
        frases.append("Sesion no intermitente: la velocidad no muestra tramos de sprint.")
    if calidad["continuidad_senal"] == "con_huecos":
        frases.append("La serie de frecuencia cardiaca tiene tramos reconstruidos "
                      "por interpolacion.")
    if len(bloques) == 1:
        frases.append("Se detecto un unico bloque continuo de esfuerzo.")
    elif not bloques:
        frases.append("No se detecto ningun bloque de esfuerzo.")
    frases.append("Ronin analiza deportes de arranque-parada (ultimate, futbol).")
    return frases
