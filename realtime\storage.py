"""本地会话存储管理"""
import json
from pathlib import Path

class SessionStorage:
    def __init__(self, base_path="data"):
        self.base_path = Path(base_path)

    def init_session(self, session_id):
        paths = {}
        for sub in ["text", "audio", "video", "analysis"]:
            p = self.base_path / session_id / sub
            p.mkdir(parents=True, exist_ok=True)
            paths[sub] = p
        return paths

    def list_sessions(self):
        if not self.base_path.exists():
            return []
        return sorted([d.name for d in self.base_path.iterdir() if d.is_dir()])

    def save_text(self, session_id, data):
        path = self.base_path / session_id / "text" / f"{data['timestamp']}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def save_audio(self, session_id, ts, audio_bytes):
        path = self.base_path / session_id / "audio" / f"{ts}.webm"
        with open(path, "wb") as f:
            f.write(audio_bytes)
        return str(path)

    def save_frame(self, session_id, ts, image_bytes):
        path = self.base_path / session_id / "video" / f"{ts}.jpg"
        with open(path, "wb") as f:
            f.write(image_bytes)
        return str(path)

    def save_analysis(self, session_id, data):
        path = self.base_path / session_id / "analysis" / f"{data['timestamp']}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_text(self, session_id):
        folder = self.base_path / session_id / "text"
        if not folder.exists():
            return []
        results = []
        for f in sorted(folder.glob("*.json"), key=lambda x: float(x.stem)):
            results.append(json.loads(f.read_text(encoding="utf-8")))
        return results
