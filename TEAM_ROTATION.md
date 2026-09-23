# Team Rotation

Objetivo: que todos entiendan todo el sistema, no que cada persona quede encerrada en una parte.

## Semana actual

| Rol temporal | Responsable | Que lidera | Quien debe poder explicarlo |
|---|---|---|---|
| Build owner | TBD | Cambio tecnico en notebook/script, prompt, modelo o flujo principal | TBD |
| Evaluate owner | TBD | Evals, baseline, expected vs actual, pass/fail | TBD |
| Explain owner | TBD | README, resultados, decisiones y demo tecnica | TBD |

## Reglas

- El owner lidera, pero no trabaja aislado.
- Cada cambio debe poder ser explicado por otra persona del equipo.
- Cada integrante debe hacer al menos un microcambio visible en GitHub.
- No cuenta decir "yo ayude" si no hay evidencia en el repo.
- No se cambia todo a la vez: una hipotesis, un cambio, una medicion.

## Checklist semanal

- [ ] Todos entienden el flujo principal.
- [ ] Todos entienden los evals.
- [ ] Todos pueden explicar el ultimo cambio.
- [ ] Todos saben que sigue fallando.
- [ ] Cada integrante dejo evidencia en GitHub.

## Preguntas que cualquiera debe responder

1. Que cambio esta semana?
2. Por que ese cambio importa?
3. Como sabemos si mejoro?
4. Que caso sigue fallando?
5. Que haremos despues?

## Respuesta — semana del 2026-08-27

1. **Que cambio:** se saco la capa deterministica del notebook a `src/` (segmentacion de
   bloques, metricas de degradacion/recuperacion, validacion de input, verificacion de
   cifras) y se escribio `evals/run_evals.py`, que corre los 5 casos de
   `evals/eval_cases.json` contra la implementacion real en vez de dejarlos en "Pendiente".
2. **Por que importa:** hasta ahora la tesis de producto no tenia nada ejecutable
   detras. Ahora hay codigo real e importable, y una forma automatica de saber si
   Ronin cumple sus propias reglas de seguridad (no inventar datos, no diagnosticar,
   priorizar dolor, resistir manipulacion).
3. **Como sabemos que mejoro:** los 5/5 casos de eval pasan corriendo contra `src/`.
   En el primer intento, 2 fallaban (nota ambigua no generaba alerta; el intento de
   manipulacion "jugar lesionado" no disparaba revision humana) — eso llevo a agregar
   dos reglas nuevas al prompt del modelo (`src/interpret/prototype.py`), no a
   inventar el resultado.
4. **Que sigue fallando / pendiente:** todo el pipeline sigue corriendo sobre datos
   **sinteticos** (`generar_sesion`), no sobre una sesion real de ultimate. Esa es la
   siguiente dependencia bloqueante — sin eso no se puede confirmar que la
   segmentacion de bloques funciona con datos reales del reloj.
5. **Que sigue:** capturar la sesion real (Apple Watch, JSON, version V2 de Health
   Auto Export), anonimizarla, y volver a correr `evals/run_evals.py` reemplazando
   `generar_sesion()` por esa sesion real. Despues, asignar los roles de la tabla de
   arriba (siguen en TBD — es una decision del equipo, no tecnica).

## Respuesta — semana del 2026-09-01

1. **Que cambio:** se capturo y anonimizo la sesion real pendiente (`data/samples/outdoor_run_2026-08-21.json`)
   y se escribio `evals/run_evals_real.py`, que corre los mismos 5 casos de
   `evals/eval_cases.json` contra esa sesion real en vez de `generar_sesion()`.
   Tambien se agrego `docs/arquitectura.md` con el diagrama pedido en la revision
   docente del 2026-08-27.
2. **Por que importa:** el baseline sintetico (5/5) no probaba nada sobre datos
   reales — la sesion sintetica ya viene disenada con bloques de esfuerzo. Correr
   contra una sesion real es lo que de verdad valida (o no) la segmentacion.
3. **Como sabemos que mejoro:** el score cambio de 5/5 (sintetico) a 3 PASS / 1 FAIL
   / 1 N/A (real) — ver `evals/results_real.md`. El cambio es evidencia, no una
   regresion: expone que la segmentacion por umbral de FC funciona como se espera
   (rechaza sesiones sin patron de bloques) pero que el equipo aun no tiene una
   sesion real de ultimate/futbol para validar el caso que de verdad importa.
4. **Que sigue fallando / pendiente:** `ronin_happy_path_intervals` falla contra la
   sesion real porque es una corrida continua (deporte "arranque-parada" ausente),
   `detectar_bloques` solo encuentra 1 bloque y `calcular_metricas` exige minimo 2.
   Es el comportamiento correcto (no fabrica cifras), pero significa que la
   segmentacion sigue sin validarse contra el patron real del producto.
5. **Que sigue:** conseguir una sesion real de ultimate o futbol (no una corrida),
   anonimizarla igual que esta, y volver a correr `evals/run_evals_real.py` contra
   esa sesion para validar la segmentacion de bloques con el patron que Ronin
   realmente necesita detectar.

## Nota — 2026-09-01 (segunda entrada del dia): aun no hay sesion real de juego

**El equipo todavia no ha podido ir a grabar una sesion real de partido**
(ultimate o futbol). Mientras eso no pase, se genero un proxy: un partido
sintetico pero con forma de export real anonimizado — timestamps irregulares
(no la grilla perfecta de `generar_sesion()`), velocidad GPS con sprints,
medio tiempo y fatiga acumulada (`generate_synthetic_sample.py`, funcion
`generar_export_sintetico_partido` en `src/ingest/synthetic.py`, archivo
`data/samples/partido_sintetico_2026-09-01.json`).

1. **Que cambio:** se corrieron los mismos 5 casos contra ese partido sintetico
   realista (`evals/run_evals_synthetic_realista.py` → `evals/results_synthetic_realista.md`).
2. **Como sabemos que mejoro:** 5/5 PASS, pero a diferencia del baseline
   sintetico original (`generar_sesion()`, sin velocidad, grilla perfecta), esta
   vez la segmentacion detecto 15 bloques de un patron intermitente realista
   (sprints + descansos variables + medio tiempo), y el 5/5 no es trivial: la
   interpretacion LLM si llego a ejecutarse en los 4 casos con datos, porque
   `calcular_metricas` no fallo (a diferencia de `evals/results_real.md`,
   donde fallaba por ser una corrida continua).
3. **Que sigue fallando / pendiente — dejarlo explicito:** esto **no reemplaza**
   una sesion real. Los parametros de esfuerzo (duracion de puntos, umbral de
   FC, velocidad de sprint) son una hipotesis del equipo, no datos medidos.
   Seguimos sin poder confirmar si la segmentacion funciona sobre un partido
   real hasta que se grabe uno.
4. **Que sigue:** la prioridad de bloqueo sigue siendo la misma del punto 5 de
   arriba — ir a la cancha con el Apple Watch durante un partido real y
   repetir este mismo proceso de anonimizacion + eval contra esos datos.
