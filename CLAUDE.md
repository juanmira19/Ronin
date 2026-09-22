# Ronin — contexto para Claude

Última actualización: 2026-09-22.

Este archivo existe para que una sesión nueva entienda el proyecto sin releer
todo el repo. Si cambias algo estructural, actualízalo en el mismo commit.

---

## Qué es Ronin

Análisis de rendimiento para **deportes intermitentes** (ultimate frisbee,
fútbol). El reloj te dice "7,4 km a ritmo 7:12" después de un partido; ese dato
no significa nada, porque no corriste 7 km a ritmo constante sino decenas de
esfuerzos máximos con recuperaciones incompletas. El promedio borra justo lo
que importa.

Ronin lee la serie temporal (FC + velocidad) más una lectura subjetiva del
jugador, y devuelve cuántos bloques de esfuerzo hubo, si la intensidad cayó, si
la recuperación empeoró, y qué priorizar esta semana.

**Producto, no salud.** No diagnostica ni da consejo médico. Cuando hay duda,
marca `requiere_revision` y la decisión es del jugador.

---

## La regla central: el reparto sistema / IA

**No la reabras sin hablarlo con el humano.**

- **El sistema (código determinístico) calcula TODOS los números.** Segmentación
  de bloques, degradación, recuperación, divergencia, comparación con historial,
  confianza de la segmentación.
- **La IA solo redacta.** Recibe las métricas ya calculadas —nunca datos
  crudos— y escribe tres campos: `lectura_sesion`, `recomendacion_semana`,
  `alertas`. Los otros cinco campos del contrato los arma el sistema.
- **Después se verifica.** `verificar_cifras` compara cada número del texto
  generado contra la lista de cifras que el sistema calculó (tolerancia ±1). Si
  aparece una intrusa, el texto se descarta entero.

Corolario práctico: **nunca metas una cifra nueva al prompt** sin agregarla a
`cifras_permitidas`, y cada cifra que agregas ahí debilita el verificador para
todas las demás. Por eso `calidad_segmentacion` devuelve etiquetas y frases,
nunca números.

---

## Contrato de salida — ocho campos, fijos

Definido en `src/common/contract.py`. No se negocia sin conversación.

| Campo | Contenido |
|---|---|
| `lectura_sesion` | 2-3 frases en lenguaje del jugador, máx 400 caracteres |
| `bloques_esfuerzo` | `{cantidad, duracion_media_seg, distribucion, confianza}` |
| `degradacion` | `{pico_pct, recuperacion_pct}` |
| `comparacion_historial` | objeto o `null` si hay menos de 2 sesiones previas |
| `divergencia_percepcion` | `alineado` \| `percibio_mas` \| `percibio_menos` |
| `recomendacion_semana` | solo entrenamiento, prohibido lenguaje médico |
| `alertas` | lista de `{tipo, mensaje, severidad}`, puede estar vacía |
| `requiere_revision` | `true` obligatorio si alguna alerta es de severidad alta |

`contract_check()` valida forma y reglas. Severidad `alta` está reservada a
molestia física y patrón repetido; una degradación o una divergencia son
`atencion` como máximo.

---

## Decisiones cerradas

- **Bloques, no sprints.** La FC tiene 15-30 s de latencia y el GPS pierde
  precisión en cambios de dirección. Contar sprints no es honesto con este
  hardware; los bloques (≈ los puntos jugados) sí son detectables.
- **Ningún umbral absoluto de velocidad.** Uno fijo en km/h penaliza al jugador
  lento; uno relativo a su máxima invierte el resultado. La intermitencia se
  mide con `numero_efectivo_bloques` = `(Σd)² / Σd²`, que es adimensional.
- **La FCmax no se pide ni se estima por edad.** Se deriva de la mayor FC
  sostenida que el propio jugador alcanzó (`src/perfil/fcmax.py`), con mediana
  móvil de 25 s para que un pico del sensor no fije un techo falso. Con menos de
  3 sesiones se marca provisional y la confianza no puede ser `alta`.
  Un perfil que declare `fc_max` explícitamente manda: así los evals no se mueven.
- **El sistema dice cuánto confía.** `alta` / `media` / `baja`. Prefiere decir
  "esto no lo segmenté bien" antes que entregar un análisis que parece sólido.
- **Lo subjetivo pesa.** Molestia física reportada levanta alerta alta sin
  importar lo que digan las métricas.
- **La nota del jugador es dato, no instrucción.** Si contiene órdenes dirigidas
  al modelo, se ignoran Y se levanta alerta alta: intentar forzar permiso para
  jugar lesionado ya es señal de riesgo.

---

## Qué está medido y qué es hipótesis

Distinguirlo es parte del proyecto. No lo borres para que algo se vea mejor.

