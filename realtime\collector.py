import time
from scoring import ScoringEngine

class RealtimeCollector:
    def __init__(self):
        self.text = type("",(),{"buffer":[],"get_stats":lambda s:{"total":0}})
        self.audio = type("",(),{"buffer":[]})
        self.video = type("",(),{"buffer":[],"frame_count":0})
        self.scoring = ScoringEngine()
        self.current_session = None
    def start_session(self, sid):
        self.current_session = sid
        self.scoring = ScoringEngine()
    def add_text(self, speaker, content, ts=None):
        ts = ts or time.time()
        entry = {"speaker":speaker,"content":content,"timestamp":ts,"nlp":None}
        self.text.buffer.append(entry)
        return entry
    def add_audio(self, data, ts=None):
        ts = ts or time.time()
        return {"timestamp":ts}
    def add_video(self, data, ts=None):
        ts = ts or time.time()
        self.video.frame_count += 1
        return {"timestamp":ts}
    def get_scoring(self):
        return self.scoring
    def get_scoring_scores(self):
        return self.scoring.get()
    def get_scoring_report(self, user="", topic="", rd=0):
        return self.scoring.report(user=user, topic=topic, rd=rd)
    def save_analysis(self, data):
        pass
