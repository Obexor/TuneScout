from scipy.signal import butter, lfilter
import numpy as np

def butter_lowpass_filter(data, cutoff, fs, order=5, gain=1.0):
    nyquist = 0.5 * fs  # Nyquist frequency
    normal_cutoff = cutoff / nyquist
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    filtered_data = lfilter(b, a, data)
    return filtered_data * gain  # Apply bass gain


def butter_highpass_filter(data, cutoff, fs, order=5, gain=1.0):
    nyquist = 0.5 * fs
    normal_cutoff = cutoff / nyquist
    b, a = butter(order, normal_cutoff, btype='high', analog=False)
    filtered_data = lfilter(b, a, data)
    return filtered_data * gain  # Apply treble gain

def equalizer(data, freq_range, fs, order=5, gain=1.0):
    low, high = freq_range  # Define band range (e.g., (200, 3000) for midrange)
    nyquist = 0.5 * fs
    low_normal = low / nyquist
    high_normal = high / nyquist
    b, a = butter(order, [low_normal, high_normal], btype='band', analog=False)
    filtered_data = lfilter(b, a, data)
    return filtered_data * gain  # Apply midrange gain
