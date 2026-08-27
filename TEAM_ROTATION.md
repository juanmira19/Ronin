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
