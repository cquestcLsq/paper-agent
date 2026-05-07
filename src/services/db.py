"""
SQLite 历史记录服务
"""
import sqlite3
import json
from datetime import datetime
from typing import Optional


DB_PATH = "history.db"


def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """创建表（如果不存在）"""
    conn = _get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS research_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            papers_json TEXT NOT NULL,
            report_zh TEXT DEFAULT '',
            report_en TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def save_research(query: str, papers: list, report_zh: str, report_en: str) -> int:
    """保存一次调研记录，返回记录 ID"""
    conn = _get_conn()
    cursor = conn.execute(
        "INSERT INTO research_history (query, papers_json, report_zh, report_en) VALUES (?, ?, ?, ?)",
        (query, json.dumps(papers, ensure_ascii=False), report_zh, report_en)
    )
    conn.commit()
    row_id = cursor.lastrowid
    conn.close()
    return row_id


def get_all_history() -> list:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT id, query, datetime(created_at, 'localtime') as created_at FROM research_history ORDER BY created_at DESC LIMIT 50"
    ).fetchall()
    conn.close()
    return [{"id": r["id"], "query": r["query"], "created_at": r["created_at"]} for r in rows]


def get_history_by_id(history_id: int) -> Optional[dict]:
    """获取单条历史记录的完整信息"""
    conn = _get_conn()
    row = conn.execute(
        "SELECT * FROM research_history WHERE id = ?", (history_id,)
    ).fetchone()
    conn.close()
    if row:
        return {
            "id": row["id"],
            "query": row["query"],
            "papers": json.loads(row["papers_json"]),
            "report_zh": row["report_zh"],
            "report_en": row["report_en"],
            "created_at": row["created_at"]
        }
    return None


def delete_history(history_id: int):
    """删除一条历史记录"""
    conn = _get_conn()
    conn.execute("DELETE FROM research_history WHERE id = ?", (history_id,))
    conn.commit()
    conn.close()


# 启动时自动初始化
init_db()