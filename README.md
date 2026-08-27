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
| `bloques_esfuerzo` | Cantidad, duración media y distribución por intensidad |
| `degradacion` | Caída del pico entre primera y segunda mitad; empeoramiento de la recuperación |
| `comparacion_historial` | Qué cambió respecto a las últimas 5 sesiones del mismo tipo |
| `divergencia_percepcion` | `alineado` · `percibio_mas` · `percibio_menos` |
| `recomendacion_semana` | Qué priorizar en los próximos días |
| `alertas` | Señales que merecen atención (puede estar vacía) |
| `requiere_revision` | Booleano: cuándo hace falta mirada humana |

## Principios de diseño

**La IA no calcula números.** La detección de bloques de esfuerzo y todas las métricas derivadas son determinísticas: las hace el sistema. La IA interpreta, contextualiza y explica. Antes de mostrar cualquier resultado, el sistema verifica que las cifras del texto generado coincidan con las calculadas.

**Bloques, no sprints.** La frecuencia cardíaca tiene entre 15 y 30 segundos de latencia y el GPS pierde precisión con cambios de dirección bruscos. Contar sprints individuales no es honesto con este hardware. Ronin detecta bloques de esfuerzo —que en ultimate corresponden aproximadamente a los puntos jugados— porque eso sí es detectable con confianza.

**Lo subjetivo pesa.** El reloj no sabe cómo te sentiste. Mismo ritmo, misma frecuencia cardíaca, peor sensación es una señal real, y ninguna app que solo lea datos de sensores puede verla. Si el jugador reporta molestia física, eso pesa por encima de cualquier métrica.

**Rendimiento, nunca salud.** Ronin no diagnostica ni da consejo médico. Cuando los umbrales se cruzan, no adivina: marca `requiere_revision` y sugiere descanso.

## Estado

Tesis de problema, flujo y contrato de salida definidos. La capa determinística
(segmentación, métricas, validación) y la capa de interpretación con IA ya están
implementadas en `src/` y pasan los 5 casos de `evals/`. Pendiente: correr todo
esto contra una sesión real de Apple Watch — hoy corre sobre datos sintéticos.

## Estructura actual

```
ronin/
├── data/            # datos de sesiones — NO se versiona (ver .gitignore)
│   ├── raw/         # exports crudos de Health Auto Export (JSON, v2)
│   └── samples/     # ejemplos anonimizados para pruebas
├── src/
│   ├── common/      # constantes, contrato de producto, cliente del modelo (Groq)
│   ├── ingest/      # generación de sesión sintética; lectura de exports reales (pendiente)
│   ├── segment/     # detección de bloques de esfuerzo (determinístico)
│   ├── metrics/     # degradación, recuperación, comparación con historial
│   ├── interpret/   # capa de IA: prompt, parsing y validación del JSON
│   └── verify/      # verificación de cifras y reglas de seguridad
├── evals/           # eval_cases.json + run_evals.py, corre contra src/
└── tests/
```

Instalar dependencias con `pip install -r requirements.txt`. Correr los evals con
`GROQ_API_KEY=... python -m evals.run_evals` desde la raíz del repo.

## Privacidad

Los datos de frecuencia cardíaca y ubicación son información sensible. Este repositorio **no versiona datos de sesiones reales**. Cualquier ejemplo incluido está anonimizado y se usa solo para pruebas.

## Equipo

19+1=20 — Juan Pablo Mira · Andrés Jacobo Leal
Proyecto desarrollado en el marco de Makers Fellowship.
