"""Plumbing para llamar al modelo (Groq) y forzar JSON schema estricto.
Extraido de la celda 2 y 9 del notebook."""

import json
import os
import re

from pydantic import BaseModel

MODEL = "openai/gpt-oss-120b"

_client = None


def get_client():
    """Cliente Groq perezoso: solo exige GROQ_API_KEY cuando de verdad se llama al modelo,
    no al importar el modulo (permite correr la capa deterministica sin credenciales)."""
    global _client
    if _client is None:
        from groq import Groq

        api_key = os.getenv("GROQ_API_KEY")
        assert api_key, "Falta GROQ_API_KEY"
        _client = Groq(api_key=api_key)
    return _client


def schema_strict(model: type[BaseModel]) -> dict:
    """Groq con strict:true exige additionalProperties:false y todos los campos required.
    Solo se cierran los objetos que declaran properties: un dict de claves libres
    no tiene properties y agregarle required lo vuelve invalido."""
    s = model.model_json_schema()

    def cerrar(node):
        if isinstance(node, dict):
            if node.get("type") == "object" and node.get("properties"):
                node["additionalProperties"] = False
                node["required"] = sorted(node["properties"].keys())
            for v in node.values():
                cerrar(v)
        elif isinstance(node, list):
            for v in node:
                cerrar(v)

    cerrar(s)
    return s


def ask_model_json(system_prompt: str, payload: dict, model_cls=None,
                    max_tokens: int = 4000, temperature: float = 0.0) -> dict:
    kwargs = {}
    if model_cls is not None:
        kwargs["response_format"] = {
            "type": "json_schema",
            "json_schema": {"name": model_cls.__name__.lower(),
                             "strict": True,
                             "schema": schema_strict(model_cls)},
        }
    else:
        kwargs["response_format"] = {"type": "json_object"}

    response = get_client().chat.completions.create(
        model=MODEL,
        max_completion_tokens=max_tokens,   # incluye los tokens de razonamiento
        reasoning_effort="low",
        temperature=temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
        ],
        **kwargs,
    )
    text = response.choices[0].message.content
    if not text or not text.strip():
        raise RuntimeError("Respuesta vacia: sube max_tokens, el razonamiento "
                            "consumio el presupuesto de tokens.")
    text = re.sub(r"^```json\s*|\s*```$", "", text.strip())
    return json.loads(text)
