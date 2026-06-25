"""语音模态粗判模块 — SenseVoiceSmall + 基础音频分析"""

import os, json, tempfile, subprocess, struct
from typing import Optional, List
from .models import VoiceFeatures


class VoiceAnalyzer:
    """语音分析器 — 支持 SenseVoiceSmall 和基础分析"""

    def __init__(self, sensevoice_path: Optional[str] = None):
        self.sensevoice_path = sensevoice_path
        self._sv_available = sensevoice_path is not None and os.path.exists(sensevoice_path)

    def analyze(self, audio_path: str, transcript: Optional[str] = None) -> VoiceFeatures:
        """分析音频文件，返回语音特征"""
        if not os.path.exists(audio_path):
            return VoiceFeatures()

        features = VoiceFeatures()
        wav_path = self._ensure_wav(audio_path)
        if not wav_path:
            return features

        # 基础音频分析
        info = self._parse_wav_header(wav_path)
        if info:
            features.duration = info["duration"]

        # 语速（需要文本+时长）
        if transcript and features.duration > 0:
            features.speech_rate = round(len(transcript) / features.duration, 2)

        # 音量分析
        volume = self._analyze_volume(wav_path)
        if volume:
            features.volume_peak = round(volume["peak"], 4)
            features.volume_avg = round(volume["avg"], 4)

        # 停顿检测
        pauses = self._detect_pauses(wav_path)
        if pauses:
            features.pause_count = pauses["count"]
            features.pause_duration = round(pauses["total"], 4)

        # SenseVoiceSmall 情绪识别
        if self._sv_available:
            emotion = self._sensevoice_emotion(wav_path)
            if emotion:
                features.basic_emotion = emotion

        return features

    def _ensure_wav(self, path: str) -> Optional[str]:
        """确保音频为 WAV 格式，必要时转换"""
        if path.lower().endswith(".wav"):
            return path
        out = tempfile.mktemp(suffix=".wav")
        try:
            subprocess.run(
                ["ffmpeg", "-y", "-i", path, "-ac", "1", "-ar", "16000", out],
                capture_output=True, timeout=30
            )
            return out if os.path.exists(out) else None
        except Exception:
            return None

    def _parse_wav_header(self, path: str) -> Optional[dict]:
        """解析 WAV 文件头获取基本信息"""
        try:
            with open(path, "rb") as f:
                header = f.read(44)
                if header[:4] != b"RIFF":
                    return None
                channels = struct.unpack("<H", header[22:24])[0]
                sample_rate = struct.unpack("<I", header[24:28])[0]
                bits = struct.unpack("<H", header[34:36])[0]
                data_size = struct.unpack("<I", header[40:44])[0]
                duration = data_size / (sample_rate * channels * bits / 8) if sample_rate > 0 else 0
                return {
                    "channels": channels,
                    "sample_rate": sample_rate,
                    "bits": bits,
                    "duration": round(duration, 2),
                    "data_size": data_size,
                }
        except Exception:
            return None

    def _analyze_volume(self, path: str) -> Optional[dict]:
        """分析音量（基于样本值的 RMS 和峰值）"""
        try:
            with open(path, "rb") as f:
                data = f.read()[44:]  # 跳过 WAV 头
            samples = struct.unpack(f"<{len(data)//2}h", data)
            peak = max(abs(s) for s in samples) / 32768.0 if samples else 0
            rms = (sum(s * s for s in samples) / len(samples)) ** 0.5 / 32768.0 if samples else 0
            return {"peak": peak, "avg": rms}
        except Exception:
            return None

    def _detect_pauses(self, path: str, silence_thresh: float = 0.02, min_pause: int = 300) -> Optional[dict]:
        """检测停顿（基于音量阈值）"""
        try:
            with open(path, "rb") as f:
                data = f.read()[44:]
            samples = struct.unpack(f"<{len(data)//2}h", data)
            sr = 16000
            frame_size = sr // 50  # 20ms 帧
            is_silent = []
            for i in range(0, len(samples), frame_size):
                frame = samples[i:i + frame_size]
                rms = (sum(s * s for s in frame) / max(len(frame), 1)) ** 0.5 / 32768.0
                is_silent.append(rms < silence_thresh)

            # 合并连续静音帧
            pauses = []
            in_pause = False
            pause_start = 0
            for i, silent in enumerate(is_silent):
                if silent and not in_pause:
                    in_pause = True
                    pause_start = i
                elif not silent and in_pause:
                    dur = (i - pause_start) * 20  # ms
                    if dur >= min_pause:
                        pauses.append(dur)
                    in_pause = False

            if in_pause:
                dur = (len(is_silent) - pause_start) * 20
                if dur >= min_pause:
                    pauses.append(dur)

            return {
                "count": len(pauses),
                "total": round(sum(pauses) / 1000.0, 2),
                "pauses_ms": pauses,
            }
        except Exception:
            return None

    def _sensevoice_emotion(self, wav_path: str) -> Optional[str]:
        """调用 SenseVoiceSmall 进行情绪识别（需部署模型）"""
        try:
            result = subprocess.run(
                ["python", "-m", "funasr", "--model", "iic/SenseVoiceSmall",
                 "--audio", wav_path, "--tasks", "emotion"],
                capture_output=True, text=True, timeout=60
            )
            output = result.stdout.strip()
            if "happy" in output:
                return "积极"
            elif "sad" in output or "angry" in output:
                return "消极"
            elif "neutral" in output:
                return "中性"
            return None
        except Exception:
            return None
