"""
knowledge_base/dataset.py
数据集切分工具 - 8:1:1 训练/验证/测试
"""
import json, random, os
from typing import List, Dict, Tuple, Optional


def split_dataset(samples: List[Dict],
                  ratios: Tuple[float, float, float] = (0.8, 0.1, 0.1),
                  seed: int = 42) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """8:1:1 切分数据集"""
    assert abs(sum(ratios) - 1.0) < 0.01, "Ratios must sum to 1.0"
    random.seed(seed)
    shuffled = list(samples)
    random.shuffle(shuffled)
    n = len(shuffled)
    train_end = int(n * ratios[0])
    val_end = train_end + int(n * ratios[1])
    train = shuffled[:train_end]
    val = shuffled[train_end:val_end]
    test = shuffled[val_end:]
    return train, val, test


def save_splits(train: List[Dict], val: List[Dict], test: List[Dict],
                output_dir: str = "knowledge_base/data"):
    """保存切分后的数据集"""
    os.makedirs(output_dir, exist_ok=True)
    for name, data in [("train", train), ("val", val), ("test", test)]:
        path = os.path.join(output_dir, f"{name}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"  {name}: {len(data)} samples -> {path}")


def load_dataset(path: str) -> List[Dict]:
    """加载JSON数据集"""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def samples_to_feature_matrix(samples: List[Dict]) -> Tuple[List, List]:
    """将样本转换为特征矩阵 (X, y) for ML models"""
    X, y = [], []
    for s in samples:
        tf = s.get("text_features", {})
        vf = s.get("voice_features", {})
        row = [
            tf.get("word_count", 0),
            tf.get("sentence_count", 0),
            tf.get("rebuttal_count", 0),
            tf.get("rebuttal_ratio", 0),
            tf.get("logic_count", 0),
            tf.get("logical_density", 0),
            tf.get("evidence_count", 0),
            tf.get("evidence_density", 0),
            tf.get("stance_shift_count", 0),
            tf.get("avg_sentence_len", 0),
            vf.get("duration", 0),
            vf.get("volume_peak", 0),
            vf.get("volume_avg", 0),
            vf.get("speech_rate", 0.5),
            vf.get("pause_ratio", 0.15),
        ]
        X.append(row)
        labels = s.get("dpm_labels", {})
        y.append([
            labels.get("aggression", 50),
            labels.get("logic", 50),
            labels.get("rhythm", 50),
            labels.get("adaptability", 50),
            labels.get("presence", 50),
        ])
    return X, y
