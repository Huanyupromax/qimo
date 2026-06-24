"""
knowledge_base/kb_train.py
知识库训练脚本 - 处理视频/音频，构建数据集，训练基线模型
"""
import os, sys, json, random, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pathlib import Path
from knowledge_base.kb_processor import KBVideoProcessor
from knowledge_base.dataset import split_dataset, save_splits, load_dataset, samples_to_feature_matrix
from models.baseline import BaselineModels


def run_pipeline(video_dir: str = r"E:\辩论视频",
                 output_dir: str = "knowledge_base/data",
                 use_audio: bool = True) -> dict:
    """完整流水线：扫描 → 特征提取 → 数据集 → 训练"""
    result = {"steps": {}}
    processor = KBVideoProcessor(video_dir)

    # Step 1: 扫描视频
    print("[1/5] 扫描视频文件...")
    files = processor.scan_videos()
    result["steps"]["scan"] = {"total_files": len(files)}
    print(f"  找到 {len(files)} 个媒体文件")
    if not files:
        return result

    # Step 2: 提取特征，构建样本
    print("[2/5] 特征提取...")
    samples = []
    for idx, f in enumerate(files):
        if idx >= 50:  # 限制处理数量
            break
        sample = {"source": f["name"], "folder": f["folder"], "size_mb": f["size_mb"]}
        # 音频特征提取
        if use_audio and f["ext"] in [".mp3", ".wav", ".m4a"]:
            try:
                vf = processor.extract_audio_features(f["path"])
                sample["voice_features"] = vf
            except:
                sample["voice_features"] = {}
        # 基于规则生成DPM伪标签
        text_feats = processor.extract_text_features_rule(f["name"])
        sample["text_features"] = text_feats
        sample["dpm_labels"] = processor.generate_dpm_labels(text_feats)
        samples.append(sample)
        if idx % 10 == 0:
            print(f"  ... {idx}/{len(files)}")

    result["steps"]["features"] = {"samples": len(samples)}
    print(f"  构建 {len(samples)} 条样本")

    # Step 3: 8:1:1切分
    print("[3/5] 数据集切分 8:1:1...")
    train, val, test = split_dataset(samples)
    save_splits(train, val, test, output_dir)
    result["steps"]["split"] = {"train": len(train), "val": len(val), "test": len(test)}

    # Step 4: 转换为特征矩阵
    print("[4/5] 特征矩阵转换...")
    X_train, y_train = samples_to_feature_matrix(train)
    X_val, y_val = samples_to_feature_matrix(val)
    X_test, y_test = samples_to_feature_matrix(test)
    print(f"  训练集: {len(X_train)} 样本, {len(X_train[0]) if X_train else 0} 特征")
    print(f"  验证集: {len(X_val)} 样本")
    print(f"  测试集: {len(X_test)} 样本")

    # Step 5: 训练基线模型
    print("[5/5] 训练基线模型...")
    bm = BaselineModels()
    results = bm.training_pipeline(X_train, y_train, X_val, y_val)
    result["steps"]["training"] = results

    # 输出评估结果
    if "random_forest_eval" in results:
        eval_result = results["random_forest_eval"]
        print(f"  RandomForest 验证 MAE: {eval_result.get('total_mae', 'N/A')}")
        for dim, scores in eval_result.items():
            if dim != "samples" and isinstance(scores, dict):
                print(f"    {dim}: MAE={scores.get('mae','?')}, RMSE={scores.get('rmse','?')}")

    # 保存模型
    bm.save("models/saved")
    print("  模型已保存至 models/saved/")

    result["model_path"] = "models/saved"
    result["status"] = "complete"
    return result


if __name__ == "__main__":
    print("=" * 60)
    print("  辩境 - 知识库训练流水线")
    print("=" * 60)
    r = run_pipeline()
    print(f"\n状态: {r.get('status', 'partial')}")
    print(f"样本数: {r.get('steps', {}).get('features', {}).get('samples', 0)}")
    print(f"训练集: {r.get('steps', {}).get('split', {}).get('train', 0)}")
    print(f"验证集: {r.get('steps', {}).get('split', {}).get('val', 0)}")
    print(f"测试集: {r.get('steps', {}).get('split', {}).get('test', 0)}")
    if "random_forest_eval" in r.get('steps', {}).get('training', {}):
        mae = r["steps"]["training"]["random_forest_eval"].get("total_mae", "?")
        print(f"RF验证MAE: {mae}")
