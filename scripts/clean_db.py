import sqlite3
from pathlib import Path

db_path = Path('d:/Desktop/Juice_shop/qa-automation/data/qa_pipeline.db')
if db_path.exists():
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cur.fetchall()]
    for t in tables:
        try:
            cur.execute(f"DELETE FROM {t} WHERE task_key = 'JS-39'")
        except Exception:
            pass
        try:
            cur.execute(f"DELETE FROM {t} WHERE issue_key = 'JS-39'")
        except Exception:
            pass
    conn.commit()
    conn.close()
    print('SQLite database cleaned for JS-39.')
