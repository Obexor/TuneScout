from scipy.signal import butter, lfilter
import numpy as np

def butter_lowpass_filter(data, cutoff, fs, order=5):
    nyquist = 0.5 * fs
    normal_cutoff = cutoff / nyquist
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return lfilter(b, a, data)

def butter_highpass_filter(data, cutoff, fs, order=5):
    nyquist = 0.5 * fs
    normal_cutoff = cutoff / nyquist
    b, a = butter(order, normal_cutoff, btype='high', analog=False)
    return lfilter(b, a, data)

def equalizer(data, fs, gain_bands):
    freq_data = np.fft.rfft(data)
    freqs = np.fft.rfftfreq(len(data), d=1/fs)

    for band, gain in gain_bands.items():
        band_indices = np.where((freqs >= band[0]) & (freqs <= band[1]))[0]
        freq_data[band_indices] *= gain

    return np.fft.irfft(freq_data)
