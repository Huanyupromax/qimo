class KnowledgeBaseCorrector:
    def __init__(self):
        self.log = []
    def correct(self, text=None, voice=None, face=None):
        result = {}
        if text: result["text"] = dict(text)
        if voice: result["voice"] = dict(voice)
        if face: result["face"] = dict(face)
        self.log.append({"type":"correction"})
        return result
