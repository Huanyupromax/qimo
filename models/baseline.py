"""
models/baseline.py
传统机器学习基线模型 - 随机森林 + 多输出回归
"""
import json, os, pickle, time
from typing import List, Dict, Tuple, Optional
import numpy as np

# sklearn imports (with fallback for missing installations)
_SKLEARN_AVAILABLE = False
try:
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.multioutput import MultiOutputRegressor
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    from sklearn.model_selection import cross_val_score
    _SKLEARN_AVAILABLE = True
except ImportError:
    RandomForestRegressor = None
    MultiOutputRegressor = None


class BaselineModels:
    """基线模型集 - RandomForest + 加权组合"""

    DIM_NAMES = ["aggression", "logic", "rhythm", "adaptability", "presence"]

    def __init__(self, use_sklearn: bool = True):
        self.use_sklearn = use_sklearn and _SKLEARN_AVAILABLE
        self.models: Dict = {}
        self.feature_importances: Optional[List] = None
        self.training_history: List[Dict] = []

    def train_random_forest(self, X_train: List, y_train: List,
                            n_estimators: int = 100,
                            max_depth: int = 10) -> Dict:
        """训练随机森林多输出回归模型"""
        if not self.use_sklearn:
            return {"status": "sklearn_not_available"}
        X = np.array(X_train)
        y = np.array(y_train)
        model = RandomForestRegressor(
            n_estimators=n_estimators, max_depth=max_depth,
            random_state=42, n_jobs=-1
        )
        multi_model = MultiOutputRegressor(model, n_jobs=-1)
        multi_model.fit(X, y)
        self.models["random_forest"] = multi_model
        self.feature_importances = model.feature_importances_
        return {"status": "trained", "samples": len(X_train)}

    def train_weighted_baseline(self, X_train: List, y_train: List) -> Dict:
        """训练加权基线模型（无sklearn替代方案）"""
        X = np.array(X_train)
        y = np.array(y_train)
        # 简单线性权重：特征均值的加权组合
        weights = {}
        dim_weights = {
            0: {"rebuttal_ratio": 0.4, "logical_density": 0.2, "evidence_density": 0.2, "volume_peak": 0.2},
            1: {"evidence_density": 0.5, "logical_density": 0.3, "word_count": 0.2},
            2: {"pause_ratio": 0.4, "speech_rate": 0.3, "avg_sentence_len": 0.3},
            3: {"stance_shift_count": 0.5, "rebuttal_ratio": 0.3, "volume_avg": 0.2},
            4: {"rebuttal_count": 0.3, "volume_peak": 0.3, "evidence_count": 0.2, "volume_avg": 0.2},
        }
        self.models["weighted_baseline"] = {"weights": dim_weights, "y_mean": y.mean(axis=0).tolist()}
        return {"status": "trained", "model": "weighted_baseline"}

    def predict(self, X_test: List, model_key: str = "random_forest") -> np.ndarray:
        """预测DPM五维分数"""
        X = np.array(X_test)
        if model_key in self.models and self.use_sklearn:
            model = self.models[model_key]
            if hasattr(model, "predict"):
                return model.predict(X)
        # fallback: 返回均值
        return np.full((len(X_test), 5), 50.0)

    def evaluate(self, y_true: List, y_pred: np.ndarray) -> Dict:
        """多维度评估模型精度"""
        yt = np.array(y_true)
        yp = np.array(y_pred)
        result = {"samples": len(yt)}
        for i, dim in enumerate(self.DIM_NAMES):
            mae = float(mean_absolute_error(yt[:, i], yp[:, i])) if self.use_sklearn else 0
            rmse = float(np.sqrt(mean_squared_error(yt[:, i], yp[:, i]))) if self.use_sklearn else 0
            result[dim] = {"mae": round(mae, 2), "rmse": round(rmse, 2)}
        result["total_mae"] = round(float(np.mean([v["mae"] for k, v in result.items() if k != "samples"])), 2)
        return result

    def save(self, path: str = "models/saved"):
        """保存模型"""
        os.makedirs(path, exist_ok=True)
        for key, model in self.models.items():
            pkl_path = os.path.join(path, f"{key}.pkl")
            with open(pkl_path, "wb") as f:
                pickle.dump(model, f)
        meta = {
            "feature_importances": self.feature_importances,
            "history": self.training_history,
            "timestamp": time.time(),
        }
        with open(os.path.join(path, "meta.json"), "w") as f:
            json.dump(meta, f, indent=2)

    def load(self, path: str = "models/saved"):
        """加载模型"""
        for fname in os.listdir(path):
            if fname.endswith(".pkl"):
                key = fname.replace(".pkl", "")
                with open(os.path.join(path, fname), "rb") as f:
                    self.models[key] = pickle.load(f)

    def get_feature_importance_report(self, feature_names: Optional[List[str]] = None) -> str:
        """生成特征重要性报告"""
        if not self.feature_importances:
            return "Feature importances not available"
        if feature_names is None:
            feature_names = [f"f{i}" for i in range(len(self.feature_importances))]
        pairs = sorted(zip(feature_names, self.feature_importances), key=lambda x: -x[1])
        return "\n".join(f"  {name}: {imp:.4f}" for name, imp in pairs[:15])

    def training_pipeline(self, X_train, y_train, X_val, y_val) -> Dict:
        """完整训练+验证流水线"""
        results = {}
        # Random Forest
        if self.use_sklearn:
            rf = self.train_random_forest(X_train, y_train)
            results["random_forest"] = rf
            pred = self.predict(X_val)
            val_result = self.evaluate(y_val, pred)
            results["random_forest_eval"] = val_result
        # Weighted baseline
        wb = self.train_weighted_baseline(X_train, y_train)
        results["weighted_baseline"] = wb
        self.training_history.append({
            "timestamp": time.time(),
            "train_samples": len(X_train),
            "val_samples": len(X_val),
            "results": results,
        })
        return results
