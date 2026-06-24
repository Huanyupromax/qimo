"""
knowledge_base/enhanced_corrector.py
辩论专业知识库双层规则纠偏系统
在通用粗判层和打分计算层中间插入知识库纠偏
"""
from typing import Dict, List, Optional, Any, Tuple
from .models import KBConfig
from .emotion_map import EmotionFeatureMapper
from .behavior_lib import BehaviorLibrary
import json, time, copy


class EnhancedCorrector:
    """增强版知识库纠偏器 - 双层映射 + 规则引擎 + 修正溯源"""

    def __init__(self, config: Optional[KBConfig] = None):
        self.config = config or KBConfig()
        self.emotion_mapper = EmotionFeatureMapper()
        self.behavior_lib = BehaviorLibrary()
        self.correction_log: List[Dict] = []
        self.correction_count = 0

        # 第一层：通用情绪 → 辩论特征映射规则库
        self.emotion_debate_rules = {
            "angry": {"aggression": 0.85, "presence": 0.75, "rhythm_risk": 0.3},
            "happy": {"aggression": 0.30, "adaptability": 0.70, "presence": 0.50},
            "neutral": {"aggression": 0.50, "logic": 0.60, "rhythm": 0.55},
            "sad": {"aggression": 0.20, "adaptability": 0.35, "presence_risk": -0.2},
            "surprise": {"aggression": 0.65, "adaptability": 0.80, "presence": 0.60},
            "fear": {"aggression": 0.15, "adaptability": 0.25, "rhythm_risk": 0.4},
            "disgust": {"aggression": 0.75, "presence": 0.70, "logic": 0.30},
        }
        # 第二层：辩论特征 → DPM五维维度调整

        self.feature_dpm_rules = {
            "aggression": {"aggression": 8.0, "presence": 3.0},
            "intensity": {"presence": 5.0, "aggression": 2.0},
            "logic_density": {"logic": 9.0, "rhythm": -1.0},
            "rebuttal_ratio": {"aggression": 7.0, "adaptability": 4.0},
            "rhythm_stability": {"rhythm": 8.0, "adaptability": 3.0},
            "evidence_density": {"logic": 10.0, "presence": 3.0},
            "volume_control": {"presence": 4.0, "rhythm": 5.0},
            "speech_pause": {"rhythm": 6.0, "adaptability": -2.0},
        }

    def correct_text(self, text_features: Dict) -> Dict:
        """文本模态知识库纠偏"""
        if not self.config.enabled:
            return {"corrected": dict(text_features), "applied": False}

        emotion = text_features.get("dominant_emotion", "neutral")
        corrections = {}
        log_entry = {"type": "text", "emotion": emotion, "rules_applied": []}

        # 第一层：情绪纠偏
        if emotion in self.emotion_debate_rules:
            emotion_rules = self.emotion_debate_rules[emotion]
            for feature, adjustment in emotion_rules.items():
                corrections[feature] = corrections.get(feature, 0) + adjustment
                log_entry["rules_applied"].append(f"emotion.{feature}={adjustment}")

        # 检测辩论行为
        raw_text = text_features.get("text", "")
        detected_behaviors = self.behavior_lib.detect_text(raw_text)
        for behavior in detected_behaviors:
            for dim, impact in behavior.score_impact.items():
                corrections[dim] = corrections.get(dim, 0) + impact / 10.0
                log_entry["rules_applied"].append(f"behavior.{behavior.behavior_id}.{dim}=+{impact/10}")

        # 第二层：特征 → DPM维度
        for feature, adjustments in self.feature_dpm_rules.items():
            if feature in text_features:
                strength = text_features[feature]
                for dim, val in adjustments.items():
                    dim_key = f"dpm_{dim}"
                    corrections[dim_key] = corrections.get(dim_key, 0) + val * strength

        result = dict(text_features)
        for k, v in corrections.items():
            if k.startswith("dpm_"):
                result[k] = result.get(k, 0) + v

        result["kb_corrected"] = True
        result["kb_corrections"] = corrections

        log_entry["corrections"] = corrections
        log_entry["timestamp"] = time.time()
        self.correction_log.append(log_entry)
        self.correction_count += 1

        return {"corrected": result, "applied": True, "log": log_entry}

    def correct_voice(self, voice_features: Dict) -> Dict:
        """语音模态知识库纠偏"""
        if not self.config.enabled:
            return {"corrected": dict(voice_features), "applied": False}

        corrections = {}
        log_entry = {"type": "voice", "rules_applied": []}

        # 语速稳定性分析
        speech_rate = voice_features.get("speech_rate", 0)
        rate_stability = voice_features.get("rate_stability", 0.5)
        if speech_rate > 0:
            if rate_stability > 0.7:
                corrections["dpm_rhythm"] = corrections.get("dpm_rhythm", 0) + 8
                log_entry["rules_applied"].append("rhythm.stable_rate=+8")
            elif rate_stability < 0.3:
                corrections["dpm_rhythm"] = corrections.get("dpm_rhythm", 0) - 3
                log_entry["rules_applied"].append("rhythm.unstable_rate=-3")

        # 音量峰值分析
        volume_peak = voice_features.get("volume_peak", 0)
        if volume_peak > 0.7:
            corrections["dpm_aggression"] = corrections.get("dpm_aggression", 0) + 6
            corrections["dpm_presence"] = corrections.get("dpm_presence", 0) + 5
            log_entry["rules_applied"].append("voice.high_peak=+6agg,+5pres")
        elif volume_peak < 0.3:
            corrections["dpm_presence"] = corrections.get("dpm_presence", 0) - 2
            log_entry["rules_applied"].append("voice.low_peak=-2pres")

        # 停顿分析
        pause_ratio = voice_features.get("pause_ratio", 0)
        if pause_ratio > 0.3:
            corrections["dpm_rhythm"] = corrections.get("dpm_rhythm", 0) + 4
            corrections["dpm_adaptability"] = corrections.get("dpm_adaptability", 0) - 2
            log_entry["rules_applied"].append("voice.high_pause=+4rhy,-2ada")
        elif pause_ratio < 0.05:
            corrections["dpm_aggression"] = corrections.get("dpm_aggression", 0) + 2
            log_entry["rules_applied"].append("voice.low_pause=+2agg")

        result = dict(voice_features)
        for k, v in corrections.items():
            result[k] = result.get(k, 0) + v
        result["kb_corrected"] = True
        result["kb_corrections"] = corrections

        log_entry["corrections"] = corrections
        log_entry["timestamp"] = time.time()
        self.correction_log.append(log_entry)
        self.correction_count += 1

        return {"corrected": result, "applied": True, "log": log_entry}

    def correct_face(self, face_features: Dict) -> Dict:
        """面部表情模态知识库纠偏"""
        if not self.config.enabled:
            return {"corrected": dict(face_features), "applied": False}

        emotion = face_features.get("dominant_emotion", "neutral")
        au_intensities = face_features.get("au_intensities", {})
        corrections = {}
        log_entry = {"type": "face", "emotion": emotion, "rules_applied": []}

        # 情绪纠偏（竞技施压 vs 负面情绪区分）
        if emotion == "angry":
            # 有知识库后，anger在高竞技场景下应解释为"施压"而非"愤怒"
            if au_intensities.get("au04", 0) > 0.6:  # 眉毛压低 = 专注/施压
                corrections["dpm_presence"] = corrections.get("dpm_presence", 0) + 6
                corrections["dpm_aggression"] = corrections.get("dpm_aggression", 0) + 4
                log_entry["rules_applied"].append("face.angry_au04=professional_pressure")
            else:
                corrections["dpm_aggression"] = corrections.get("dpm_aggression", 0) + 3
                log_entry["rules_applied"].append("face.angry_generic=+3agg")

        elif emotion == "surprise":
            if au_intensities.get("au01", 0) > 0.5:  # 眉毛上抬 = 警觉/快速反应
                corrections["dpm_adaptability"] = corrections.get("dpm_adaptability", 0) + 7
                log_entry["rules_applied"].append("face.surprise_au01=quick_response+7ada")
            else:
                corrections["dpm_adaptability"] = corrections.get("dpm_adaptability", 0) + 3
                log_entry["rules_applied"].append("face.surprise_generic=+3ada")

        # 头部姿态 - 自信度
        head_pose = face_features.get("head_pose", {})
        if head_pose.get("pitch", 0) > 15:  # 仰头 = 自信/气势
            corrections["dpm_presence"] = corrections.get("dpm_presence", 0) + 4
            log_entry["rules_applied"].append("face.head_up=+4pres")

        result = dict(face_features)
        for k, v in corrections.items():
            result[k] = result.get(k, 0) + v
        result["kb_corrected"] = True
        result["kb_corrections"] = corrections

        log_entry["corrections"] = corrections
        log_entry["timestamp"] = time.time()
        self.correction_log.append(log_entry)
        self.correction_count += 1

        return {"corrected": result, "applied": True, "log": log_entry}

    def multimodal_correct(self, text: Optional[Dict] = None,
                           voice: Optional[Dict] = None,
                           face: Optional[Dict] = None) -> Dict:
        """三模态统一纠偏入口"""
        result = {"text": {}, "voice": {}, "face": {},
                  "dpm_adjustments": {}, "logs": []}
        if text:
            t = self.correct_text(text)
            result["text"] = t["corrected"]
            if t.get("applied"):
                result["logs"].append(t.get("log", {}))
        if voice:
            v = self.correct_voice(voice)
            result["voice"] = v["corrected"]
            if v.get("applied"):
                result["logs"].append(v.get("log", {}))
        if face:
            f = self.correct_face(face)
            result["face"] = f["corrected"]
            if f.get("applied"):
                result["logs"].append(f.get("log", {}))

        # 聚合所有DPM调整
        all_dpm = {}
        for modality in ["text", "voice", "face"]:
            corr = result[modality].get("kb_corrections", {})
            for k, v in corr.items():
                if k.startswith("dpm_"):
                    dim = k.replace("dpm_", "")
                    all_dpm[dim] = all_dpm.get(dim, 0) + v
        result["dpm_adjustments"] = all_dpm
        result["kb_applied"] = bool(all_dpm)
        return result

    def get_correction_log(self, limit: int = 50) -> List[Dict]:
        """获取修正日志"""
        return self.correction_log[-limit:]

    def get_stats(self) -> Dict:
        """获取纠偏统计"""
        return {
            "total_corrections": self.correction_count,
            "log_size": len(self.correction_log),
            "enabled": self.config.enabled,
            "debug": self.config.debug_mode,
        }

    def toggle_mode(self, enabled: Optional[bool] = None) -> bool:
        """切换纠偏模式"""
        if enabled is not None:
            self.config.enabled = enabled
        else:
            self.config.enabled = not self.config.enabled
        return self.config.enabled
