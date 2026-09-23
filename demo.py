"""Demo manual de Ronin: corre el pipeline completo (sintetico + real) y
muestra el resultado en consola. Uso:

    GROQ_API_KEY=tu_key python demo.py
"""

import json

from src.ingest.health_auto_export import load_session
from src.ingest.synthetic import generar_sesion
from src.interpret.prototype import contract_check, run_prototype

PERFIL = {"nombre": "jugador_demo", "fc_max": 192, "posicion": "cutter"}
HISTORIAL = [
    {"fecha": "2026-07-30", "pico_pct": -6.0, "recuperacion_pct": 8.0},
    {"fecha": "2026-08-06", "pico_pct": -4.2, "recuperacion_pct": 5.5},
    {"fecha": "2026-08-09", "pico_pct": -5.1, "recuperacion_pct": 7.2},
]


def mostrar(titulo: str, output: dict):
    print(f"\n{'=' * 60}\n{titulo}\n{'=' * 60}")
    print(json.dumps(output, ensure_ascii=False, indent=2))
    print("\ncontract_check:", json.dumps(contract_check(output), ensure_ascii=False))


def demo_sintetico():
    """Sesion inventada con patron intermitente (bloques + descansos) — pensada
    para que SI pase el contrato, muestra el caso feliz."""
    serie, _ = generar_sesion(seed=42)
    real_input = {
        "perfil": PERFIL,
        "serie": serie,
        "tipo_sesion": "partido",
        "esfuerzo_percibido": 8,
        "nota": "me sentí bien los primeros puntos pero en el último cuarto no alcanzaba las marcas",
        "historial": HISTORIAL,
    }
    mostrar("CASO 1 — sesión sintética (patrón intermitente simulado)", run_prototype(real_input))


def demo_real():
    """Sesion real capturada con Apple Watch (Outdoor Run de prueba, no ultimate).
    Al ser una corrida continua, se espera que el sistema la rechace por no
    tener el patron de bloques que Ronin busca — es el comportamiento correcto."""
    df = load_session("data/samples/outdoor_run_2026-08-21.json")
    real_input = {
        "perfil": PERFIL,
        "serie": df,
        "tipo_sesion": "entrenamiento",
        "esfuerzo_percibido": 6,
        "nota": "corrida continua de prueba, no es un partido de ultimate",
        "historial": [],
    }
    mostrar("CASO 2 — sesión real de Apple Watch (Outdoor Run, no intermitente)", run_prototype(real_input))


if __name__ == "__main__":
    demo_sintetico()
    demo_real()
