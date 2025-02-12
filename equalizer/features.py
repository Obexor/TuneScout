import wave
import numpy as np
import tempfile
from matplotlib import pyplot as plt
import streamlit as st


def equalizer_features():
    st.header("Equalizer")
    st.write("This feature allows you to modify and equalize uploaded WAV files.")

    # File uploader for WAV
    uploaded_file = st.file_uploader("Upload a WAV file", type=["wav"])

    if uploaded_file:
        st.subheader("Equalizer Settings")
        bass_gain = st.slider("Bass Gain (dB)", -10, 10, 0)
        midrange_gain = st.slider("Midrange Gain (dB)", -10, 10, 0)
        treble_gain = st.slider("Treble Gain (dB)", -10, 10, 0)

        try:
            with wave.open(uploaded_file, "rb") as wav_file:
                # Extrahiere grundlegende Parameter und Frames
                params = wav_file.getparams()
                raw_data = wav_file.readframes(params.nframes)

                # Rohdaten in int16 konvertieren
                audio_signal = np.frombuffer(raw_data, dtype=np.int16)

                # Wenn mehrere Kanäle vorhanden sind, auf Mono reduzieren
                if params.nchannels > 1:
                    audio_signal = audio_signal[::params.nchannels]

                # Samplingrate und Signal-Dauer korrekt berechnen
                frame_rate = params.framerate
                duration = params.nframes / float(frame_rate)
                time = np.linspace(0, duration, len(audio_signal))

                # Audio-Signal bearbeiten (mit einfachen Verstärkungen für Visualisierung)
                equalized_signal = (
                        audio_signal * (1 + bass_gain / 100) +
                        audio_signal * (1 + midrange_gain / 100) +
                        audio_signal * (1 + treble_gain / 100)
                )
                equalized_signal = np.clip(equalized_signal, -32768, 32767)

                st.subheader("Equalized Signal Visualization")
                fig, ax = plt.subplots(figsize=(10, 4))
                ax.plot(time, equalized_signal, label="Equalized Signal")
                ax.set_xlabel("Time (s)")
                ax.set_ylabel("Amplitude")
                ax.legend(loc="upper right")
                st.pyplot(fig)

                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
                    with wave.open(temp_file.name, "wb") as out_wav:
                        # Ausgangssignal in WAV-Datei schreiben
                        out_wav.setnchannels(1)  # Mono
                        out_wav.setsampwidth(2)  # 16-bit Tiefe
                        out_wav.setframerate(frame_rate)
                        out_wav.writeframes(equalized_signal.astype(np.int16).tobytes())

                    # Gewähltes Audio anhören und herunterladen
                    st.audio(temp_file.name, format="audio/wav")
                    st.download_button(
                        label="Download Equalized Audio",
                        data=open(temp_file.name, "rb").read(),
                        file_name="equalized.wav",
                        mime="audio/wav"
                    )

        except Exception as e:
            st.error(f"Error processing the audio file: {e}")