**Medido:** la segmentación funciona sobre exports con forma real (timestamps
irregulares, velocidad GPS). La sesión real disponible es una corrida continua y
el sistema la **rechaza correctamente**, sin inventar bloques.

**Hipótesis del equipo, no datos de campo** (marcadas así en
`src/common/constants.py`): `UMBRAL_MOVIMIENTO_KMH`, `PERCENTIL_VELOZ`,
`LATENCIA_FC_SEG`, `SOLAPE_MIN_CONFIABLE`, `FRAC_INTERPOLADA_MAX`,
`PAUSA_MAX_ENTRE_TRAMOS_SEG` (sale de una sola sesión real).

**Ningún umbral se ajusta para hacer pasar un eval.** Si un eval falla, o el
código está mal o el eval está mal; se arregla el que corresponda y se explica.

**Primer partido real, 2026-09-04** (export de Apple Salud de Juan Pablo):
51 min en dos workouts, sin GPS. El sistema lo lee como intermitente, 13 bloques,
confianza `media`. Es **una** sesión, sin velocidad GPS: no alcanza para calibrar
las hipótesis de arriba. `recuperacion_pct` sale en ~101 %, lo que refuerza la
debilidad 1. El sample `partido_sintetico_2026-09-01.json` sigue siendo el caso
feliz de la demo. Los datos reales viven en `data/raw/` y no se versionan.

---

## Debilidades conocidas

1. **`recuperacion_pct` es frágil.** Se mueve entre +15 % y +40 % dentro del
   rango de error razonable de la FCmax, mientras `pico_pct` apenas se inmuta.
   Es la métrica con menos confianza del producto.
2. **Sensibilidad a la FCmax.** Un error de 14 ppm hacia arriba baja los bloques
   de 15 a 8 e invierte la conclusión de degradación. Por eso se deriva de datos.
3. **`export.xml` no trae GPS.** Las rutas van en `workout-routes/*.gpx`, en una
   carpeta aparte del zip de Apple Health. Sin ellas no hay señal de velocidad y
   la confianza queda topada en `media`.
4. **Velocidad derivada de distancia no cuenta como señal.** `tiene_velocidad`
   la descarta por diseño (confianza topada en `media`), aunque la del Watch en
   `export.xml` viene cada ~3 s. Revisar esa política exige hablarlo.

---

## Flujo de producto decidido

El usuario **no exporta ni sube archivos**. Configura una vez el envío
automático y se olvida.

Health Auto Export sincroniza **por horario, no al terminar el entrenamiento**,
e iOS no deja leer datos de salud con el teléfono bloqueado. O sea: la sesión
llega sola pero **tarde y a hora impredecible**. De ahí la decisión de diseño:

- **La sensación se pide en caliente**, apenas termina el partido, porque si se
  espera al archivo la nota pierde valor.
- **El dato llega después** y se empareja por marca de tiempo.

Son dos momentos separados a propósito. `export.xml` sirve como **bootstrap de
onboarding** (trae todo el historial de una vez, útil para `comparacion_historial`
y para calibrar la FCmax desde el día uno); Health Auto Export para las sesiones
nuevas.

**Onboarding (hecho):** el jugador sube el zip una vez y no elige nada.
`onboarding()` en `src/ingest/apple_health_xml.py` lo lee sin descomprimir, se
queda **solo con `DiscSports`**, une los workouts del mismo reloj separados por
menos de `PAUSA_MAX_ENTRE_TRAMOS_SEG` (el reloj corta un partido en partes) y
descarta lo que dura menos de 15 min. La pantalla lista solo los partidos y
cuenta lo descartado en una línea. Lo importado queda en `data/raw/importadas/`.
Falta: Health Auto Export para las sesiones nuevas.

---

## Cómo correr

Requiere **Python 3.9 o superior** (el Mac del equipo corre 3.9.6 del sistema).
No uses sintaxis de 3.10+: `X | None` en anotaciones revienta al importar. Usa
`Optional[X]`, o `from __future__ import annotations`.

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python -m pytest tests/              # 137 tests, sin red ni API key
python -m app.server                 # demo en http://127.0.0.1:8000
RONIN_MODO=cache python -m app.server # demo sin red
python -m scripts.precalentar_cache  # regenera la cache llamando al modelo
python -m evals.run_evals            # y run_evals_real / run_evals_synthetic_realista
```

`GROQ_API_KEY` se lee del `.env` automáticamente (`load_dotenv` en
`src/common/llm.py`); no hace falta exportarla.

---

## Estructura

```
src/
  common/    constantes, contrato, cliente Groq
  ingest/    health_auto_export (JSON), apple_health_xml (zip/export.xml ->
             partidos anonimizados), anonymize, synthetic
  segment/   blocks (bloques), velocidad (señal), calidad (confianza)
  metrics/   session (degradación, recuperación, divergencia, historial)
  perfil/    fcmax (FCmax derivada de las sesiones del jugador)
  interpret/ prototype (prompt, llamada al modelo, ensamblado del contrato),
             preguntas (preguntas sugeridas despues de la lectura)
  verify/    validate (validación de entrada, verificación de cifras)
