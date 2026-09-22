"""Contrato de producto de Ronin, fijado en la Parte 4 del notebook
(19y1_20_Makers_AI_Product_Ronin_1-2.ipynb, celda 11). Estos valores ya fueron
validados por el equipo — no se regeneran en cada corrida."""

PRODUCT_NAME = "Ronin Ultimate Frisbee Session Analyzer"

USER = (
    "Jugador de ultimate frisbee amateur o universitario que entrena varias "
    "veces por semana y ya usa Apple Watch o reloj deportivo"
)

AI_JOB = [
    "Traducir las métricas ya calculadas a lenguaje de cancha",
    "Cruzar la señal objetiva con la nota subjetiva del jugador",
    "Emitir la recomendación de entrenamiento de la semana",
    "Levantar alertas cuando la nota o las métricas lo ameriten",
]

SYSTEM_VALIDATIONS = [
    "Segmentar la serie de FC en bloques de esfuerzo (umbral sobre FC maxima, "
    "duracion minima, fusion de huecos)",
    "Clasificar cada bloque por intensidad",
    "Calcular degradacion del pico entre mitades y recuperacion via HRR60",
    "Evaluar la calidad de la segmentacion con la senal de velocidad y emitir "
    "la alerta de segmentacion dudosa cuando la confianza es baja",
    "Calcular la divergencia entre esfuerzo percibido y carga objetiva",
    "Comparar contra el historial del jugador",
    "Validar la entrada y verificar que el texto del modelo no cite cifras ajenas",
]

HUMAN_DECISION = "Si entrena o descansa cuando requiere_revision es true"

# Los ocho campos del contrato de output. Fijos, no negociables.
OUTPUT_SCHEMA = {
    "lectura_sesion": "string. Interpretacion en lenguaje del jugador, 2-3 frases, max 400 caracteres",
    "bloques_esfuerzo": "object. cantidad, duracion_media_seg, distribucion por intensidad "
                        "y confianza de la segmentacion (alta|media|baja|no_evaluada)",
    "degradacion": "object. pico_pct entre -100 y 100, recuperacion_pct entre -100 y 500",
    "comparacion_historial": "object o null. null si hay menos de 2 sesiones previas del mismo tipo",
    "divergencia_percepcion": "string. alineado | percibio_mas | percibio_menos",
    "recomendacion_semana": "string. Solo entrenamiento, prohibido lenguaje medico",
    "alertas": "array de objetos {tipo, mensaje, severidad}. Puede estar vacio",
    "requiere_revision": "boolean. true obligatorio si alguna alerta es de severidad alta",
}

REQUIRED_FIELDS = set(OUTPUT_SCHEMA.keys())
