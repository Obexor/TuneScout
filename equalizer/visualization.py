import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

def plot_signal(data, fs, title="Signal"):
    """
    Plot the time-domain signal.

    :param data: Input audio signal
    :param fs: Sampling rate of the audio signal
    :param title: Title of the plot
    """
    time = np.linspace(0, len(data) / fs, len(data))  # Generate time axis
    fig, ax = plt.subplots(figsize=(10, 4))  # Create a figure and axis
    ax.plot(time, data)  # Plot the audio signal
    ax.set_title(title)  # Set the title of the plot
    ax.set_xlabel("Time [s]")  # Set the x-axis label
    ax.set_ylabel("Amplitude")  # Set the y-axis label
    ax.grid()  # Enable grid
    st.pyplot(fig)  # Display the plot in Streamlit

def plot_spectrum(data, fs, title="Spectrum"):
    """
    Plot the frequency-domain spectrum.

    :param data: Input audio signal
    :param fs: Sampling rate of the audio signal
    :param title: Title of the plot
    """
    freq = np.fft.rfftfreq(len(data), d=1 / fs)  # Generate frequency axis
    spectrum = np.abs(np.fft.rfft(data))  # Compute the magnitude spectrum
    fig, ax = plt.subplots(figsize=(10, 4))  # Create a figure and axis
    ax.plot(freq, spectrum)  # Plot the magnitude spectrum
    ax.set_title(title)  # Set the title of the plot
    ax.set_xlabel("Frequency [Hz]")  # Set the x-axis label
    ax.set_ylabel("Magnitude")  # Set the y-axis label
    ax.grid()  # Enable grid
    st.pyplot(fig)  # Display the plot in Streamlit

