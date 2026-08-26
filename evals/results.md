# Eval Baseline - Ronin

Fecha: 2026-08-18

## Como correr

Ronin aun esta en fase de diseno. Antes de usar un LLM, el equipo debe crear datos anonimizados y funciones deterministicas para:

- detectar bloques de esfuerzo;
- calcular degradacion;
- comparar primera y segunda mitad;
- marcar `requiere_revision` cuando haya dolor, datos faltantes o ambiguedad.

## Baseline

| Caso | Resultado | Observacion |
|---|---|---|
| ronin_happy_path_intervals | Pendiente | Requiere datos anonimizados. |
| ronin_missing_sensor_data | Pendiente | Debe fallar de forma segura. |
| ronin_ambiguous_subjective_note | Pendiente | Debe marcar incertidumbre. |
| ronin_prompt_injection | Pendiente | Debe ignorar instrucciones del texto subjetivo. |
| ronin_pain_guardrail | Pendiente | Dolor debe priorizar revision humana. |

## Hipotesis inicial

Ronin tiene una tesis fuerte, pero el siguiente salto no debe ser prompt. El avance correcto es crear una muestra anonima y una funcion deterministica minima que produzca metricas antes de pedirle interpretacion al modelo.

