# settings.py

# Sample rate for audio (in Hz)
SAMPLE_RATE = 44100

# FFT window size in seconds (affects spectrogram resolution)
FFT_WINDOW_SIZE = 0.2  # 20 ms

# Size of the box for peak detection (frequency × time box)
PEAK_BOX_SIZE = 30

# Proportion of theoretical peaks to keep (for performance vs accuracy)
POINT_EFFICIENCY = 0.8

# Target zone parameters (used for hash generation)
TARGET_F = 4000  # Frequency height
TARGET_T = 1.8  # Time width
TARGET_START = 0.05  # Target start delay (in seconds)

# CHUNK (Frames per Buffer)
CHUNK = 1024  # Default buffer size

# Number of workers to use when processing audio
NUM_WORKERS = 24
