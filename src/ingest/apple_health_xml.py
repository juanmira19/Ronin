"""Lee el export nativo de Apple Health (el zip o el export.xml suelto) por
streaming (iterparse) y arma sesiones en el mismo formato anonimizado que
consume `load_session()` (src/ingest/health_auto_export.py).

Es el bootstrap del onboarding: el jugador sube el zip una vez y el sistema se
queda solo con sus partidos. Sin GPS: las rutas van en workout-routes/*.gpx y
por ahora no se leen, asi que la velocidad sale de la distancia del Watch."""

from __future__ import annotations

import xml.etree.ElementTree as ET
import zipfile
from collections import Counter
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from src.common.constants import DURACION_MIN_SESION_MIN, PAUSA_MAX_ENTRE_TRAMOS_SEG

TIPOS_ELEGIBLES = {
    "HKWorkoutActivityTypeRunning",
    "HKWorkoutActivityTypeDiscSports",
}

# El onboarding solo muestra partidos. Correr no es un deporte intermitente y el
# sistema ya lo rechaza en segmentacion; ensenarlo en la lista seria ruido.
TIPOS_PARTIDO = {"HKWorkoutActivityTypeDiscSports"}

_FC = "HKQuantityTypeIdentifierHeartRate"
_DISTANCIA = "HKQuantityTypeIdentifierDistanceWalkingRunning"
_A_KM = {"km": 1.0, "m": 0.001, "mi": 1.609344}

_FORMATO_FECHA = "%Y-%m-%d %H:%M:%S %z"


@dataclass
class WorkoutMeta:
    tipo: str
    inicio: datetime
    fin: datetime
    duracion_min: float
    fuente: str


@dataclass
class Partido:
    """Uno o mas workouts consecutivos que son el mismo partido: el reloj lo
    corta cuando alguien pausa o reinicia el workout entre puntos."""
    tramos: list[WorkoutMeta] = field(default_factory=list)

    @property
    def inicio(self) -> datetime:
        return self.tramos[0].inicio

    @property
    def fin(self) -> datetime:
        return self.tramos[-1].fin

    @property
    def fuente(self) -> str:
        return self.tramos[0].fuente

    @property
    def duracion_min(self) -> float:
        return (self.fin - self.inicio).total_seconds() / 60


@contextmanager
def _abrir(path: str | Path):
    """Abre export.xml, directo del zip si hace falta, sin descomprimirlo a disco:
    el XML de un historial de pocos anos ya pasa de 300 MB."""
    path = Path(path)
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as z:
            nombre = next((n for n in z.namelist()
                           if n == "export.xml" or n.endswith("/export.xml")), None)
            if nombre is None:
                raise ValueError("El zip no trae export.xml: no parece un export de Apple Health")
            with z.open(nombre) as f:
                yield f
    elif path.suffix == ".xml":
        with open(path, "rb") as f:
            yield f
    else:
        raise ValueError("No es un zip de Apple Health")


def _fecha(texto: str) -> datetime:
    return datetime.strptime(texto, _FORMATO_FECHA)


def _iter_workouts(path: str | Path) -> Iterator[WorkoutMeta]:
    """Todos los <Workout>, de cualquier tipo. Cada elemento se libera
    (`clear()`) apenas se lee para no cargar el archivo en memoria."""
    with _abrir(path) as f:
        for _event, elem in ET.iterparse(f, events=("end",)):
            if elem.tag == "Workout":
                yield WorkoutMeta(
                    tipo=elem.get("workoutActivityType"),
                    inicio=_fecha(elem.get("startDate")),
                    fin=_fecha(elem.get("endDate")),
                    duracion_min=float(elem.get("duration")),
                    fuente=elem.get("sourceName"),
                )
            elem.clear()


def iter_workouts_elegibles(path: str | Path, tipos=TIPOS_ELEGIBLES) -> Iterator[WorkoutMeta]:
    """Los workouts cuyo workoutActivityType esta en `tipos`."""
    return (w for w in _iter_workouts(path) if w.tipo in tipos)


