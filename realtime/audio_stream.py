"""音频流处理：降噪、特征提取"""
import time, tempfile
import numpy as np
from scipy import signal
import soundfile as sf
from modalities.voice import VoiceAnalyzer

class AudioStreamProcessor:
    def __init__(self, sample_rate=16000):
        self.sample_rate = sample_rate
        self.analyzer = VoiceAnalyzer()
        self.buffer = []

    def process_chunk(self, audio_bytes, timestamp=None, sample_rate=None):
        ts = timestamp or time.time()
        sr = sample_rate or self.sample_rate
        audio = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        audio_clean = self._reduce_noise(audio, sr)
        features = {
            "timestamp": ts,
            "duration": round(len(audio) / sr, 3),
            "rms": float(np.sqrt(np.mean(audio_clean**2))),
            "peak": float(np.max(np.abs(audio_clean))),
            "sample_rate": sr,
        }
        entry = {"timestamp": ts, "features": features, "data": audio_clean}
        self.buffer.append(entry)
        return entry

    def _reduce_noise(self, audio, sr):
        if len(audio) < 10:
            return audio
        try:
            sos = signal.butter(4, 80 / (sr / 2), btype="high", output="sos")
            return signal.sosfilt(sos, audio)
        except:
            return audio

    def analyze_latest(self):
        if not self.buffer:
            return None
        latest = self.buffer[-1]
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            sf.write(f.name, latest["data"], self.sample_rate)
            result = self.analyzer.analyze(f.name)
        return result

    def clear(self):
        self.buffer = []
