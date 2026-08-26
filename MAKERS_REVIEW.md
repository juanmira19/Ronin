# Makers Review

## Que encontramos

- El README tiene una tesis de producto superior al promedio: bloques de esfuerzo para deportes intermitentes.
- El equipo ya separa una idea clave: la IA interpreta, pero no calcula numeros.
- Aun no hay notebook, `src/`, datos anonimizados ni tests ejecutables.
- El riesgo principal es medico/deportivo: convertir interpretacion de rendimiento en consejo de salud.
- La siguiente mejora debe crear evidencia medible antes de usar modelo.

## Mejora aplicada

Agregue `evals/eval_cases.json` con 5 casos para validar el contrato de Ronin:

- sesion intermitente normal;
- datos de sensores faltantes;
- nota subjetiva ambigua;
- prompt injection;
- dolor o molestia fisica.

Tambien agregue `evals/results.md` como plantilla de baseline.

## Por que importa

Ronin no debe depender de que el modelo "suene inteligente". Si el producto promete bloques, degradacion y recuperacion, esas metricas deben salir de codigo deterministico y datos trazables. La IA entra despues para explicar, no para inventar.

## Como probarlo

1. Crear una muestra anonima en `data/samples/`.
2. Implementar una primera funcion deterministica para detectar bloques.
3. Ejecutar los casos de `evals/eval_cases.json`.
4. Registrar pass/fail en `evals/results.md`.

## Tu reto

1. Core: subir un CSV anonimo minimo con timestamp, frecuencia cardiaca y velocidad.
2. Intermediate: crear una funcion `detect_effort_blocks(sample)` que no use IA.
3. Advanced: agregar un validador que compare las cifras del texto generado por IA contra las metricas calculadas.
