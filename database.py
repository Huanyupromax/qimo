"""User database - SQLite persistent storage"""
import sqlite3, hashlib, datetime, os
from pathlib import Path

class UserDB:
    def __init__(self, db_path=None):
        if db_path is None:
            db_dir = Path(__file__).parent / "data"
            db_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(db_dir / "users.db")
        self.db_path = db_path
        self._init()

    def _init(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password_hash TEXT NOT NULL, salt TEXT NOT NULL, created_at TEXT)")
        conn.commit()
        conn.close()

    def add_user(self, username, password_hash, salt):
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("INSERT INTO users (username, password_hash, salt, created_at) VALUES (?,?,?,datetime('now'))", (username, password_hash, salt))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False

    def get_user(self, username):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {"username": row["username"], "password_hash": row["password_hash"], "salt": row["salt"]}
        return None

    def user_exists(self, username):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("SELECT 1 FROM users WHERE username = ?", (username,))
        exists = cursor.fetchone() is not None
        conn.close()
        return exists

    def count_users(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        conn.close()
        return count

class ReportDB:
    """辩论报告数据库"""
    def __init__(self, db_path=None):
        from pathlib import Path
        if db_path is None:
            p = Path(__file__).parent / "data"
            p.mkdir(parents=True, exist_ok=True)
            db_path = str(p / "reports.db")
        self.db_path = db_path
        self._init()

    def _init(self):
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        conn.execute("CREATE TABLE IF NOT EXISTS reports (id TEXT PRIMARY KEY, username TEXT NOT NULL, topic TEXT, rounds INTEGER DEFAULT 0, timestamp REAL, dbti_code TEXT, dbti_name TEXT, total_score INTEGER, report_json TEXT)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_uname ON reports(username)")
        conn.commit()
        conn.close()

    def save(self, rid, username, data):
        import sqlite3, json
        conn = sqlite3.connect(self.db_path)
        conn.execute("INSERT OR REPLACE INTO reports VALUES (?,?,?,?,?,?,?,?,?)",
            (rid, username, data.get("topic",""), data.get("rounds",0),
             data.get("timestamp",0), data.get("dbti_code",""),
             data.get("dbti_name",""), data.get("total",0),
             json.dumps(data, ensure_ascii=False)))
        conn.commit()
        conn.close()

    def list(self, username, limit=50):
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT id, topic, rounds, timestamp, dbti_code, dbti_name, total_score FROM reports WHERE username=? ORDER BY timestamp DESC LIMIT ?", (username, limit)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get(self, rid):
        import sqlite3, json
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM reports WHERE id=?", (rid,)).fetchone()
        conn.close()
        if row:
            d = dict(row)
            d["report"] = json.loads(d.pop("report_json"))
            return d
        return None