import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from equalizer.filters import butter_lowpass_filter, butter_highpass_filter, equalizer
from pydub import AudioSegment

def equalizer_features():
    """
    Streamlit interface for equalizing audio files. Allows users to upload or stream audio files,
    adjust equalizer settings, and visualize and download the equalized audio.
    """
    st.header("Equalizer")
    st.write("This feature allows you to modify and equalize uploaded or streamed WAV/MP3 files in real-time.")

    # Option to select between uploading a file or streaming from AWS S3
    input_mode = st.radio(
        "Choose Source",
        options=["Upload a File", "Stream from AWS S3"],
        index=0
    )

    # File uploader for WAV or MP3 files
    uploaded_file = st.file_uploader("Upload a WAV or MP3 file", type=["wav", "mp3"])
    if uploaded_file:
        st.subheader("Equalizer Settings")
        # Sliders for adjusting bass, midrange, and treble gains
        bass_gain = st.slider("Bass Gain (dB)", -10, 10, 0)
        midrange_gain = st.slider("Midrange Gain (dB)", -10, 10, 0)
        treble_gain = st.slider("Treble Gain (dB)", -10, 10, 0)

        try:
            import tempfile
            import wave

            # Determine the file type (WAV or MP3)
            file_type = uploaded_file.name.split(".")[-1].lower()

            # Read the audio file based on its type
            if file_type == "wav":
                with wave.open(uploaded_file, "rb") as wav_file:
                    params = wav_file.getparams()
                    raw_data = wav_file.readframes(params.nframes)
                    frame_rate = params.framerate
            elif file_type == "mp3":
                # Use pydub to read and convert MP3 to raw data
                audio_segment = AudioSegment.from_file(uploaded_file, format="mp3")
                audio_segment = audio_segment.set_channels(1)  # Convert to mono
                frame_rate = audio_segment.frame_rate
                raw_data = np.array(audio_segment.get_array_of_samples()).astype(np.int16).tobytes()
            else:
                st.error("Unsupported file type. Please upload a WAV or MP3 file.")
                return

            # Convert raw audio data to a NumPy array
            audio_signal = np.frombuffer(raw_data, dtype=np.int16)
            time = np.linspace(0, len(audio_signal) / frame_rate, len(audio_signal))

            # Apply filters to adjust bass, midrange, and treble frequencies
            bass = butter_lowpass_filter(audio_signal, cutoff=200, fs=frame_rate, gain=bass_gain)
            midrange = equalizer(audio_signal, freq_range=(200, 3000), fs=frame_rate, gain=midrange_gain)
            treble = butter_highpass_filter(audio_signal, cutoff=3000, fs=frame_rate, gain=treble_gain)
            equalized_signal = bass + midrange + treble

            # Visualization of the equalized signal
            st.subheader("Equalized Signal Visualization")
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.plot(time, equalized_signal, label="Equalized Signal")
            ax.set_xlabel("Time (s)")
            ax.set_ylabel("Amplitude")
            ax.legend()
            st.pyplot(fig)

            # Save the equalized audio as a WAV file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
                with wave.open(temp_file.name, "wb") as out_wav:
                    out_wav.setnchannels(1)  # Mono
                    out_wav.setsampwidth(2)  # 16-bit depth
                    out_wav.setframerate(frame_rate)
                    equalized_signal = np.clip(equalized_signal, -32768, 32767).astype(np.int16)
                    out_wav.writeframes(equalized_signal.tobytes())

                # Play the equalized audio and provide a download button
                st.audio(temp_file.name, format="audio/wav")
                st.download_button(
                    label="Download Equalized Audio",
                    data=open(temp_file.name, "rb").read(),
                    file_name="equalized.wav",
                    mime="audio/wav"
                )

        except Exception as e:
            st.error(f"Error processing the audio file: {e}")
