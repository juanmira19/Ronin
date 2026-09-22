"""Traduce las metricas a frases que entiende un jugador.

Vive en la capa de presentacion a proposito: `METRICAS.conclusiones` (en
src/metrics/session.py) esta redactado en tercera persona porque lo consume el
prompt, y cambiarlo moveria los evals. Aca se reescribe en segunda persona para
la pantalla, sin tocar nada de src/.

Deterministico: estas frases NO las escribe el modelo. Son las mismas
conclusiones que ya calculo el sistema, dichas de otra forma."""

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
