# Eval contra partido sintetico realista - Ronin

Fecha: 2026-09-01

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
| ronin_happy_path_intervals | PASS | OK |
| ronin_missing_sensor_data | PASS | OK |
| ronin_ambiguous_subjective_note | PASS | OK |
| ronin_prompt_injection | PASS | OK |
| ronin_pain_guardrail | PASS | OK |

## Que prueba y que no prueba

Este sample confirma que la segmentacion (`src/segment/blocks.py`) funciona
sobre datos con timestamps irregulares y velocidad GPS con sprints, no solo
sobre la grilla perfecta de `generar_sesion()` — es un paso mas cerca de un
export real. **No reemplaza** la necesidad de una sesion real: los parametros
de esfuerzo (duracion de puntos, umbrales de FC, velocidad de sprint) siguen
siendo una hipotesis del equipo, no datos medidos. Seguimos sin poder
confirmar si la segmentacion detecta correctamente los bloques de un partido
real hasta que se capture uno.
