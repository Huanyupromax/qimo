"""
跨模态时序对齐工具 — 统一文本/音频/视频时间轴，解决异步延迟
"""

from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Tuple
from enum import Enum


class ModalityType(str, Enum):
    TEXT = "text"
    AUDIO = "audio"
    VIDEO = "video"


class TimePoint(BaseModel):
    """带时间戳的数据点"""
    timestamp: float
    value: Any
    confidence: float = 1.0


class ModalityTrack(BaseModel):
    """单一模态的时间序列"""
    modality: ModalityType
    name: str = ""
    start_offset: float = 0.0        # 该模态相对全局起点的延迟（秒）
    sample_rate: Optional[float] = None
    points: List[TimePoint] = []

    def total_duration(self) -> float:
        """该模态的总时长"""
        if not self.points:
            return 0.0
        return self.points[-1].timestamp + self.start_offset

    def get_at(self, global_time: float) -> Optional[TimePoint]:
        """获取全局时间点对应的值（线性插值）"""
        local_t = global_time - self.start_offset
        if not self.points or local_t < 0:
            return None
        pts = self.points
        if local_t <= pts[0].timestamp:
            return pts[0]
        if local_t >= pts[-1].timestamp:
            return pts[-1]
        for i in range(len(pts) - 1):
            if pts[i].timestamp <= local_t <= pts[i + 1].timestamp:
                r = (local_t - pts[i].timestamp) / max(pts[i + 1].timestamp - pts[i].timestamp, 1e-6)
                return TimePoint(
                    timestamp=global_time,
                    value=self._interp(pts[i].value, pts[i + 1].value, r),
                    confidence=pts[i].confidence * (1 - r) + pts[i + 1].confidence * r
                )
        return pts[-1]

    def _interp(self, a, b, r: float):
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            return round(a * (1 - r) + b * r, 4)
        if isinstance(a, dict) and isinstance(b, dict):
            result = {}
            for k in set(a) | set(b):
                va, vb = a.get(k, 0), b.get(k, 0)
                if isinstance(va, (int, float)) and isinstance(vb, (int, float)):
                    result[k] = round(va * (1 - r) + vb * r, 4)
                else:
                    result[k] = a.get(k) if r < 0.5 else b.get(k)
            return result
        return a


class AlignedFrame(BaseModel):
    """对齐后的单帧数据"""
    timestamp: float
    text: Optional[Dict[str, Any]] = None
    audio: Optional[Dict[str, Any]] = None
    video: Optional[Dict[str, Any]] = None


class TemporalAligner:
    """跨模态时序对齐器，支持：
    - 多模态时间轴统一
    - 异步延迟补偿
    - 互相关自动延迟估计
    - 线性插值
    """

    def __init__(self, fps: float = 10.0):
        self.fps = fps
        self.interval = 1.0 / fps

    def align(self, tracks: List[ModalityTrack]) -> List[AlignedFrame]:
        """将所有模态对齐到统一时间轴"""
        if not tracks:
            return []

        # 时间范围
        starts = [t.start_offset for t in tracks if t.points]
        ends = [t.total_duration() for t in tracks if t.points]
        if not starts or not ends:
            return []
        t0, t1 = min(starts), max(ends)
        if t1 <= t0:
            return []

        frames = []
        t = t0
        while t <= t1 + 1e-6:
            frame = AlignedFrame(timestamp=round(t, 3))
            for track in tracks:
                pt = track.get_at(t)
                if pt and pt.value is not None:
                    key = track.modality.value
                    setattr(frame, key, {"v": pt.value, "c": round(pt.confidence, 3)})
            frames.append(frame)
            t += self.interval
        return frames

    def compensate(self, tracks: List[ModalityTrack], offsets: Dict[ModalityType, float]) -> List[ModalityTrack]:
        """手动指定各模态的延迟补偿（秒）"""
        out = []
        for t in tracks:
            t.start_offset -= offsets.get(t.modality, 0.0)
            out.append(t)
        return out

    @staticmethod
    def estimate_lag(a: ModalityTrack, b: ModalityTrack, max_lag: float = 2.0) -> float:
        """通过互相关估计两个模态的延迟"""
        try:
            import numpy as np
            va = [p.value for p in a.points if isinstance(p.value, (int, float))]
            vb = [p.value for p in b.points if isinstance(p.value, (int, float))]
            n = min(len(va), len(vb))
            if n < 10:
                return 0.0
            va, vb = np.array(va[:n]), np.array(vb[:n])
            corr = np.correlate(va - va.mean(), vb - vb.mean(), mode="full")
            lag = np.argmax(corr) - (n - 1)
            return lag / n * (a.points[-1].timestamp if len(a.points) > 1 else 1.0)
        except ImportError:
            return 0.0

    @staticmethod
    def text_timing(text: str, words_per_sec: float = 4.0) -> List[TimePoint]:
        """从文字估算时间轴：将文字按句分点"""
        import re
        sentences = [s.strip() for s in re.split(r"[。！？!?\n]", text) if s.strip()]
        points, t = [], 0.0
        for s in sentences:
            dur = len(s) / words_per_sec
            points.append(TimePoint(timestamp=round(t, 2), value=s, confidence=1.0))
            t += dur
        return points

    @staticmethod
    def audio_timing(duration: float, values: List[float], sr_hz: float) -> List[TimePoint]:
        """等间隔音频帧"""
        return [TimePoint(timestamp=i / sr_hz, value=v, confidence=1.0) for i, v in enumerate(values)]

    @staticmethod
    def video_timing(duration: float, fps: float, default_value: Any = None) -> List[TimePoint]:
        """等间隔视频帧骨架"""
        count = int(duration * fps)
        return [TimePoint(timestamp=i / fps, value=default_value, confidence=0.0) for i in range(count)]
