import sqlite3,os
from pathlib import Path
class UserDB:
 def __init__(s):
  d=Path(__file__).parent/"data";d.mkdir(exist_ok=True,parents=True)
  s.db=str(d/"users.db");c=sqlite3.connect(s.db)
  c.execute("CREATE TABLE IF NOT EXISTS users(username TEXT PRIMARY KEY,password_hash TEXT,salt TEXT)")
  c.commit();c.close()
 def add_user(s,u,h,sa):
  c=sqlite3.connect(s.db);c.execute("INSERT OR REPLACE INTO users VALUES(?,?,?)",(u,h,sa));c.commit();c.close()
 def get_user(s,u):
  c=sqlite3.connect(s.db);c.row_factory=sqlite3.Row
  r=c.execute("SELECT*FROM users WHERE username=?",(u,)).fetchone();c.close()
  return dict(r) if r else None
 def user_exists(s,u):
  c=sqlite3.connect(s.db)
  return c.execute("SELECT 1 FROM users WHERE username=?",(u,)).fetchone() is not None
