"""Genera la cache de interpretaciones de la demo llamando al modelo de verdad.

Correr UNA vez con red antes de presentar:

    GROQ_API_KEY=... python -m scripts.precalentar_cache

Guarda en `app/cache/` la salida real del modelo para cada combinacion de
sesion x nota predefinida. Despues la demo puede correr con
`RONIN_MODO=cache python -m app.server` sin red y sin riesgo.

No inventa texto: si el modelo no responde, el caso queda sin cache y la demo
lo dira en pantalla en vez de mostrar una lectura falsa."""

from app.analysis import analizar
from app.presets import NOTAS, SESIONES


def main():
    generados, saltados = 0, 0
    for sesion in SESIONES.values():
        for nota in NOTAS:
            etiqueta = f"{sesion['id']:12s} x {nota['id']}"
            try:
                r = analizar(sesion["id"], nota["rpe"], nota["texto"], modo="vivo")
            except Exception as exc:  # noqa: BLE001
                print(f"[ERROR ] {etiqueta} — {type(exc).__name__}: {str(exc)[:120]}")
                continue
            if r["estado"] == "rechazada":
                print(f"[n/a   ] {etiqueta} — rechazada en {r['etapa_fallida']}, no usa modelo")
                saltados += 1
            else:
                print(f"[cache ] {etiqueta} — fuente {r['fuente_interpretacion']}, "
                      f"revision={r['salida']['requiere_revision']}")
                generados += 1
    print(f"\n{generados} interpretaciones en cache, {saltados} casos sin modelo (rechazo deterministico).")


if __name__ == "__main__":
    main()
