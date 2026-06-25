import os, json, subprocess, wave, struct, tempfile
from pathlib import Path
from typing import List, Dict, Optional

class AudioFeatureExtractor:
    FEATURE_NAMES = ["duration", "volume_peak", "volume_avg", "speech_ratio", "pause_ratio", "zero_crossing_rate"]

    def __init__(self, ffmpeg_path: Optional[str] = None):
        self.ffmpeg_path = ffmpeg_path or self._find_ffmpeg()
        self.ffmpeg_available = self.ffmpeg_path and os.path.isfile(self.ffmpeg_path)

    def _find_ffmpeg(self) -> Optional[str]:
        local = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ffmpeg.exe")
        if os.path.isfile(local):
            return os.path.abspath(local)
        import shutil
        return shutil.which("ffmpeg")

    def extract_wav_features(self, wav_path: str) -> Dict:
        features = {}
        try:
            with wave.open(wav_path, "rb") as wf:
                nframes = wf.getnframes()
                rate = wf.getframerate()
                duration = nframes / rate
                features["duration"] = round(duration, 1)
                raw = wf.readframes(min(nframes, rate * 30))
                if len(raw) < 4:
                    return features
                samples = struct.unpack(f"<{len(raw)//2}h", raw[:len(raw)//2*2])
                peak = max(abs(s) for s in samples) / 32768.0
                avg = sum(abs(s) for s in samples) / len(samples) / 32768.0
                features["volume_peak"] = round(peak, 3)
                features["volume_avg"] = round(avg, 3)
                threshold = max(avg * 0.5, 0.01)
                speech = sum(1 for s in samples if abs(s) / 32768.0 > threshold)
                features["speech_ratio"] = round(speech / len(samples) * 100, 1)
                features["pause_ratio"] = round(1.0 - speech / len(samples), 3)
                zcr = sum(1 for i in range(1, len(samples)) if (samples[i-1] >= 0) != (samples[i] >= 0))
                features["zero_crossing_rate"] = round(zcr / len(samples), 4)
        except Exception as e:
            features["error"] = str(e)
        return features

    def extract_mp3_features(self, mp3_path: str, max_duration: int = 30) -> Dict:
        if not self.ffmpeg_available:
            return {"error": "ffmpeg not available"}
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            wav_path = tmp.name
        try:
            cmd = [self.ffmpeg_path, "-i", mp3_path, "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "1", "-y"]
            if max_duration > 0:
                cmd.extend(["-t", str(max_duration)])
            cmd.append(wav_path)
            subprocess.run(cmd, capture_output=True, timeout=max_duration + 30)
            if os.path.isfile(wav_path):
                feats = self.extract_wav_features(wav_path)
                feats["source"] = os.path.basename(mp3_path)
                return feats
        except:
            pass
        finally:
            try: os.unlink(wav_path)
            except: pass
        return {"error": "conversion failed"}

    def process_directory(self, directory: str, ext: str = ".mp3", max_files: int = 0) -> List[Dict]:
        results = []
        d = Path(directory)
        if not d.exists():
            return results
        files = sorted(d.rglob(f"*{ext}"))
        if max_files > 0:
            files = files[:max_files]
        for f in files:
            print(f"  处理: {f.relative_to(d)}")
            feats = self.extract_mp3_features(str(f)) if ext != ".wav" else self.extract_wav_features(str(f))
            feats["file"] = str(f.relative_to(d))
            results.append(feats)
        return results
