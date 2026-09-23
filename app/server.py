"""API de Ronin + pagina de demo.

Esta capa no contiene logica de producto: envuelve el mismo pipeline que corren
los evals (`src/`). Es la forma de la API que consumiria la app real.

    python -m app.server            # http://127.0.0.1:8000
    RONIN_MODO=cache python -m app.server   # sin red, solo interpretaciones ya generadas
"""

import os
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.analysis import analizar, catalogo, importar_export, preguntar
from app.llm_cache import InterpretacionNoDisponible
from src.interpret.preguntas import PREGUNTAS
from app.presets import SESIONES

STATIC = Path(__file__).resolve().parent / "static"
MODO_POR_DEFECTO = os.getenv("RONIN_MODO", "auto")  # auto | vivo | cache

app = FastAPI(title="Ronin API", version="0.1.0",
              description="Analisis de sesiones de deportes intermitentes.")


class PeticionAnalisis(BaseModel):
    sesion_id: str = Field(..., description="id de una sesion del catalogo")
    esfuerzo_percibido: int = Field(8, ge=1, le=10)
    nota: str = Field("", max_length=600)
    modo: Optional[str] = Field(None, description="auto | vivo | cache")


@app.get("/api/catalogo")
def get_catalogo():
    return {**catalogo(), "modo": MODO_POR_DEFECTO}


@app.post("/api/analizar")
def post_analizar(peticion: PeticionAnalisis):
    if peticion.sesion_id not in SESIONES:
        raise HTTPException(404, f"Sesion desconocida: {peticion.sesion_id}")
    return analizar(peticion.sesion_id, peticion.esfuerzo_percibido,
                    peticion.nota, modo=peticion.modo or MODO_POR_DEFECTO)


class PeticionPregunta(PeticionAnalisis):
    pregunta_id: str = Field(..., description="id de una pregunta sugerida del catalogo")


@app.post("/api/preguntar")
def post_preguntar(peticion: PeticionPregunta):
    if peticion.sesion_id not in SESIONES:
        raise HTTPException(404, f"Sesion desconocida: {peticion.sesion_id}")
    if peticion.pregunta_id not in PREGUNTAS:
        raise HTTPException(404, f"Pregunta desconocida: {peticion.pregunta_id}")
    try:
        return {"disponible": True,
                **preguntar(peticion.sesion_id, peticion.esfuerzo_percibido, peticion.nota,
                            peticion.pregunta_id, modo=peticion.modo or MODO_POR_DEFECTO)}
    except InterpretacionNoDisponible as exc:
        # Sin modelo ni cache no se inventa la respuesta: la pagina lo dice.
        return {"disponible": False, "motivo": str(exc)}


@app.post("/api/onboarding")
async def post_onboarding(request: Request):
    """Recibe el zip de Apple Salud tal cual (cuerpo crudo, sin multipart) y
    devuelve solo los partidos que encontro. El zip se lee en disco y se borra:
    lo unico que queda son las series anonimizadas de los partidos."""
    with tempfile.NamedTemporaryFile(suffix=".zip") as tmp:
        async for trozo in request.stream():
            tmp.write(trozo)
        tmp.flush()
        try:
            return await run_in_threadpool(importar_export, tmp.name)
        except ValueError as exc:
            raise HTTPException(400, str(exc))


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


app.mount("/static", StaticFiles(directory=STATIC), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=int(os.getenv("PORT", "8000")))
