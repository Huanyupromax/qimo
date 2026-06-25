"""视频人脸模态粗判模块 — DeepFace 集成"""

import os, base64, tempfile
from typing import Optional, List, Dict
from .models import FaceFeatures


# 7 类基础情绪
EMOTION_LABELS = ["angry", "disgust", "fear", "happy", "sad", "surprise", "neutral"]


class FaceAnalyzer:
    """人脸分析器 — 基于 DeepFace"""

    def __init__(self):
        self._deepface_available = False
        self._df = None
        try:
            from deepface import DeepFace
            self._df = DeepFace
            self._deepface_available = True
        except Exception as e:
            self._deepface_available = False
            print(f"[DeepFace load failed] {e}")

    @property
    def available(self) -> bool:
        """DeepFace 是否可用"""
        return self._deepface_available

    def analyze_frame(self, image_path: str) -> Optional[FaceFeatures]:
        """分析单张图片/帧"""
        if not self._deepface_available or not os.path.exists(image_path):
            return None
        try:
            result = self._df.analyze(
                img_path=image_path,
                actions=["emotion", "age", "gender"],
                enforce_detection=False,
                silent=True
            )
            if isinstance(result, list):
                result = result[0] if result else None
            if not result:
                return None

            features = FaceFeatures()
            # 情绪
            emotions = result.get("emotion", {})
            features.emotions = {k: round(v / 100.0, 4) for k, v in emotions.items()}
            features.dominant_emotion = result.get("dominant_emotion", "neutral")
            features.face_count = 1
            return features
        except Exception:
            return None

    def analyze_batch(self, image_paths: List[str]) -> List[FaceFeatures]:
        """批量分析多帧"""
        results = []
        for path in image_paths:
            result = self.analyze_frame(path)
            if result:
                results.append(result)
        return results

    def analyze_base64(self, b64_str: str) -> Optional[FaceFeatures]:
        """分析 base64 编码的图片"""
        try:
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
                if "," in b64_str:
                    b64_str = b64_str.split(",")[1]
                f.write(base64.b64decode(b64_str))
                tmp_path = f.name
            result = self.analyze_frame(tmp_path)
            os.unlink(tmp_path)
            return result
        except Exception:
            return None

    @staticmethod
    def get_emotion_label_cn(emotion: str) -> str:
        """英文情绪标签 → 中文"""
        mapping = {
            "angry": "愤怒", "disgust": "厌恶", "fear": "恐惧",
            "happy": "高兴", "sad": "悲伤", "surprise": "惊讶",
            "neutral": "中性",
        }
        return mapping.get(emotion, emotion)