def agrupar_tramos(workouts: list[WorkoutMeta],
                   pausa_max_seg: int = PAUSA_MAX_ENTRE_TRAMOS_SEG) -> list[Partido]:
    """Une workouts consecutivos del mismo tipo y del mismo reloj cuando la pausa
    entre uno y otro no pasa de `pausa_max_seg`."""
    partidos: list[Partido] = []
    for w in sorted(workouts, key=lambda x: x.inicio):
        actual = partidos[-1] if partidos else None
        if (actual and w.tipo == actual.tramos[-1].tipo and w.fuente == actual.fuente
                and (w.inicio - actual.fin).total_seconds() <= pausa_max_seg):
            actual.tramos.append(w)
        else:
            partidos.append(Partido([w]))
    return partidos


def extraer_series(path: str | Path, partidos: list[Partido]) -> list[dict]:
    """Una pasada por los <Record> de FC y distancia, asignando cada uno al
    partido en cuyo rango cae. Solo cuentan los del mismo reloj que grabo el
    workout: el iPhone registra su propia distancia y sumarla la duplicaria.

    Devuelve un dict por partido, anonimizado igual que `anonymize_dict()`:
    `t` en segundos desde el inicio, sin fechas ni identificadores."""
    series = [{"heart_rate": [], "distance_km": []} for _ in partidos]
    dias = {d.strftime("%Y-%m-%d") for p in partidos for d in (p.inicio, p.fin)}

    with _abrir(path) as f:
        for _event, elem in ET.iterparse(f, events=("end",)):
            if elem.tag == "Record" and elem.get("type") in (_FC, _DISTANCIA):
                inicio_txt = elem.get("startDate", "")
                # filtro barato por dia antes de parsear la fecha: el export
                # trae anos de registros y solo interesan unos minutos
                if inicio_txt[:10] in dias:
                    _asignar(elem, _fecha(inicio_txt), partidos, series)
            elem.clear()

    return [_sesion(p, s) for p, s in zip(partidos, series)]


def _asignar(elem, inicio_reg: datetime, partidos: list[Partido], series: list[dict]) -> None:
    for p, s in zip(partidos, series):
        if not (p.inicio <= inicio_reg <= p.fin and elem.get("sourceName") == p.fuente):
            continue
        if elem.get("type") == _FC:
            s["heart_rate"].append({"t": int((inicio_reg - p.inicio).total_seconds()),
                                    "bpm": round(float(elem.get("value")), 1)})
        else:
            # la distancia viene por incrementos; se fecha al final del tramo
            fin_reg = _fecha(elem.get("endDate"))
            km = float(elem.get("value")) * _A_KM.get(elem.get("unit"), 1.0)
            s["distance_km"].append({"t": int((fin_reg - p.inicio).total_seconds()),
                                     "km": round(km, 5)})
        return


def _sesion(p: Partido, s: dict) -> dict:
    return {
        "tipo_sesion": "partido",
        "duracion_seg": int((p.fin - p.inicio).total_seconds()),
        "tramos": [{"inicio_seg": int((w.inicio - p.inicio).total_seconds()),
                    "fin_seg": int((w.fin - p.inicio).total_seconds())} for w in p.tramos],
        "heart_rate": sorted(s["heart_rate"], key=lambda m: m["t"]),
        "route_speed": [],
        "distance_km": sorted(s["distance_km"], key=lambda m: m["t"]),
    }


def onboarding(path: str | Path,
               pausa_max_seg: int = PAUSA_MAX_ENTRE_TRAMOS_SEG,
               duracion_min: float = DURACION_MIN_SESION_MIN) -> dict:
    """Del export completo, solo los partidos que se pueden analizar.

    Dos pasadas por el XML: en el export los <Record> van antes que los
    <Workout>, asi que hay que conocer los partidos antes de buscar su FC.

    Devuelve `partidos` (cada uno con su `sesion` lista para `load_session`) y
    `descartados`, que solo cuenta lo que se dejo fuera y por que."""
    tipos = Counter()
    candidatos = []
    for w in _iter_workouts(path):
        if w.tipo in TIPOS_PARTIDO:
            candidatos.append(w)
        else:
            tipos[w.tipo] += 1

    agrupados = agrupar_tramos(candidatos, pausa_max_seg)
    largos = [p for p in agrupados if p.duracion_min >= duracion_min]
    sesiones = extraer_series(path, largos) if largos else []

    partidos = [{"partido": p, "sesion": s} for p, s in zip(largos, sesiones) if s["heart_rate"]]
    return {
        "partidos": partidos,
        "descartados": {
            "no_son_partidos": sum(tipos.values()),
            "demasiado_cortos": len(agrupados) - len(largos),
            "sin_frecuencia_cardiaca": len(largos) - len(partidos),
        },
    }
