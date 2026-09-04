# Ronin

**Análisis de rendimiento para deportes intermitentes.**

Tu reloj te dice que corriste 7,4 km a ritmo 7:12 en un partido de ultimate. Ese dato no significa nada: no corriste 7 km a ritmo constante, hiciste decenas de esfuerzos máximos con recuperaciones incompletas. El promedio borra justo lo que importa.

Ronin lee los datos crudos de tu reloj y los interpreta en el lenguaje de tu deporte: cuántos bloques de esfuerzo hubo, si su intensidad cayó a lo largo del partido, si recuperaste peor hacia el final, y qué priorizar en la semana.

---

## El problema

Todo el ecosistema de wearables está construido sobre esfuerzo **continuo**. Ritmo, distancia, zona 2, carga de entrenamiento: modelos diseñados para correr y montar bici, donde el esfuerzo es sostenido y parejo.

Los deportes intermitentes —ultimate, fútbol, baloncesto, tenis, squash— funcionan al revés: sprints cortos, pausas, repetición. Un punto de ultimate dura hasta 3 minutos y después viene descanso. Las métricas actuales promedian ese patrón hasta volverlo invisible.

Resultado: jugadores que entrenan con lógica de corredor de fondo, llegan sin capacidad de repetir esfuerzos, y se fatigan en el último cuarto sin saber por qué.

## Qué hace Ronin

Recibe la serie temporal de una sesión (frecuencia cardíaca y velocidad con marcas de tiempo) más una lectura subjetiva del jugador, y devuelve un análisis estructurado:

| Campo | Qué contiene |
|---|---|
| `lectura_sesion` | Interpretación en lenguaje del jugador, 2–3 frases |
| `bloques_esfuerzo` | Cantidad, duración media, distribución por intensidad y confianza de la segmentación |
| `degradacion` | Caída del pico entre primera y segunda mitad; empeoramiento de la recuperación |
| `comparacion_historial` | Qué cambió respecto a las últimas 5 sesiones del mismo tipo |
| `divergencia_percepcion` | `alineado` · `percibio_mas` · `percibio_menos` |
| `recomendacion_semana` | Qué priorizar en los próximos días |
| `alertas` | Señales que merecen atención (puede estar vacía) |
| `requiere_revision` | Booleano: cuándo hace falta mirada humana |

## Principios de diseño

**La IA no calcula números.** La detección de bloques de esfuerzo y todas las métricas derivadas son determinísticas: las hace el sistema. La IA interpreta, contextualiza y explica. Antes de mostrar cualquier resultado, el sistema verifica que las cifras del texto generado coincidan con las calculadas.

**Bloques, no sprints.** La frecuencia cardíaca tiene entre 15 y 30 segundos de latencia y el GPS pierde precisión con cambios de dirección bruscos. Contar sprints individuales no es honesto con este hardware. Ronin detecta bloques de esfuerzo —que en ultimate corresponden aproximadamente a los puntos jugados— porque eso sí es detectable con confianza.

La velocidad sí se usa, pero para dos cosas acotadas: corregir el *inicio* de cada bloque (por esa latencia, cuando la FC cruza el umbral el esfuerzo ya empezó) y decidir si la sesión tiene patrón de arranque-parada. Nunca cambia cuántos bloques hay ni qué tan intensos son: en eso manda la FC.

**El sistema dice cuánto confía.** Cada segmentación sale con una etiqueta de confianza (`alta`/`media`/`baja`). Una corrida continua, una serie con tramos reconstruidos por interpolación, o bloques de FC que no coinciden con los tramos rápidos bajan esa confianza y levantan una alerta. Ronin prefiere decir "esto no lo segmenté bien" antes que entregar un análisis que parece sólido y no lo es.

**Lo subjetivo pesa.** El reloj no sabe cómo te sentiste. Mismo ritmo, misma frecuencia cardíaca, peor sensación es una señal real, y ninguna app que solo lea datos de sensores puede verla. Si el jugador reporta molestia física, eso pesa por encima de cualquier métrica.

**Rendimiento, nunca salud.** Ronin no diagnostica ni da consejo médico. Cuando los umbrales se cruzan, no adivina: marca `requiere_revision` y sugiere descanso.

## Estado

Tesis de problema, flujo y contrato de salida definidos. La capa determinística
(segmentación, calidad, métricas, validación) y la capa de interpretación con IA
están implementadas en `src/`, con 90 tests unitarios en `tests/` que corren sin
API key.

Los 5 casos de `evals/` pasan contra datos sintéticos (`results.md`) y contra un
partido sintético-realista con forma de export real (`results_synthetic_realista.md`).
Contra la única sesión **real** disponible (`results_real.md`, un Outdoor Run)
el caso feliz falla, y falla bien: es una corrida continua, no un deporte de
arranque-parada, y el sistema lo rechaza con diagnóstico explícito en vez de
inventar bloques.

**Pendiente, y sigue siendo la dependencia bloqueante:** grabar un partido real
de ultimate o fútbol con el reloj. Los umbrales de velocidad de hoy son hipótesis
del equipo (ver `src/common/constants.py`), no valores medidos en cancha.

## Estructura actual

```
ronin/
├── data/            # datos de sesiones — NO se versiona (ver .gitignore)
│   ├── raw/         # exports crudos de Health Auto Export (JSON, v2)
│   └── samples/     # ejemplos anonimizados para pruebas
├── src/
│   ├── common/      # constantes, contrato de producto, cliente del modelo (Groq)
│   ├── ingest/      # generación de sesión sintética; lectura de exports reales
│   ├── segment/     # bloques de esfuerzo, señal de velocidad y confianza (determinístico)
│   ├── metrics/     # degradación, recuperación, comparación con historial
│   ├── interpret/   # capa de IA: prompt, parsing y validación del JSON
│   └── verify/      # verificación de cifras y reglas de seguridad
├── evals/           # eval_cases.json + run_evals.py, corre contra src/
└── tests/           # suite pytest de la capa determinística (sin API key)
```

Instalar dependencias con `pip install -r requirements.txt`. Desde la raíz del repo:

- Tests unitarios (rápidos, sin red ni API key): `python -m pytest tests/`
- Evals de calidad del modelo: `GROQ_API_KEY=... python -m evals.run_evals`
  (también `run_evals_real` y `run_evals_synthetic_realista`)

## Privacidad

Los datos de frecuencia cardíaca y ubicación son información sensible. Este repositorio **no versiona datos de sesiones reales**. Cualquier ejemplo incluido está anonimizado y se usa solo para pruebas.

## Equipo

19+1=20 — Juan Pablo Mira · Andrés Jacobo Leal
Proyecto desarrollado en el marco de Makers Fellowship.
