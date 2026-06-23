"""视频流处理：帧采样、人脸分析"""
import time, tempfile
import cv2
import numpy as np
from modalities.face import FaceAnalyzer

class VideoStreamProcessor:
    def __init__(self, sample_interval=5):
        self.sample_interval = sample_interval
        self.frame_count = 0
        self.buffer = []
        self.face_analyzer = FaceAnalyzer()

    def process_frame(self, frame_bytes, timestamp=None):
        ts = timestamp or time.time()
        self.frame_count += 1
        if self.frame_count % self.sample_interval != 0:
            return None
        nparr = np.frombuffer(frame_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if frame is None:
            return None
        face_result = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
                cv2.imwrite(f.name, frame)
                face_r = self.face_analyzer.analyze_frame(f.name)
                if face_r:
                    face_result = face_r.model_dump() if hasattr(face_r, "model_dump") else face_r.__dict__
        except:
            pass
        entry = {
            "timestamp": ts,
            "frame_number": self.frame_count,
            "face_analysis": face_result,
            "shape": list(frame.shape) if frame is not None else None,
        }
        self.buffer.append(entry)
        return entry

    def clear(self):
        self.buffer = []
        self.frame_count = 0
