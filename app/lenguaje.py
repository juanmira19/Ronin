"""Traduce las metricas a frases que entiende un jugador.

Vive en la capa de presentacion a proposito: `METRICAS.conclusiones` (en
src/metrics/session.py) esta redactado en tercera persona porque lo consume el
prompt, y cambiarlo moveria los evals. Aca se reescribe en segunda persona para
la pantalla, sin tocar nada de src/.

Deterministico: estas frases NO las escribe el modelo. Son las mismas
conclusiones que ya calculo el sistema, dichas de otra forma."""

from datetime import datetime
from typing import Optional

PICO = {
    "perdio intensidad en la segunda mitad": "Perdiste fuerza en la segunda mitad",
    "subio la intensidad en la segunda mitad": "Fuiste a más en la segunda mitad",
    "mantuvo la intensidad toda la sesion": "Mantuviste la intensidad de principio a fin",
}

RECUPERACION = {
    "recupero peor hacia el final": "Te costó más recuperar entre esfuerzos",
    "recupero mejor hacia el final": "Recuperaste mejor hacia el final",
    "recupero igual toda la sesion": "Recuperaste igual toda la sesión",
}

CONFIANZA = {
    "media": "Esta sesión la leímos con menos certeza de la habitual",
    "baja": "Esta sesión no la pudimos separar en esfuerzos con confianza",
}


def hallazgos(metricas: dict, calidad: Optional[dict] = None) -> list[dict]:
    """Tres o cuatro frases, cada una con un dato de apoyo. El orden importa:
    primero cuantos esfuerzos hubo, que es lo que el reloj no sabe decir."""
    b = metricas["bloques_esfuerzo"]
    c = metricas["conclusiones"]
    salida = [
        {"titulo": f"Hiciste {b['cantidad']} esfuerzos",
         "detalle": f"de {b['duracion_media_seg']} segundos en promedio, "
                    f"{b['distribucion']['maximo']} de ellos al máximo"},
        {"titulo": PICO.get(c["pico"], c["pico"]),
         "detalle": "comparando tus esfuerzos de la primera mitad con los de la segunda"},
        {"titulo": RECUPERACION.get(c["recuperacion"], c["recuperacion"]),
         "detalle": "mirando cuánto te baja el pulso en el minuto siguiente a cada esfuerzo"},
    ]
    aviso = CONFIANZA.get((calidad or {}).get("confianza"))
    if aviso:
        salida.append({"titulo": aviso, "detalle": "preferimos decirlo a darte un número que no se sostiene"})
    return salida


def frase_reloj(reloj: dict) -> str:
    """La linea del contraste, en una sola frase."""
    partes = []
    if "distancia_km" in reloj:
        partes.append(f"{reloj['distancia_km']:.2f} km".replace(".", ","))
    if reloj.get("ritmo_medio"):
        partes.append(f"ritmo {reloj['ritmo_medio']} por km")
    partes.append(f"{reloj['fc_media']} pulsaciones de media")
    return " · ".join(partes)


DIAS = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


def fecha_partido(d: datetime) -> str:
    """"viernes 4 sep, 5:00 p. m.", en la hora local en que se jugo."""
    hora = d.hour % 12 or 12
    sufijo = "a. m." if d.hour < 12 else "p. m."
    return f"{DIAS[d.weekday()]} {d.day} {MESES[d.month - 1]}, {hora}:{d.minute:02d} {sufijo}"


# Cada conclusion del sistema, contada desde cada mitad, con su tono (True =
# buena noticia). Relativas a proposito: el sistema compara una mitad contra la
# otra, no contra un ideal. El tono decide el conector: "y" si las dos frases van
# en la misma direccion, "pero" si se contradicen.
_PICO_MITADES = {
    "perdio intensidad en la segunda mitad": (("Tus esfuerzos llegaban más arriba", True),
                                              ("Tus esfuerzos ya no llegaban tan arriba", False)),
    "subio la intensidad en la segunda mitad": (("Arrancaste guardándote un poco", False),
                                                ("Subiste la intensidad", True)),
    "mantuvo la intensidad toda la sesion": (("Jugaste a tope", True),
                                             ("Seguiste con la misma intensidad", True)),
}
_REC_MITADES = {
    "recupero peor hacia el final": (("entre puntos el pulso te bajaba rápido", True),
                                     ("entre puntos el pulso te bajaba menos: "
                                      "llegabas a cada punto más cargado", False)),
    "recupero mejor hacia el final": (("entre puntos te costaba bajar el pulso", False),
                                      ("entre puntos recuperabas mejor que al principio", True)),
    "recupero igual toda la sesion": (("entre puntos recuperabas bien", True),
                                      ("recuperabas igual que al principio", True)),
}


def _dato_mitad(m: dict) -> str:
    dato = f"{m['esfuerzos']} esfuerzos"
    ppm = m["recuperacion_ppm"]
    if ppm is not None and ppm <= 2:
        dato += " · el pulso casi no bajaba en el minuto siguiente"
    elif ppm is not None:
        dato += f" · el pulso bajaba {ppm} pulsaciones en el minuto siguiente"
    return dato


def _frase(pico, rec) -> str:
    if rec is None:
        return f"{pico[0]}."
    conector = " y " if pico[1] == rec[1] else ", pero "
    return f"{pico[0]}{conector}{rec[0]}."


def mitades(metricas: dict, partido: dict) -> list:
    """Primera y segunda mitad en una frase cada una, con su dato debajo."""
    c = metricas["conclusiones"]
    pico = _PICO_MITADES.get(c["pico"], ((c["pico"], True), (c["pico"], True)))
    rec = _REC_MITADES.get(c["recuperacion"], (None, None))
    return [{"titulo": nombre, "texto": _frase(pico[i], rec[i]),
             "dato": _dato_mitad(partido[clave])}
            for i, (nombre, clave) in enumerate([("Primera mitad", "primera"),
                                                  ("Segunda mitad", "segunda")])]
