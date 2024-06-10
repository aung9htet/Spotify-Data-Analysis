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
from scipy.signal import butter, lfilter
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
        track_preview = track_data['preview_url']

        # retrieve song from preview
        path = "audio_to_analyse/preview.wav"
        urllib.request.urlretrieve(track_preview, path)
        self.audio_sample_data = (self.sig, self.rate) = librosa.load(path)
        
        # chatgpt init
        openai.api_key = authentication.gpt_key
        client = openai.OpenAI(api_key=authentication.gpt_key)
        self.user_prompt = ""
        audio_file= open(path, "rb")
        transcription = client.audio.transcriptions.create(
            model="whisper-1", 
            file=audio_file
        )
        self.transcript_text = transcription.text
        print(self.transcript_text)
        openai.api_key = authentication.gpt_key

        # Frequency ranges for instruments (Hz)
        self.instrument_ranges = {
            'Classical Piano': (27.5, 4200),
            'Electric Guitar': (82, 1200),
            'Classical Guitar': (82, 880),
            'Electronic/Lo-fi': (20, 15000),
            'Acoustic Guitar': (82, 880),
            'Atmospheric Effects': (20, 20000),
            'Pads/Synthesizers': (20, 15000),
            'Flute': (261.63, 4000),
            'Drums/Beats': (50, 15000),
            'Trumpet/Horn/Saxophone': (146.83, 1000),
            'Electric Piano/Keyboard': (27.5, 4200),
            'Percussions': (100, 10000),
            'Vocals/Vocal Samples': (85, 1200),
            'Guitar': (82, 880),
            'Strings': (65, 4000),
            'Orchestra': (20, 20000),
            'Asian Strings': (146.83, 1000),
            'Synthesizer': (20, 15000),
            'Binaural Waves': (20, 20000),
            'Felt Piano': (27.5, 4200),
            'Bass Guitar': (40, 400),
            'Mandolin': (196, 880),
            'Samples': (20, 20000),
        }
        self.energy = {}

        # run
        self.analyse_song()
        self.system_prompt = gpt_prompt.system_prompt

    def get_response(self):
        response = openai.chat.completions.create(
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
        lyrics = f'Lyrics: {self.transcript_text}'

        # # Plotting the features
        # plt.figure(figsize=(14, 8))

        # plt.subplot(3, 2, 1)
        # librosa.display.specshow(chroma_stft, y_axis='chroma', x_axis='time')
        # plt.title('Chroma STFT')
        # plt.colorbar()

        # plt.subplot(3, 2, 2)
        # librosa.display.specshow(librosa.amplitude_to_db(librosa.stft(self.sig), ref=np.max), y_axis='log', x_axis='time')
        # plt.title('Spectrogram')
        # plt.colorbar(format='%+2.0f dB')

        # plt.subplot(3, 2, 3)
        # plt.semilogy(rms.T, label='RMS Energy')
        # plt.xticks([])
        # plt.xlim([0, rms.shape[-1]])
        # plt.title('RMS Energy')
        # plt.legend()

        # plt.subplot(3, 2, 4)
        # plt.semilogy(zcr.T, label='Zero Crossing Rate')
        # plt.xticks([])
        # plt.xlim([0, zcr.shape[-1]])
        # plt.title('Zero Crossing Rate')
        # plt.legend()

        # plt.subplot(3, 2, 5)
        # plt.semilogy(centroid.T, label='Spectral Centroid')
        # plt.xticks([])
        # plt.xlim([0, centroid.shape[-1]])
        # plt.title('Spectral Centroid')
        # plt.legend()

        # plt.subplot(3, 2, 6)
        # plt.semilogy(rolloff.T, label='Spectral Rolloff')
        # plt.xticks([])
        # plt.xlim([0, rolloff.shape[-1]])
        # plt.title('Spectral Rolloff')
        # plt.legend()

        # plt.tight_layout()
        # plt.show()

        # # Additional analysis for genre/instrument classification
        # # Normally this would involve a pre-trained model, but for simplicity we use PCA to visualize
        # scaler = StandardScaler()
        # mfcc_scaled = scaler.fit_transform(mfcc.T)

        # pca = PCA(n_components=2)
        # mfcc_pca = pca.fit_transform(mfcc_scaled)

        # plt.figure(figsize=(8, 6))
        # plt.scatter(mfcc_pca[:, 0], mfcc_pca[:, 1])
        # plt.title('PCA of MFCC')
        # plt.xlabel('Principal Component 1')
        # plt.ylabel('Principal Component 2')
        # plt.show()
        # Process each instrument
        energies = {}
        for instrument, (lowcut, highcut) in self.instrument_ranges.items():
            filtered_signal = self.bandpass_filter(self.sig, lowcut, highcut, self.rate)
            if len(filtered_signal) == 0:
                energy = 0
            else:
                energy = self.calculate_energy(filtered_signal)
            energies[instrument] = energy
        self.energy = f"Energies: {str(energies)}"
        self.user_prompt = tempo + '\n' + mfcc_shape + '\n' + spectrral_centroid + '\n' + spectral_bandwidth + '\n' + spectral_contrast + '\n' + rms + '\n' + zcr + '\n' + spectral_rolloff + '\n' + bf + '\n' + cs + '\n' + h + '\n' + p + '\n' + lyrics + '\n' + self.energy

        # Print energies
        for instrument, energy in energies.items():
            print(f'{instrument}: {energy}')


    # Define bandpass filter
    def butter_bandpass(self, lowcut, highcut, fs, order=5):
        nyquist = 0.5 * fs
        low = lowcut / nyquist
        high = highcut / nyquist
        if low <= 0 or high >=1:
            return [], []
        b, a = butter(order, [low, high], btype='band')
        return b, a

    def bandpass_filter(self, data, lowcut, highcut, fs, order=5):
        b, a = self.butter_bandpass(lowcut, highcut, fs, order=order)
        if len(b) == 0 and len(a) == 0:
            return []
        y = lfilter(b, a, data)
        return y

    # Calculate energy
    def calculate_energy(self, filtered_signal):
        energy = np.sum(np.square(filtered_signal))
        return energy

gpt = GPTAnalysis("4MAU5QwI1Gu57gsnL7CUpt")
gpt.get_response()