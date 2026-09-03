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

<!-- MAKERS_REVIEW_2026_08_27_START -->
## Revision docente - 2026-08-27

### Lo que vimos

- Andres Jacobo hizo un salto fuerte: extrajo capa deterministica a src/, agrego demo, requirements, datos sample, eval runner y tests.
- Juan Pablo Mira ya tiene rama, pero el aporte individual debe quedar mas claro y diferenciado.
- El proyecto tiene buena tesis: analizar sesiones deportivas con estructura, metricas y validacion.
- El baseline actual pasa 5/5, pero corre sobre datos sinteticos.
- El siguiente salto es probar con datos reales anonimizados o al menos muestras mas parecidas al mundo real.

### Reto de hoy

Pasen de sintetico a evidencia mas realista:

1. Agregar un sample anonimizado o semi-realista en data/samples/.
2. Correr los mismos evals contra ese sample.
3. Documentar si el score cambia y que hipotesis aparece.

### Tarea obligatoria: diagrama de arquitectura

Crear docs/arquitectura.md con un diagrama Mermaid que muestre:

`mermaid
flowchart LR
  DatosSesion --> Ingesta
  Ingesta --> Anonimizacion
  Anonimizacion --> Segmentacion
  Segmentacion --> Metricas
  Metricas --> InterpretacionLLM
  InterpretacionLLM --> Verificacion
  Evals --> Verificacion
`

El diagrama debe mostrar claramente que es deterministico, que usa LLM y donde se verifica.

### Criterio de aceptacion

Crear estructura es buen avance, pero ahora necesitamos evidencia con datos que se parezcan al producto real.
<!-- MAKERS_REVIEW_2026_08_27_END -->

<!-- MAKERS_CODE_ARCH_REVIEW_2026_09_01_START -->

## Revision de codigo y arquitectura - 2026-09-01

### Lectura docente

- Andres Jacobo hizo uno de los avances tecnicos mas fuertes: src/, evals, tests, demo, requirements y sample.
- Juan Pablo Mira aparece con merge, pero su aporte individual tecnico sigue poco claro.
- No se detecto docs/arquitectura.md.
- El baseline pasa, pero principalmente sobre datos sinteticos.

### Revision de principios

- Bien: separar ingesta, metricas, interpretacion y verificacion es buena direccion.
- Falta: arquitectura explicita para que el equipo pueda explicar el sistema entero.
- Falta: evidencia con datos mas cercanos al uso real.

### Pendiente de equipo

Crear docs/arquitectura.md y correr los evals contra un sample anonimizado o semi-realista.

### Pendiente por poca evidencia individual

Juan Pablo debe dejar commit propio: arquitectura, sample, eval adicional o mejora de validacion.

<!-- MAKERS_CODE_ARCH_REVIEW_2026_09_01_END -->

## Respuesta al equipo — 2026-09-02

Responde a las dos revisiones docentes de arriba (2026-08-27 y 2026-09-01), que pedian lo mismo: `docs/arquitectura.md` y correr los evals contra un sample anonimizado o semi-realista.

- Se agrego `docs/arquitectura.md` con el diagrama Mermaid pedido, mostrando la cadena `DatosSesion -> Ingesta -> Anonimizacion -> Segmentacion -> Metricas -> InterpretacionLLM -> Verificacion`, con `Evals` alimentando la `Verificacion`, y marcando explicitamente que es deterministico, donde entra el LLM y donde se verifica su salida.
- Se agrego `data/samples/outdoor_run_2026-08-21.json`: sesion real de Apple Watch (Outdoor Run), anonimizada con `src/ingest/anonymize.py` (sin lat/lon, sin identificadores, timestamps relativos al inicio). Se corrieron los mismos 5 casos de `evals/eval_cases.json` contra ella con `evals/run_evals_real.py` (nuevo script, no reemplaza el baseline sintetico). Resultado en `evals/results_real.md`: 3 PASS, 1 FAIL, 1 N/A — cambia frente al 5/5 del baseline sintetico (`evals/results.md`).
- Hipotesis confirmada: la sesion real es una corrida continua (FC sostenida, sin bajadas), no el patron intermitente de arranque-parada de ultimate/futbol. `detectar_bloques` encuentra un unico bloque; `calcular_metricas` exige al menos 2 y falla explicitamente en vez de inventar una cifra, por lo que el sistema rechaza la sesion (`{"error": [...]}`) antes de llamar al modelo. El caso feliz (`ronin_happy_path_intervals`) es el unico que falla por eso; los otros tres pasan de forma trivial porque el rechazo ya implica `requiere_revision=True`.

**Aclaracion importante: el equipo aun no ha podido ir a grabar una sesion real
de partido (ultimate o futbol).** La unica sesion real capturada hasta ahora es
una corrida continua de prueba (`outdoor_run_2026-08-21.json`), que por diseno
no tiene el patron intermitente que Ronin necesita validar. Mientras se
consigue esa grabacion, se genero un proxy honesto: un partido sintetico con
forma de export real anonimizado (timestamps irregulares, velocidad GPS con
sprints, medio tiempo, fatiga acumulada) en `data/samples/partido_sintetico_2026-09-01.json`
(`generate_synthetic_sample.py` / `src/ingest/synthetic.py:generar_export_sintetico_partido`).
Los 5 casos corridos contra ese sample dan 5/5 PASS de forma no trivial (la
segmentacion detecta 15 bloques y la interpretacion LLM si se ejecuta) — ver
`evals/results_synthetic_realista.md`. Esto **no reemplaza** una sesion real:
los parametros de esfuerzo son una hipotesis del equipo, no datos medidos. Se
deja explicito para no confundir "pasa el eval" con "esta validado con datos
reales de un partido".

Conclusion honesta: el "5/5" sintetico original no probaba la segmentacion
contra datos reales. Ahora hay evidencia real de que el umbral funciona
(rechaza lo que no es intermitente) y evidencia sintetica-realista de que
funciona sobre un patron de bloques con forma de export real, pero sigue
pendiente una sesion real de ultimate/futbol para validar el caso que el
producto de verdad necesita resolver — ver `TEAM_ROTATION.md` (respuestas
2026-09-01).
