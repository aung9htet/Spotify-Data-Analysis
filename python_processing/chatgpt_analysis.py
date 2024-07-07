import openai
from openai import OpenAI
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
from google.cloud import speech
import os
import io
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
        track_preview = track_data['preview_url']

        # retrieve song from preview
        path = "audio_to_analyse/preview.wav"
        urllib.request.urlretrieve(track_preview, path)
        self.audio_sample_data = (self.sig, self.rate) = librosa.load(path)
        
        # google speech to text
        # os.environ['GOOGLE_APPLICATION_CREDENTIALS']= '../authentication/google-authentication.json'
        # client = speech.SpeechClient()
        # with io.open(path, 'rb') as audio_file:
        #     content = audio_file.read()
        #     audio = speech.RecognitionAudio(content=content)
        # config = speech.RecognitionConfig(
        #     # encoding=speech.RecognitionConfig.AudioEncoding.FLAC,
        #     enable_automatic_punctuation=True,
        #     audio_channel_count=2,
        #     language_code= "en-US",
        #     alternative_language_codes= ["ko-KR"],
        #     model = "latest_long"
        # )
        # response = client.recognize(request={"config": config, "audio": audio})
        # for result in response.results:
        #     print("Transcript: {}".format(result.alternatives[0].transcript))
        
        # open ai whisper
        openai.api_key = authentication.gpt_key
        client = OpenAI(api_key=authentication.gpt_key)

        audio_file= open(path, "rb")
        self.transcription = client.audio.transcriptions.create(
            model="whisper-1", 
            file=audio_file,
            language= ["en", "kr", "jp"]
        )

        # chatgpt init
        self.user_prompt = ""
        self.system_prompt = gpt_prompt.system_prompt

        # Frequency ranges for instruments (Hz)
        self.instrument_ranges = {
            'Classical Piano': {
                'low_mid': (250, 260),    # Narrow lower midrange
                'mid': (500, 610),        # Narrow midrange
                'high_mid': (1000, 1010)  # Narrow upper midrange
            },
            'Electric Guitar': {
                'low_mid': (200, 210),    # Narrow low midrange
                'mid': (400, 410),        # Narrow midrange
                'high_mid': (800, 810)    # Narrow upper midrange
            },
            'Classical Guitar': {
                'low_mid': (200, 220),    # Slightly broader low midrange
                'mid': (400, 420),        # Slightly broader midrange
                'high_mid': (600, 620)    # Slightly broader upper midrange
            },
            'Acoustic Guitar': {
                'low_mid': (200, 220),    # Slightly broader low midrange
                'mid': (400, 420),        # Slightly broader midrange
                'high_mid': (600, 620)    # Slightly broader upper midrange
            },
            'Electronic/Lo-fi': {
                'low_mid': (250, 300),    # Slightly broader lower midrange
                'mid': (500, 550),        # Slightly broader midrange
                'high_mid': (1000, 1050)  # Slightly broader upper midrange
            },
            'Atmospheric Effects': {
                'mid': (2000, 3000),      # Broad midrange
                'high': (4000, 5000),     # Broad high frequencies
                'very_high': (6000, 7000) # Broad very high frequencies
            },
            'Pads/Synthesizers': {
                'low_mid': (250, 300),    # Slightly broader lower midrange
                'mid': (500, 550),        # Slightly broader midrange
                'high_mid': (1000, 1050)  # Slightly broader upper midrange
            },
            'Flute': {
                'mid': (523.25, 633.25),  # Narrow midrange (C5 to C#5)
                'high_mid': (1046.5, 1156.5),# Narrow upper midrange (C6 to C#6)
                'high': (2093, 2203)      # Narrow high (C7 to C#7)
            },
            'Drums/Beats': {
                'low_mid': (250, 300),    # Slightly broader lower midrange
                'mid': (500, 550),        # Slightly broader midrange
                'high_mid': (1000, 2000)  # Broad upper midrange
            },
            'Trumpet/Horn/Saxophone': {
                'low_mid': (293.66, 303.66), # Narrow lower midrange
                'mid': (500, 510),        # Narrow midrange
                'high_mid': (1000, 1010)  # Narrow upper midrange
            },
            'Electric Piano/Keyboard': {
                'low_mid': (250, 260),    # Narrow lower midrange
                'mid': (500, 510),        # Narrow midrange
                'high_mid': (1000, 1010)  # Narrow upper midrange
            },
            'Percussions': {
                'mid': (1000, 1100),      # Narrow midrange
                'high_mid': (2000, 2100), # Narrow upper midrange
                'high': (4000, 5000)      # Broad high frequencies
            },
            'Vocals/Vocal Samples': {
                'low_mid': (180, 200),    # Slightly broader lower midrange
                'mid': (400, 420),        # Slightly broader midrange
                'high_mid': (800, 820)    # Slightly broader upper midrange
            },
            'Strings': {
                'low_mid': (200, 220),    # Slightly broader lower midrange
                'mid': (500, 520),        # Slightly broader midrange
                'high_mid': (1000, 1020)  # Slightly broader upper midrange
            },
            'Orchestra': {
                'low_mid': (250, 300),    # Slightly broader lower midrange
                'mid': (500, 550),        # Slightly broader midrange
                'high_mid': (1000, 1050)  # Slightly broader upper midrange
            },
            'Asian Strings': {
                'low_mid': (293.66, 313.66), # Slightly broader lower midrange
                'mid': (500, 520),        # Slightly broader midrange
                'high_mid': (1000, 1020)  # Slightly broader upper midrange
            },
            'Synthesizer': {
                'low_mid': (250, 300),    # Slightly broader lower midrange
                'mid': (500, 550),        # Slightly broader midrange
                'high_mid': (1000, 1050)  # Slightly broader upper midrange
            },
            'Binaural Waves': {
                'full': (20, 20000)       # Full frequency range
            },
            'Felt Piano': {
                'low_mid': (250, 260),    # Narrow lower midrange
                'mid': (500, 510),        # Narrow midrange
                'high_mid': (1000, 1010)  # Narrow upper midrange
            },
            'Bass Guitar': {
                'low': (40, 60),          # Narrow low frequencies
                'low_mid': (80, 100),     # Slightly broader low midrange
                'mid': (160, 180)         # Slightly broader midrange
            },
            'Mandolin': {
                'low_mid': (293.66, 313.66), # Slightly broader lower midrange
                'mid': (500, 520),        # Slightly broader midrange
                'high_mid': (800, 820)    # Slightly broader upper midrange
            },
            'Samples': {
                'low_mid': (250, 300),    # Slightly broader lower midrange
                'mid': (500, 550),        # Slightly broader midrange
                'high_mid': (1000, 1050)  # Slightly broader upper midrange
            },
        }

        self.energy = {}

        # run audio analysis to get user prompt
        self.analyse_song()
        # print(self.user_prompt)
    
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
        # message = str(message).split('[')
        message = [str(message).split('[')[1], str(message).split('[')[2], str(message).split('[')[3]]
        new_message = ""
        for i in message:
            new_message += str(i)
        message = new_message
        message = [str(message).split(']')[0], str(message).split(']')[1], str(message).split(']')[2]]
        new_message = ""
        for i in message:
            new_message += str(i)
        message = new_message
        message = str(message).split(':')
        genre = message[0].split('\n')[0].split(',')
        genre = [x.strip(' ') for x in genre]
        instruments = message[1].split('\n')[0].split(',')
        instruments = [x.strip(' ') for x in instruments]
        feelings = message[2].split('\n')[0].split(',')
        feelings = [x.strip(' ') for x in feelings]
        results_dict = {'Genre': genre, 'Instruments': instruments, 'Feelings': feelings}
        return results_dict
    
    def get_total_results(self):
        total_result = {'Genre': {}, 'Instruments': {}, 'Feelings': {}}
        for progress in range(10):
            print(progress)
            result = self.get_response()
            for key in total_result:
                results = result[key]
                for i in results:
                    if i in total_result[key]:
                        total_result[key][i] += 1
                    else:
                        total_result[key][i] = 0
        for key in total_result:
            dict_to_sort = total_result[key]
            dict_to_sort = dict(sorted(dict_to_sort.items(), key=lambda item: item[1], reverse=True))
            total_result[key] = dict_to_sort
        print(total_result)
        return total_result
                
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
        energies = self.get_energy()

        # Anaylsed features init
        self.tempo = tempo
        self.mfcc_shape = mfcc.shape
        self.spectrral_centroid = centroid.mean()
        self.spectral_bandwidth = bandwidth.mean()
        self.spectral_contrast = spectral_contrast.mean(axis=1)
        self.rms = rms.mean()
        self.zcr = zcr.mean()
        self.spectral_rolloff = rolloff.mean()
        self.beat_frames = beat_frames
        self.chroma_stft = chroma_stft
        self.harmonic = harmonic
        self.percussive = percussive

        # Display analysed audio features from audio sample
        audio_data = "The following describes audio features analysed and calculated from a preview audio sample:"
        audio_data = audio_data + f'\nTempo: {tempo}'
        audio_data = audio_data + f'\nMFCC shape: {mfcc.shape}'
        audio_data = audio_data + f'\nSpectral Centroid: {centroid.mean()}'
        audio_data = audio_data + f'\nSpectral Bandwidth: {bandwidth.mean()}'
        audio_data = audio_data + f'\nSpectral Contrast: {spectral_contrast.mean(axis=1)}'
        audio_data = audio_data + f'\nRoot Mean Square (RMS): {rms.mean()}'
        audio_data = audio_data + f'\nZero Crossing Rate (ZCR): {zcr.mean()}'
        audio_data = audio_data + f'\nSpectral Rolloff: {rolloff.mean()}'
        audio_data = audio_data + f'\nBeat Frames: {beat_frames}'
        audio_data = audio_data + f'\nChroma STFT: {chroma_stft}'
        audio_data = audio_data + f'\nHarmonic: {harmonic}'
        audio_data = audio_data + f'\nPercussive: {percussive}'
        audio_data = audio_data + f'\nNormalised Energies: {str(energies)}'
        
        # Spotify audio features
        spotify_audio_features = self.spotify_audio_features
        self.danceability = spotify_audio_features['danceability']
        self.energy = spotify_audio_features['energy']
        self.key = spotify_audio_features['key']
        self.loudness = spotify_audio_features['loudness']
        self.mode = spotify_audio_features['mode']
        self.speechiness = spotify_audio_features['speechiness']
        self.acousticness = spotify_audio_features['acousticness']
        self.instrumentalness = spotify_audio_features['instrumentalness']
        self.liveness = spotify_audio_features['liveness']
        self.valence = spotify_audio_features['valence']
        self.tempo = spotify_audio_features['tempo']

        # Display spotify audio features
        spotify_data = "\n\nThe following describes spotify's anaylzed audio features:"
        spotify_data = spotify_data + f'\nDanceability: {self.danceability}'
        spotify_data = spotify_data + f'\nEnergy: {self.energy}'
        spotify_data = spotify_data + f'\nKey: {self.key}'
        spotify_data = spotify_data + f'\nLoudness: {self.loudness}'
        spotify_data = spotify_data + f'\nMode: {self.mode}'
        spotify_data = spotify_data + f'\nSpeechiness: {self.speechiness}'
        spotify_data = spotify_data + f'\nAcousticness: {self.acousticness}'
        spotify_data = spotify_data + f'\nInstrumentalness: {self.instrumentalness}'
        spotify_data = spotify_data + f'\nLiveness: {self.liveness}'
        spotify_data = spotify_data + f'\nValence: {self.valence}'
        spotify_data = spotify_data + f'\nTempo: {self.tempo}'

        # Lyrics
        lyrics = f"\nLyrics: {self.transcription}"
        self.user_prompt = audio_data + spotify_data + lyrics
        print(self.user_prompt)
    
    def get_energy(self):
        energy_dict = self.calculate_instrument_energy(self.sig, self.rate, self.instrument_ranges)
        for key in energy_dict:
            # instrument_range = self.instrument_ranges[key]
            # total_band = 0
            # for i_range in instrument_range:
            #     band = instrument_range[i_range]
            #     total_band += (band[1] - band[0])
            energy_dict[key] = np.sum(energy_dict[key])
            # energy_dict[key] = np.sum(energy_dict[key])/total_band
        return energy_dict
    
    def bandpass_filter(self, signal, sr, low_freq, high_freq):
        nyquist = sr / 2
        if low_freq >= nyquist or high_freq >= nyquist:
            return np.zeros_like(signal)
        else:
            sos = butter(2, [low_freq, high_freq], btype='band', fs=sr, output='sos')
            filtered_signal = sosfilt(sos, signal)
            return filtered_signal

    def calculate_energy(self, signal, sr, low_freq, high_freq):
        filtered_signal = self.bandpass_filter(signal, sr, low_freq, high_freq)
        return np.sum(filtered_signal ** 2)

    def calculate_instrument_energy(self, signal, sr, instrument_ranges):
        energy_dict = {}
        for instrument, ranges in instrument_ranges.items():
            instrument_energy = []
            for range_name, (low, high) in ranges.items():
                energy = self.calculate_energy(signal, sr, low, high)
                instrument_energy.append(energy)
            energy_dict[instrument] = instrument_energy
        return energy_dict

    # def normalize_energy_independently(self, energy_dict):
    #     normalized_energy = {}
    #     for instrument, energies in energy_dict.items():
    #         total_energy = sum(energies)
    #         if total_energy > 0:
    #             normalized_energies = [e / total_energy for e in energies]
    #             average_energy = np.mean(normalized_energies)
    #             normalized_energy[instrument] = average_energy
    #         else:
    #             normalized_energy[instrument] = 0  # Handle zero-energy case
    #     return normalized_energy

# gpt = GPTAnalysis("6h6runZeeczWEuEW2pFvYW")
gpt = GPTAnalysis("1BncfTJAWxrsxyT9culBrj")
gpt.get_total_results()