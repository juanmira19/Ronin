# Caché de interpretaciones

Salidas **reales** del modelo, guardadas por `scripts/precalentar_cache.py` para
que la demo funcione sin red. La clave de cada archivo es el hash del payload
exacto que recibió el modelo, así que cambiar el RPE o la nota genera otra
entrada: la caché nunca devuelve la lectura de otra sesión.

Regla: aquí no se escribe texto a mano. Si no hay modelo ni caché, la demo lo
dice en pantalla en vez de inventar una lectura.
