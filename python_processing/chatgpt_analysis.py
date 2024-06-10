import openai
import urllib
import librosa
import sys
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from spotify_api_intergration import SpotifyAPI
from scipy.io import wavfile
from scipy.signal import butter, sosfilt
import gpt_prompts.song_analysis_prompt as gpt_prompt
sys.path.append('..')
import authentication.gpt_api_key as authentication

class GPTAnalysis(object):

    def __init__(self, track_id):
        """
            The following object will get song analysis data from ChatGPT based on audio data from spotify preview
            and spotify audio analysis data.
        """
        # spotify api init
        self.spotify_api = SpotifyAPI()
        track_data = self.spotify_api.get_track_data(track_id)
        self.spotify_audio_features = self.spotify_api.get_track_audio_feature(track_id)
        # self.spotify_track_lyrics = self.spotify_api.get_track_lyrics(track_id)
        track_preview = track_data['preview_url']

        # retrieve song from preview
        path = "audio_to_analyse/preview.wav"
        urllib.request.urlretrieve(track_preview, path)
        self.audio_sample_data = (self.sig, self.rate) = librosa.load(path)
        
        # chatgpt init
        self.user_prompt = ""
        self.system_prompt = gpt_prompt.system_prompt
        openai.api_key = authentication.gpt_key

        # Frequency ranges for instruments (Hz)
        self.instrument_ranges = {
            'Classical Piano': {'low': (27.5, 250), 'mid': (250, 2000), 'high': (2000, 4200)},
            'Electric Guitar': {'mid': (82, 1200)},
            'Classical Guitar': {'mid': (82, 880)},
            'Electronic/Lo-fi': {'bass': (20, 250), 'mid': (250, 2000), 'high': (2000, 8000)},
            'Acoustic Guitar': {'mid': (82, 880)},
            'Atmospheric Effects': {'full': (20, 20000)},
            'Pads/Synthesizers': {'full': (20, 15000)},
            'Flute': {'mid': (261.63, 4000)},
            'Drums/Beats': {'full': (50, 15000)},
            'Trumpet/Horn/Saxophone': {'mid': (146.83, 1000)},
            'Electric Piano/Keyboard': {'low': (27.5, 250), 'mid': (250, 2000), 'high': (2000, 4200)},
            'Percussions': {'full': (100, 10000)},
            'Vocals/Vocal Samples': {'mid': (85, 1200)},
            'Guitar': {'mid': (82, 880)},
            'Strings': {'full': (65, 4000)},
            'Orchestra': {'full': (20, 20000)},
            'Asian Strings': {'mid': (146.83, 1000)},
            'Synthesizer': {'full': (20, 15000)},
            'Binaural Waves': {'full': (20, 20000)},
            'Felt Piano': {'low': (27.5, 250), 'mid': (250, 2000), 'high': (2000, 4200)},
            'Bass Guitar': {'low': (40, 400)},
            'Mandolin': {'mid': (196, 880)},
            'Samples': {'full': (20, 20000)},
        }
        self.energy = {}

        # run audio analysis to get user prompt
        self.analyse_song()
        print(self.user_prompt)
    
    def get_response(self):
        response = openai.chat.completions.create(
            # model="gpt-3.5-turbo",
            model="gpt-4o",
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": self.user_prompt}
            ]
        )
        message = response.choices[0].message.content
        print(message)
    
    def analyse_song(self):
        # Extract features
        tempo, beat_frames = librosa.beat.beat_track(y=self.sig, sr=self.rate)
        chroma_stft = librosa.feature.chroma_stft(y=self.sig, sr=self.rate)
        spectral_contrast = librosa.feature.spectral_contrast(y=self.sig, sr=self.rate)
        mfcc = librosa.feature.mfcc(y=self.sig, sr=self.rate, n_mfcc=13)
        rms = librosa.feature.rms(y=self.sig)
        zcr = librosa.feature.zero_crossing_rate(self.sig)
        centroid = librosa.feature.spectral_centroid(y=self.sig, sr=self.rate)
        bandwidth = librosa.feature.spectral_bandwidth(y=self.sig, sr=self.rate)
        rolloff = librosa.feature.spectral_rolloff(y=self.sig, sr=self.rate)
        harmonic, percussive = librosa.effects.hpss(self.sig)

        # Display features
        tempo = f'Tempo: {tempo}'
        mfcc_shape = f'MFCC shape: {mfcc.shape}'
        spectrral_centroid = f'Spectral Centroid: {centroid.mean()}'
        spectral_bandwidth = f'Spectral Bandwidth: {bandwidth.mean()}'
        spectral_contrast = f'Spectral Contrast: {spectral_contrast.mean(axis=1)}'
        rms = f'Root Mean Square (RMS): {rms.mean()}'
        zcr = f'Zero Crossing Rate (ZCR): {zcr.mean()}'
        spectral_rolloff = f'Spectral Rolloff: {rolloff.mean()}'
        bf = f'Beat Frames: {beat_frames}'
        cs = f'Chroma STFT: {chroma_stft}'
        h = f'Harmonic: {harmonic}'
        p = f'Percussive: {percussive}'
        energies = {}

        energy_dict = self.calculate_instrument_energy(self.sig, self.rate, self.instrument_ranges)
        energies = self.normalize_energy(energy_dict)

        self.energy = f"Normalised Energies: {str(energies)}"
        audio_data = tempo + '\n' + mfcc_shape + '\n' + spectrral_centroid + '\n' + spectral_bandwidth + '\n' + spectral_contrast + '\n' + rms + '\n' + zcr + '\n' + spectral_rolloff + '\n' + bf + '\n' + cs + '\n' + h + '\n' + p + '\n' + self.energy
        self.user_prompt = audio_data + '\n Audio Features:' + str(self.spotify_audio_features)

    def bandpass_filter(self, signal, sr, low_freq, high_freq):
        nyquist = sr / 2
        if low_freq >= nyquist or high_freq >= nyquist:
            filtered_signal = []
        else:
            sos = butter(2, [low_freq, high_freq], btype='band', fs=sr, output='sos')
            filtered_signal = sosfilt(sos, signal)
        return filtered_signal

    def calculate_energy(self, signal, sr, low_freq, high_freq):
        filtered_signal = self.bandpass_filter(signal, sr, low_freq, high_freq)
        if len(filtered_signal) == 0:
            energy = 0
        else:
            energy = np.sum(filtered_signal ** 2)
        return energy

    def calculate_instrument_energy(self, signal, sr, instrument_ranges):
        energy_dict = {}
        for instrument, ranges in instrument_ranges.items():
            instrument_energy = []
            for range_name, (low, high) in ranges.items():
                energy = self.calculate_energy(signal, sr, low, high)
                instrument_energy.append(energy)
            energy_dict[instrument] = instrument_energy
        return energy_dict
    
    def normalize_energy(self, energy_dict):
        normalized_energy = {}
        for instrument, energy in energy_dict.items():
            total_energy = sum(energy)
            if total_energy > 0:
                normalized_energy[instrument] = [e / total_energy for e in energy]
            else:
                normalized_energy[instrument] = energy
        return normalized_energy

gpt = GPTAnalysis("0NDUuWBh1ykEGtIBtD9tAm")
gpt.get_response()