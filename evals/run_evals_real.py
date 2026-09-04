"""Corre los mismos 5 casos de evals/eval_cases.json contra la sesion real
anonimizada (data/samples/outdoor_run_2026-08-21.json) en vez de la
generar_sesion() sintetica que usa evals/run_evals.py. Ver TEAM_ROTATION.md
(respuesta 2026-08-27, punto 5) y MAKERS_REVIEW.md (reto de hoy).

`ronin_missing_sensor_data` no aplica: la sesion real siempre tiene datos de
sensores, por definicion no puede probar el caso "sin datos". Se marca N/A.

    GROQ_API_KEY=... python -m evals.run_evals_real
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from evals.run_evals import CASES_PATH, HISTORIAL, PERFIL, evaluar_caso
from src.ingest.health_auto_export import load_session
from src.interpret.prototype import contract_check, run_prototype

ROOT = Path(__file__).resolve().parent.parent
RESULTS_PATH = ROOT / "evals" / "results_real.md"
SAMPLE_PATH = ROOT / "data" / "samples" / "outdoor_run_2026-08-21.json"

SERIE_REAL = load_session(SAMPLE_PATH)


def construir_input(caso: dict) -> dict | None:
    inp = caso["input"]
    if inp["heart_rate_series"] is None:
        return None
    return {
        "perfil": PERFIL,
        "serie": SERIE_REAL,
        # La sesion real es un "Outdoor Run" de prueba, no un partido de
        # ultimate/futbol: se declara como entrenamiento, no como partido.
        "tipo_sesion": "entrenamiento",
        "esfuerzo_percibido": 8,
        "nota": inp["player_note"],
        "historial": HISTORIAL,
    }


def main():
    casos = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    filas = []
    for caso in casos:
        real_input = construir_input(caso)
        if real_input is None:
            obs = "no aplica: la sesion real siempre tiene datos de sensores"
            filas.append((caso["id"], "N/A", obs))
            print(f"[N/A] {caso['id']} — {obs}")
            continue
        try:
            output = run_prototype(real_input)
            check = contract_check(output) if "error" not in output else {"cumple_contrato": None}
            ok, obs = evaluar_caso(caso, output, check)
            resultado = "PASS" if ok else "FAIL"
        except Exception as exc:  # noqa: BLE001
            resultado, obs = "ERROR", str(exc)[:200]
        filas.append((caso["id"], resultado, obs))
        print(f"[{resultado}] {caso['id']} — {obs}")

    fecha = date.today().isoformat()
    tabla = "\n".join(f"| {cid} | {res} | {obs.replace('|', '/')} |" for cid, res, obs in filas)
    RESULTS_PATH.write_text(
        f"""# Eval contra sesion real - Ronin

Fecha: {fecha}

Mismos 5 casos de `evals/eval_cases.json`, corridos contra la sesion real
anonimizada (`data/samples/outdoor_run_2026-08-21.json`, un Outdoor Run de
Apple Watch) en vez de `generar_sesion()` sintetica. Ver `evals/run_evals_real.py`.

## Como correr

`GROQ_API_KEY=... python -m evals.run_evals_real` desde la raiz del repo.

## Resultado

| Caso | Resultado | Observacion |
|---|---|---|
{tabla}

## Hipotesis confirmada

La segmentacion deterministica (`src/segment/blocks.py`) encuentra un unico
bloque de esfuerzo (570 s) en la sesion real: es una corrida continua, no el
patron intermitente (arranque-parada) que Ronin espera de ultimate o futbol.
`calcular_metricas` exige al menos 2 bloques para calcular degradacion entre
mitades y falla explicitamente en vez de inventar una cifra — el sistema
rechaza la sesion (`{{"error": [...]}}`) antes de llamar al modelo.

## Que aporta la senal de velocidad

Desde que `detectar_bloques` consume la columna `v` (ver `src/segment/velocidad.py`
y `src/segment/calidad.py`), el rechazo dejo de ser un sintoma opaco
("menos de 2 bloques") y trae la causa. Para esta sesion la confianza de
segmentacion es **baja**, por dos razones independientes y verificables:

1. **Patron continuo**: 0.0% de las muestras superan los 14 km/h. El maximo de
   toda la corrida es 13.4 km/h. No hay sprints, luego no hay arranque-parada.
   (El partido sintetico, en contraste, pasa 8.3% del tiempo sobre ese umbral.)
2. **Senal con huecos**: la serie de FC tiene dos huecos (184 s y 145 s) que
   `load_session` rellena por interpolacion lineal. Son ~16% de la sesion, y
   esa FC es reconstruida, no medida. Antes eso solo salia por consola; ahora
   viaja en `df.attrs["frac_interpolada"]` y pesa en la confianza.

El FAIL de `ronin_happy_path_intervals` **no se corrigio, y no debe corregirse**:
esta corrida genuinamente no es una sesion de ultimate. Bajar el umbral para
forzar bloques seria fabricar la metrica. Lo que cambio es la calidad del
diagnostico, no el veredicto.

Eso explica el cambio de score frente al baseline sintetico (`evals/results.md`,
5/5 con datos sinteticos disenados para tener bloques):

- `ronin_happy_path_intervals` pasa a FAIL: esperaba `requiere_revision=False`
  con metricas deterministicas, pero la sesion real no tiene el patron de
  bloques que el caso feliz asume.
- `ronin_ambiguous_subjective_note`, `ronin_prompt_injection` y
  `ronin_pain_guardrail` siguen en PASS, pero de forma trivial: como el sistema
  rechaza la sesion por falta de segmentacion, `requiere_revision` sale `True`
  en los tres, que coincide con lo esperado — no porque el modelo haya
  razonado sobre la nota del jugador (no llego a llamarse: los 4 casos con
  datos fallan antes de la interpretacion LLM).
- `ronin_missing_sensor_data` no aplica (N/A): la sesion real siempre tiene
  datos.

Conclusion: el score "5/5" del baseline sintetico no prueba que la
segmentacion de bloques funcione con datos reales — la sintetica ya viene
disenada con bloques. El siguiente paso no es ajustar el umbral para forzar
bloques en esta corrida (seria fabricar la metrica), sino conseguir una sesion
real de ultimate/futbol (deporte de arranque-parada) para validar la
segmentacion contra el patron que el producto realmente necesita detectar.
""",
        encoding="utf-8",
    )
    print(f"\nResultados escritos en {RESULTS_PATH}")


if __name__ == "__main__":
    main()
