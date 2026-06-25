"""
knowledge_base/kb_processor.py
辩论视频知识库处理流水线
提取多模态特征，构建结构化数据集
"""
import os, json, csv, time, random
from typing import List, Dict, Optional, Tuple
from pathlib import Path


class KBVideoProcessor:
    """辩论视频知识库处理器 - 提取特征构建数据集"""

    DIMENSIONS = ["aggression", "logic", "rhythm", "adaptability", "presence"]

    def __init__(self, video_base_dir: str = r"E:\辩论视频"):
        self.base_dir = Path(video_base_dir)
        self.dataset: List[Dict] = []

    def scan_videos(self) -> List[Dict]:
        """扫描视频文件夹，返回视频/音频文件列表"""
        files = []
        if not self.base_dir.exists():
            return files
        for root, dirs, fnames in os.walk(str(self.base_dir)):
            for f in fnames:
                ext = Path(f).suffix.lower()
                if ext in [".mp4", ".mp3", ".wav", ".m4a", ".avi", ".mov"]:
                    files.append({
                        "path": os.path.join(root, f),
                        "name": f,
                        "ext": ext,
                        "folder": os.path.basename(root),
                        "size_mb": round(os.path.getsize(os.path.join(root, f)) / (1024*1024), 1),
                    })
        return files

    def extract_audio_features(self, audio_path: str) -> Dict:
        """提取音频基础特征（无librosa时的规则引擎替代）"""
        import wave, struct, math
        features = {
            "duration": 0, "volume_peak": 0, "volume_avg": 0,
            "speech_rate": 0.5, "pause_ratio": 0.15,
        }
        try:
            with wave.open(audio_path, "rb") as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                duration = frames / rate
                features["duration"] = round(duration, 1)
                if duration > 0:
                    # 读取采样点估算音量
                    chunk = min(frames, rate * 10)  # 最多10秒
                    raw = wf.readframes(chunk)
                    if raw:
                        samples = struct.unpack(f"<{len(raw)//2}h", raw[:len(raw)//2*2])
                        peak = max(abs(s) for s in samples) / 32768.0
                        avg = sum(abs(s) for s in samples) / len(samples) / 32768.0
                        features["volume_peak"] = round(peak, 3)
                        features["volume_avg"] = round(avg, 3)
        except Exception as e:
            features["error"] = str(e)
        return features

    def extract_text_features_rule(self, transcript: str) -> Dict:
        """基于规则的文本特征提取"""
        sentences = [s.strip() for s in transcript.replace("！","。").replace("？","。").split("。") if s.strip()]
        words = transcript.split()
        word_count = len(words)
        sentence_count = len(sentences)

        # 反驳标记检测
        rebuttal_keywords = ["但是", "然而", "可是", "不过", "问题在于", "恰恰相反",
                            "事实上", "实际上", "难道", "怎么能", "凭什么"]
        rebuttal_count = sum(1 for kw in rebuttal_keywords if kw in transcript)

        # 逻辑连接词检测
        logic_keywords = ["因此", "所以", "因为", "如果", "那么", "由此", "可见",
                         "综上所述", "第一", "第二", "首先", "其次", "最后"]
        logic_count = sum(1 for kw in logic_keywords if kw in transcript)

        # 证据引用检测
        evidence_keywords = ["数据显示", "据统计", "研究表明", "根据", "调查显示",
                           "报告指出", "数据表明", "例如", "比如", "参照"]
        evidence_count = sum(1 for kw in evidence_keywords if kw in transcript)

        # 立场转换
        stance_keywords = ["从另一个角度看", "退一步说", "换个思路", "另一方面",
                          "不可否认", "虽然"]
        stance_count = sum(1 for kw in stance_keywords if kw in transcript)

        rebuttal_ratio = rebuttal_count / max(sentence_count, 1)
        logic_density = logic_count / max(word_count, 1) * 100
        evidence_density = evidence_count / max(word_count, 1) * 100

        return {
            "word_count": word_count,
            "sentence_count": sentence_count,
            "rebuttal_count": rebuttal_count,
            "rebuttal_ratio": round(rebuttal_ratio, 3),
            "logic_count": logic_count,
            "logical_density": round(logic_density, 2),
            "evidence_count": evidence_count,
            "evidence_density": round(evidence_density, 2),
            "stance_shift_count": stance_count,
            "avg_sentence_len": round(word_count / max(sentence_count, 1), 1),
        }

    def generate_dpm_labels(self, features: Dict, style: str = "balanced") -> Dict:
        """基于规则生成DPM伪标签（有真实评分后可替换）"""
        scores = {}
        # 进攻性
        aggression = min(100, (
            features.get("rebuttal_ratio", 0) * 60 +
            features.get("evidence_density", 0) * 0.3 +
            features.get("stance_shift_count", 0) * 3
        ))
        scores["aggression"] = round(aggression, 1)

        # 逻辑密度
        logic = min(100, (
            features.get("logical_density", 0) * 3 +
            features.get("evidence_density", 0) * 0.5
        ))
        scores["logic"] = round(logic, 1)

        # 节奏控制
        rhythm = min(100, 50 + random.uniform(-15, 15))
        scores["rhythm"] = round(rhythm, 1)

        # 弹性适应
        adaptability = min(100, features.get("stance_shift_count", 0) * 10 + 30)
        scores["adaptability"] = round(adaptability, 1)

        # 气势压制
        presence = min(100, features.get("rebuttal_count", 0) * 5 + 30)
        scores["presence"] = round(presence, 1)

        return scores

    def build_sample(self, video_info: Dict, transcript: str = "",
                     voice_features: Optional[Dict] = None) -> Dict:
        """构建单条训练样本"""
        text_feats = self.extract_text_features_rule(transcript)
        sample = {
            "source": video_info.get("name", "unknown"),
            "folder": video_info.get("folder", ""),
            "text_features": text_feats,
        }
        if voice_features:
            sample["voice_features"] = voice_features
        sample["dpm_labels"] = self.generate_dpm_labels(text_feats)
        return sample

    def save_dataset(self, samples: List[Dict], output_path: str):
        """保存数据集为JSON"""
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(samples, f, ensure_ascii=False, indent=2)
