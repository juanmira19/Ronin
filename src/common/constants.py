SAMPLE_DT = 5  # segundos entre muestras de FC (Apple Watch en workout muestrea ~cada 5 s)

# --- Velocidad -------------------------------------------------------------
# Los umbrales de abajo son HIPOTESIS del equipo, no valores medidos en campo.
# Se re-derivan cuando exista una sesion real de ultimate/futbol grabada (ver
# TEAM_ROTATION.md: sigue siendo la dependencia bloqueante del proyecto).
# Ninguno se ajusta para hacer pasar un eval.
#
# No hay umbral de sprint, a proposito. Uno absoluto (14 km/h) penalizaba al
# jugador lento, y uno relativo a su propia velocidad maxima invierte el
# resultado: correr es sostener velocidad alta, mientras que un partido es
# estar parado con explosiones cortas. La intermitencia se mide con la forma
# del esfuerzo (`numero_efectivo_bloques` en src/segment/blocks.py), que es
# adimensional.

UMBRAL_MOVIMIENTO_KMH = 3.0  # HIPOTESIS: frontera entre caminar y trotar. Unico
                             # umbral absoluto de velocidad que queda, y solo se
                             # usa para refinar limites de bloques.
PERCENTIL_VELOZ = 90  # HIPOTESIS: "lo rapido" de una sesion, relativo a ella misma

# HIPOTESIS: punto medio del rango 15-30 s de latencia de la FC que declara el
# README. NO esta calibrado: el desfase de ~5 s que se mide por correlacion
# cruzada en el partido sintetico es artefacto del generador (tau=2.5 s), no
# fisiologia. Calibrarlo de verdad exige una sesion de partido real.
LATENCIA_FC_SEG = 20

SOLAPE_MIN_CONFIABLE = 0.50  # HIPOTESIS: solape minimo sprint-vs-bloques para confiar
FRAC_INTERPOLADA_MAX = 0.05  # HIPOTESIS: por encima de esto la serie tiene demasiado relleno
GAP_INTERPOLADO_SEG = 60  # huecos mas grandes que esto se interpolan igual, pero se reportan
