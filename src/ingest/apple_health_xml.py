"""Recorre <Workout> del export.xml nativo de Apple Health (streaming,
iterparse) y filtra solo los tipos que Ronin analiza: corridas y deportes de
disco (ultimate). No extrae FC ni GPS todavia -- eso implica correlacionar
<Record>/<WorkoutRoute> con el rango de tiempo de cada workout y queda para un
modulo aparte."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

TIPOS_ELEGIBLES = {
    "HKWorkoutActivityTypeRunning",
    "HKWorkoutActivityTypeDiscSports",
}

_FORMATO_FECHA = "%Y-%m-%d %H:%M:%S %z"


@dataclass
class WorkoutMeta:
    tipo: str
    inicio: datetime
    fin: datetime
    duracion_min: float
    fuente: str


def iter_workouts_elegibles(path: str | Path) -> Iterator[WorkoutMeta]:
    """Recorre export.xml por streaming y devuelve, uno a uno, los workouts
    cuyo workoutActivityType esta en TIPOS_ELEGIBLES. No carga el archivo
    completo en memoria: cada elemento se libera (`clear()`) apenas se lee."""
    for _event, elem in ET.iterparse(path, events=("end",)):
        if elem.tag == "Workout":
            tipo = elem.get("workoutActivityType")
            if tipo in TIPOS_ELEGIBLES:
                yield WorkoutMeta(
                    tipo=tipo,
                    inicio=datetime.strptime(elem.get("startDate"), _FORMATO_FECHA),
                    fin=datetime.strptime(elem.get("endDate"), _FORMATO_FECHA),
                    duracion_min=float(elem.get("duration")),
                    fuente=elem.get("sourceName"),
                )
        elem.clear()
