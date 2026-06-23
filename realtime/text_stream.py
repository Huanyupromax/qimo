"""文本流处理：缓存对话、分句、标记说话人、NLP分析"""
import re, time
from modalities.text import TextAnalyzer

class TextStreamProcessor:
    def __init__(self):
        self.buffer = []
        self.analyzer = TextAnalyzer()

    def process(self, speaker, content, timestamp=None):
        ts = timestamp or time.time()
        entry = {
            "speaker": speaker,
            "content": content,
            "timestamp": ts,
            "sentences": self._split(content),
            "nlp": None
        }
        try:
            nlp = self.analyzer.analyze(content)
            entry["nlp"] = nlp.model_dump() if hasattr(nlp, "model_dump") else nlp.__dict__
        except Exception as e:
            entry["nlp_error"] = str(e)
        self.buffer.append(entry)
        return entry

    def _split(self, text):
        return [s.strip() for s in re.split(r"[。！？!?\n]", text) if s.strip()]

    def get_recent(self, n=10):
        return self.buffer[-n:]

    def get_full(self):
        return self.buffer

    def clear(self):
        self.buffer = []

    def get_stats(self):
        uc = sum(1 for e in self.buffer if e["speaker"] == "user")
        ac = sum(1 for e in self.buffer if e["speaker"] == "ai")
        return {"total": len(self.buffer), "user": uc, "ai": ac, "chars": sum(len(e["content"]) for e in self.buffer)}
