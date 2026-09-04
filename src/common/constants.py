SAMPLE_DT = 5  # segundos entre muestras de FC (Apple Watch en workout muestrea ~cada 5 s)

# --- Velocidad -------------------------------------------------------------
# Todos los umbrales de abajo son HIPOTESIS del equipo, no valores medidos en
# campo. Se re-derivan cuando exista una sesion real de ultimate/futbol grabada
# (ver TEAM_ROTATION.md: sigue siendo la dependencia bloqueante del proyecto).
# Ninguno se ajusta para hacer pasar un eval.

UMBRAL_SPRINT_KMH = 14.0  # HIPOTESIS: separa 0.0% (corrida real) de 8.3% (partido sintetico)
UMBRAL_MOVIMIENTO_KMH = 3.0  # HIPOTESIS: frontera entre caminar y trotar
FRAC_SPRINT_MIN_INTERMITENTE = 0.02  # HIPOTESIS: >=2% del tiempo en sprint => patron intermitente

# HIPOTESIS: punto medio del rango 15-30 s de latencia de la FC que declara el
# README. NO esta calibrado: el desfase de ~5 s que se mide por correlacion
# cruzada en el partido sintetico es artefacto del generador (tau=2.5 s), no
# fisiologia. Calibrarlo de verdad exige una sesion de partido real.
LATENCIA_FC_SEG = 20

SOLAPE_MIN_CONFIABLE = 0.50  # HIPOTESIS: solape minimo sprint-vs-bloques para confiar
FRAC_INTERPOLADA_MAX = 0.05  # HIPOTESIS: por encima de esto la serie tiene demasiado relleno
GAP_INTERPOLADO_SEG = 60  # huecos mas grandes que esto se interpolan igual, pero se reportan
