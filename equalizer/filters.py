from scipy.signal import butter, lfilter
import numpy as np

def butter_lowpass_filter(data, cutoff, fs, order=5, gain=1.0):
    """
    Apply a low-pass filter to the input data.

    :param data: Input audio signal
    :param cutoff: Cutoff frequency for the low-pass filter
    :param fs: Sampling rate of the audio signal
    :param order: Order of the filter
    :param gain: Gain to apply to the filtered signal
    :return: Filtered audio signal with applied gain
    """
    nyquist = 0.5 * fs  # Nyquist frequency
    normal_cutoff = cutoff / nyquist  # Normalized cutoff frequency
    b, a = butter(order, normal_cutoff, btype='low', analog=False)  # Design the filter
    filtered_data = lfilter(b, a, data)  # Apply the filter to the data
    return filtered_data * gain  # Apply bass gain

def butter_highpass_filter(data, cutoff, fs, order=5, gain=1.0):
    """
    Apply a high-pass filter to the input data.

    :param data: Input audio signal
    :param cutoff: Cutoff frequency for the high-pass filter
    :param fs: Sampling rate of the audio signal
    :param order: Order of the filter
    :param gain: Gain to apply to the filtered signal
    :return: Filtered audio signal with applied gain
    """
    nyquist = 0.5 * fs  # Nyquist frequency
    normal_cutoff = cutoff / nyquist  # Normalized cutoff frequency
    b, a = butter(order, normal_cutoff, btype='high', analog=False)  # Design the filter
    filtered_data = lfilter(b, a, data)  # Apply the filter to the data
    return filtered_data * gain  # Apply treble gain

def equalizer(data, freq_range, fs, order=5, gain=1.0):
    """
    Apply a band-pass filter to the input data to act as an equalizer.

    :param data: Input audio signal
    :param freq_range: Tuple containing the low and high cutoff frequencies for the band-pass filter
    :param fs: Sampling rate of the audio signal
    :param order: Order of the filter
    :param gain: Gain to apply to the filtered signal
    :return: Filtered audio signal with applied gain
    """
    low, high = freq_range  # Define band range (e.g., (200, 3000) for midrange)
    nyquist = 0.5 * fs  # Nyquist frequency
    low_normal = low / nyquist  # Normalized low cutoff frequency
    high_normal = high / nyquist  # Normalized high cutoff frequency
    b, a = butter(order, [low_normal, high_normal], btype='band', analog=False)  # Design the band-pass filter
    filtered_data = lfilter(b, a, data)  # Apply the filter to the data
    return filtered_data * gain  # Apply midrange gain
