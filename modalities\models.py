"""统一特征封装层 — Pydantic v2 模型"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class TextFeatures(BaseModel):
    """文本模态特征"""
    basic_emotion: str = "中性"
    emotion_score: float = 0.0
    rebuttal_sentences: List[str] = []
    rebuttal_ratio: float = 0.0
    logical_word_count: int = 0
    logical_density: float = 0.0
    evidence_word_count: int = 0
    evidence_density: float = 0.0
    word_count: int = 0
    sentence_count: int = 0


class VoiceFeatures(BaseModel):
    """语音模态特征"""
    speech_rate: float = 0.0
    volume_peak: float = 0.0
    volume_avg: float = 0.0
    pause_count: int = 0
    pause_duration: float = 0.0
    pitch_avg: Optional[float] = None
    pitch_std: Optional[float] = None
    basic_emotion: Optional[str] = None
    duration: float = 0.0


class FaceFeatures(BaseModel):
    """人脸模态特征"""
    emotions: Dict[str, float] = {}
    dominant_emotion: str = "neutral"
    au_intensity: Optional[Dict[str, float]] = None
    head_pose: Optional[Dict[str, float]] = None
    face_count: int = 0


class UnifiedAnalysis(BaseModel):
    """三类模态统一输出"""
    text: Optional[TextFeatures] = None
    voice: Optional[VoiceFeatures] = None
    face: Optional[FaceFeatures] = None
    knowledge_correction: Optional[Dict[str, Any]] = None
    debate_round: int = 0
    speaker: str = ""

    def to_json(self) -> str:
        return self.model_dump_json(exclude_none=True, indent=2)
