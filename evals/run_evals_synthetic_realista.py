"""Corre los mismos 5 casos de evals/eval_cases.json contra un partido de
ultimate sintetico pero realista (mismo formato que un export anonimizado real,
timestamps irregulares, velocidad GPS con sprints, medio tiempo, fatiga
acumulada) en vez de `generar_sesion()` (grilla perfecta, sin velocidad) o de
la sesion real de corrida continua (`evals/run_evals_real.py`).

Este sample es un proxy: el equipo aun no ha podido grabar un partido real de
ultimate/futbol para anonimizarlo. Ver TEAM_ROTATION.md / MAKERS_REVIEW.md,
respuesta 2026-09-01.

    GROQ_API_KEY=... python -m evals.run_evals_synthetic_realista
"""

import json
from pathlib import Path

from evals.run_evals import CASES_PATH, HISTORIAL, PERFIL, evaluar_caso
from src.ingest.health_auto_export import load_session
from src.interpret.prototype import contract_check, run_prototype

ROOT = Path(__file__).resolve().parent.parent
RESULTS_PATH = ROOT / "evals" / "results_synthetic_realista.md"
SAMPLE_PATH = ROOT / "data" / "samples" / "partido_sintetico_2026-09-01.json"

SERIE_PARTIDO = load_session(SAMPLE_PATH)
SERIE_CORTA = SERIE_PARTIDO[SERIE_PARTIDO["t"] <= 600].reset_index(drop=True)


def construir_input(caso: dict) -> dict:
    inp = caso["input"]
    serie = SERIE_CORTA if inp["heart_rate_series"] is None else SERIE_PARTIDO
    return {
        "perfil": PERFIL,
        "serie": serie,
        "tipo_sesion": "partido",
        "esfuerzo_percibido": 5 if inp["heart_rate_series"] is None else 8,
        "nota": inp["player_note"],
        "historial": HISTORIAL,
    }


def main():
    casos = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    filas = []
    for caso in casos:
        real_input = construir_input(caso)
        try:
            output = run_prototype(real_input)
            check = contract_check(output) if "error" not in output else {"cumple_contrato": None}
            ok, obs = evaluar_caso(caso, output, check)
            resultado = "PASS" if ok else "FAIL"
        except Exception as exc:  # noqa: BLE001
            resultado, obs = "ERROR", str(exc)[:200]
        filas.append((caso["id"], resultado, obs))
        print(f"[{resultado}] {caso['id']} — {obs}")

    fecha = "2026-09-01"
    tabla = "\n".join(f"| {cid} | {res} | {obs.replace('|', '/')} |" for cid, res, obs in filas)
    RESULTS_PATH.write_text(
        f"""# Eval contra partido sintetico realista - Ronin

Fecha: {fecha}

Mismos 5 casos de `evals/eval_cases.json`, corridos contra un partido de
ultimate sintetico pero con forma de export real anonimizado
(`data/samples/partido_sintetico_2026-09-01.json`: timestamps irregulares,
velocidad GPS con sprints, medio tiempo, fatiga acumulada — generado con
`generate_synthetic_sample.py` / `src/ingest/synthetic.py:generar_export_sintetico_partido`).

**Por que existe este archivo:** el equipo aun no ha podido ir a grabar y
anonimizar un partido real de ultimate o futbol (deporte de arranque-parada).
Mientras eso no pase, este sample sintetico-realista es el mejor proxy
disponible para probar la segmentacion contra un patron intermitente, en vez
de contra la grilla idealizada de `generar_sesion()` o contra la corrida
continua real (`evals/results_real.md`), que por diseño no tiene bloques.

## Como correr

`GROQ_API_KEY=... python -m evals.run_evals_synthetic_realista` desde la raiz
del repo. Antes hay que generar el sample: `python generate_synthetic_sample.py`.

## Resultado

| Caso | Resultado | Observacion |
|---|---|---|
{tabla}

## Que prueba y que no prueba

Este sample confirma que la segmentacion (`src/segment/blocks.py`) funciona
sobre datos con timestamps irregulares y velocidad GPS con sprints, no solo
sobre la grilla perfecta de `generar_sesion()` — es un paso mas cerca de un
export real. **No reemplaza** la necesidad de una sesion real: los parametros
de esfuerzo (duracion de puntos, umbrales de FC, velocidad de sprint) siguen
siendo una hipotesis del equipo, no datos medidos. Seguimos sin poder
confirmar si la segmentacion detecta correctamente los bloques de un partido
real hasta que se capture uno.
""",
        encoding="utf-8",
    )
    print(f"\nResultados escritos en {RESULTS_PATH}")


if __name__ == "__main__":
    main()
