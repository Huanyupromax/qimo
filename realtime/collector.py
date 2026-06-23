from scoring import ScoringEngine
class RealtimeCollector:
 def __init__(s):s.scoring=ScoringEngine();s.current_session=None
 def start_session(s,sid):s.current_session=sid;s.scoring=ScoringEngine()
 def get_scoring(s):return s.scoring
 def get_scoring_scores(s):return s.scoring.get()
 def get_scoring_report(s,u="",t="",rd=0):return s.scoring.report(user=u,topic=t,rd=rd)
 def add_text(s,*a,**k):return {}
 def add_audio(s,*a,**k):return {}
 def add_video(s,*a,**k):return {}
