import sounddevice as sd
import wave
import numpy as np
from scipy.signal import spectrogram
from scipy.ndimage import maximum_filter
from pipeline import settings
import subprocess


def record_audio(output_file, duration=10):
    """
    Record audio from the microphone and save it to a WAV file.

    :param output_file: The name of the output WAV file
    :param duration: Duration of the recording in seconds
    """
    SAMPLE_RATE = 44100  # Sampling rate in Hz
    CHANNELS = 1  # Number of audio channels

    print(f"Recording for {duration} seconds...")
    audio_data = sd.rec(int(duration * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=CHANNELS, dtype='int16')
    sd.wait()  # Wait for the recording to finish

    with wave.open(output_file, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)  # 2 bytes for 16-bit PCM
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio_data.tobytes())
    print("Recording complete and saved.")


def file_to_spectrogram(filename):
    """
    Berechnet das Spektrogramm einer WAV-Datei basierend auf Einstellungen in `settings`.
    Die Datei muss vorher in Mono konvertiert und resampled sein.

    :param filename: Pfad zur WAV-Datei
    :return:
        - f: Liste von Frequenzen
        - t: Liste von Zeiten
        - Sxx: Leistungswert für jedes Zeit-/Frequenzpaar
    """
    with wave.open(filename, 'rb') as wf:
        # Überprüfen, ob die Datei Mono ist
        channels = wf.getnchannels()
        if channels > 1:
            raise ValueError("Das Audio muss ein Mono-Kanal sein.")

        sample_rate = wf.getframerate()
        n_frames = wf.getnframes()
        audio = np.frombuffer(wf.readframes(n_frames), dtype=np.int16)

        # Check, ob die Samplerate der `settings.SAMPLE_RATE` entspricht
        if sample_rate != settings.SAMPLE_RATE:
            raise ValueError(f"Samplerate muss {settings.SAMPLE_RATE} Hz sein.")

        # Spektrogramm berechnen
        nperseg = int(settings.SAMPLE_RATE * settings.FFT_WINDOW_SIZE)
        f, t, Sxx = spectrogram(audio, fs=sample_rate, nperseg=nperseg)
        return f, t, Sxx


def find_peaks(Sxx):
    """
    Findet Peaks in einem Spektrogramm.

    Grundlage:
      - `settings.PEAK_BOX_SIZE` für die Region um jeden Peak.
      - Die Anzahl der Peaks wird auf Grundlage von `settings.POINT_EFFICIENCY` berechnet.

    :param Sxx: Das Spektrogramm
    :return: Eine Liste von Peaks
    """
    data_max = maximum_filter(Sxx, size=settings.PEAK_BOX_SIZE, mode='constant', cval=0.0)
    peak_mask = (Sxx == data_max)  # Nur die größten Werte sind gültig
    y_peaks, x_peaks = peak_mask.nonzero()
    peak_values = Sxx[y_peaks, x_peaks]

    # Sortieren nach Stärke des Wertes
    i = peak_values.argsort()[::-1]
    j = [(y_peaks[idx], x_peaks[idx]) for idx in i]

    # Anzahl Peaks berechnen auf Basis von Effizienz
    total_area = Sxx.shape[0] * Sxx.shape[1]
    peak_limit = int((total_area / (settings.PEAK_BOX_SIZE ** 2)) * settings.POINT_EFFICIENCY)

    return j[:peak_limit]


def idxs_to_tf_pairs(idxs, t, f):
    """
    Konvertiert Indizes von Zeit- und Frequenzpunkten in reale Werte.

    :param idxs: Liste von Indizes
    :param t: Liste von Zeitpunkten
    :param f: Liste von Frequenzpunkten
    :return: Array von (Frequenz, Zeit)-Paaren
    """
    return np.array([(f[i[0]], t[i[1]]) for i in idxs])


def my_spectrogram(audio):
    """
    Erstellt ein Spektrogramm für die genannten Einstellungen in `settings`.

    :param audio: Audio-Daten als NumPy-Array
    :return: Frequenz, Zeit und Spektrogramm-Werte
    """
    nperseg = int(settings.SAMPLE_RATE * settings.FFT_WINDOW_SIZE)
    return spectrogram(audio, settings.SAMPLE_RATE, nperseg=nperseg)



def convert_mp3_to_wav(input_file, output_file):
    """
       Konvertiert eine MP3-Datei in WAV mithilfe von ffmpeg.

       :param input_file: Pfad zur Eingabedatei (MP3)
       :param output_file: Pfad zur Ausgabedatei (WAV)
       :return: True, falls die Konvertierung erfolgreich war, andernfalls False.
       """
    try:
        # ffmpeg-Kommando ausführen
        command = [
            "ffmpeg", "-y",  # Überschreibt die Datei ohne Nachfrage
            "-i", input_file,  # Eingabedatei
            "-ac", "1",  # Mono-Kanal erzwingen
            "-ar", "44100",  # Samplerate auf 44.1 kHz setzen
            output_file  # Ausgabedatei
        ]
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Fehler bei der MP3-zu-WAV-Konvertierung: {e}")
        return False

