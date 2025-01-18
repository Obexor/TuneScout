import streamlit as st
import wave
import numpy as np
import soundfile as sf
from .visualization import plot_signal, plot_spectrum

def equalizer_features():
    st.header("Equalizer")
    st.write("This feature allows you to modify and equalize uploaded or streamed WAV/MP3 files in real-time.")

    # Option to select between uploading a file or streaming from AWS S3
    input_mode = st.radio(
        "Choose Source",
        options=["Upload a File", "Stream from AWS S3"],
        index=0
    )

    uploaded_file = None
    uploaded_file = st.file_uploader("Upload a WAV or MP3 file", type=["wav", "mp3"])
    # If a file is either uploaded or streamed, proceed with processing
    if uploaded_file:
        st.subheader("Equalizer Settings")
        bass_gain = st.slider("Bass Gain (dB)", -10, 10, 0)
        midrange_gain = st.slider("Midrange Gain (dB)", -10, 10, 0)
        treble_gain = st.slider("Treble Gain (dB)", -10, 10, 0)

        # Process the file
        try:
            import tempfile
            import wave

            # Handle WAV and MP3 files
            file_type = uploaded_file.name.split(".")[-1].lower()

            if file_type == "wav":
                with wave.open(uploaded_file, "rb") as wav_file:
                    params = wav_file.getparams()
                    raw_data = wav_file.readframes(params.nframes)
                    frame_rate = params.framerate
            elif file_type == "mp3":
                data, frame_rate = sf.read(uploaded_file)
                raw_data = (data * (2 ** 15 - 1)).astype(np.int16).tobytes()

            # Visualize the original signal
            plot_signal(np.frombuffer(raw_data, dtype=np.int16), frame_rate, title="Original Signal")
            plot_spectrum(np.frombuffer(raw_data, dtype=np.int16), frame_rate, title="Original Spectrum")

            # Apply equalizer settings (this is a placeholder, actual equalizer logic should be implemented)
            # For example, you can use scipy.signal to apply filters

            # Visualize the equalized signal
            plot_signal(np.frombuffer(raw_data, dtype=np.int16), frame_rate, title="Equalized Signal")
            plot_spectrum(np.frombuffer(raw_data, dtype=np.int16), frame_rate, title="Equalized Spectrum")

        except Exception as e:
            st.error(f"An error occurred: {e}")