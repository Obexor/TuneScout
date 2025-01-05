import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

def plot_signal(data, fs, title="Signal"):

    time = np.linspace(0, len(data)/fs, len(data))
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(time, data)
    ax.set_title(title)
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Amplitude")
    ax.grid()
    st.pyplot(fig)  # Streamlit-kompatibel anzeigen


def plot_spectrum(data, fs, title="Spectrum"):

    freq = np.fft.rfftfreq(len(data), d=1/fs)
    spectrum = np.abs(np.fft.rfft(data))
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(freq, spectrum)
    ax.set_title(title)
    ax.set_xlabel("Frequency [Hz]")
    ax.set_ylabel("Magnitude")
    ax.grid()
    st.pyplot(fig)  # Streamlit-kompatibel anzeigen

