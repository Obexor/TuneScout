# pipeline/settings.py

SAMPLE_RATE = 44100  # Beispiel-Sample-Rate
FFT_WINDOW_SIZE = 0.02  # z.B. 20 ms
PEAK_BOX_SIZE = 20  # Größe der Region für die Peak-Suche
POINT_EFFICIENCY = 0.1  # Effizienz für Peaks

# Diese Werte fehlen anscheinend:
TARGET_T = 50  # Zeitfenster (ein Beispielwert)
TARGET_F = 30  # Frequenzfenster (ein Beispielwert)
TARGET_START = 5  # Startbereich (ein Beispielwert)