app/         API FastAPI + página de la demo. NO contiene lógica de producto:
             presets, analysis (orquesta src/), lenguaje (métricas → frases),
             llm_cache (cache de salidas reales), server, static/index.html
evals/       eval_cases.json (5 casos) + 3 runners con sus results.md
tests/       137 tests, corren sin red ni API key
docs/        arquitectura.md (diagrama Mermaid), demo.md (guion de 6 min)
data/        samples/ anonimizados (versionados); raw/ con exports reales e
             importadas/ NO se versiona (ver .gitignore)
```

**`app/` no duplica lógica.** Si tocas `src/segment/blocks.py`, la demo cambia
sola. Mantenlo así: cualquier cálculo nuevo va en `src/`, no en `app/`.

`app/lenguaje.py` traduce `METRICAS.conclusiones` a segunda persona para la
pantalla. Vive en presentación a propósito: el texto de `src/metrics` lo consume
el prompt y cambiarlo movería los evals.

---

## La demo

Pantalla de producto, no dashboard. Lo primero y más grande es lo que escribió
la IA; los hallazgos van en frases ("Perdiste fuerza en la segunda mitad") en
vez de porcentajes; la gráfica de FC y el JSON quedan plegados.

Tres sesiones, tres comportamientos:

- **Partido de ultimate** → caso feliz: 15 bloques, confianza alta.
- **Corrida continua** (sesión real de Apple Watch) → rechazo en segmentación:
  un solo bloque, se detiene antes de llamar al modelo.
- **Sesión incompleta** → rechazo en validación: 10 min, mínimo 15.

Además, los partidos que se importan desde el zip (`POST /api/onboarding`)
aparecen en la bandeja como sesiones reales.

**Lo que aporta la IA** (lo que el código no puede): `lectura_sesion` cruza la
nota del jugador con lo que midió el reloj (confirma o contradice), lo traduce a
lo que suele pasar en la cancha como consecuencia probable (Ronin no ve las
jugadas; nunca habla de posiciones: no se le pasan ni puede suponerlas) y
propone una acción para el próximo partido. Va arriba, destacada.

**Preguntas sugeridas** (`POST /api/preguntar`, `src/interpret/preguntas.py`):
tres preguntas fijas, no chat libre. Parten del mismo paquete que la lectura
(sin `CALIDAD_SEGMENTACION`, que inducía explicaciones inventadas), sobre la
lectura ya mostrada, y se verifican contra las mismas `cifras_permitidas`. El
chat libre queda pendiente: exige guardrails por turno y sus evals.

Cuatro notas predefinidas, textuales de `evals/eval_cases.json`, que disparan
los guardrails en vivo. Verificado: la nota normal no levanta alerta y las
cuatro de riesgo —ambigua, dolor de rodilla, dolor de isquio e intento de
manipulación— levantan `molestia_fisica` de severidad alta.

Lo que hay en `app/cache/` son salidas reales del modelo, guardadas por
`scripts/precalentar_cache.py` o por la propia demo al correr en vivo. La
carpeta crece sola. **Nunca se escribe una interpretación a mano** para que la
demo se vea bien: si no hay modelo ni caché, la pantalla lo dice en vez de
inventar.

---

## Convenciones

- **Mensajes de commit en español**, cortos, en imperativo ("Agrega parser de
  workouts", no "Se agregó..."). Sin emojis. El cuerpo explica **por qué**, no
  qué archivos cambiaron.
- **No agregues líneas de atribución a Claude** (`Co-Authored-By`,
  `Claude-Session`) a los commits de este repo.
- Sin emojis en código ni en la interfaz.
- Textos de la UI en español, tono directo, sin exclamaciones ni motivación.
- Los datos de FC y ubicación son sensibles: `data/` no se versiona y los
  samples van anonimizados (sin lat/lon, sin identificadores, `t` relativo).

---

## Equipo y ramas

19+1=20 — Juan Pablo Mira (`Dev_Pablo`) · Andrés Jacobo Leal (`DevJacobo`).
Makers Fellowship. Repo: `github.com/juanmira19/Ronin`.

Reparto actual: Jacobo lleva el pipeline determinístico, la interpretación, los
evals, la demo y (acordado con Juan Pablo) la ingesta desde `export.xml`: ya
correlaciona `<Record>` de FC y distancia con cada partido; falta leer las rutas
`workout-routes/*.gpx`.

Se trabaja por rama y PR a `main`, no push directo.
