# settings.py

# Sample rate for audio (in Hz)
SAMPLE_RATE = 44100

# Number of audio channels (mono recording)
CHANNELS = 1  # 1 für Mono, 2 für Stereo

# CHUNK (Frames per Buffer)
CHUNK = 1024

# FFT window size in seconds (affects spectrogram resolution)
FFT_WINDOW_SIZE = 0.02  # 20ms

# Size of the box for peak detection (frequency × time box)
PEAK_BOX_SIZE = 30

# Proportion of theoretical peaks to keep (for performance vs accuracy)
POINT_EFFICIENCY = 0.5

# Target zone parameters (used for hash generation)
TARGET_F = 200  # Frequency height
TARGET_T = 1  # Time width
TARGET_START = 0.5  # Target start delay (in seconds)

# Multiprocessing settings
NUM_WORKERS = 4

# Directory to save audio files
SAVE_DIRECTORY = "test/"  # Ordner für Audio-Speicherung