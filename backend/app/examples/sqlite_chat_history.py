"""
SQLite 版 BaseChatMessageHistory（不依赖已日落的 langchain-community）。

模块级按 db 路径复用连接，减少反复 sqlite3.connect 的开销。
"""

from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, message_to_dict, messages_from_dict

# 按绝对路径复用连接（check_same_thread=False，供 Gradio 线程池使用）
_connections: dict[str, sqlite3.Connection] = {}
_conn_lock = threading.Lock()


def _shared_connection(db_path: Path) -> sqlite3.Connection:
    key = str(db_path.resolve())
    with _conn_lock:
        conn = _connections.get(key)
        if conn is None:
            conn = sqlite3.connect(key, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            # WAL：读写更不易互相堵住（教程级并发足够）
            conn.execute("PRAGMA journal_mode=WAL")
            _connections[key] = conn
        return conn


class SqliteChatMessageHistory(BaseChatMessageHistory):
    """按 session_id 把对话消息持久化到本地 SQLite。"""

    def __init__(
        self,
        session_id: str,
        *,
        db_path: str | Path,
        table_name: str = "message_store",
    ) -> None:
        self.session_id = session_id
        self.db_path = Path(db_path)
        self.table_name = table_name
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_table()

    def _connect(self) -> sqlite3.Connection:
        return _shared_connection(self.db_path)

    def _ensure_table(self) -> None:
        conn = self._connect()
        with _conn_lock:
            conn.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    message TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                f"""
                CREATE INDEX IF NOT EXISTS ix_{self.table_name}_session
                ON {self.table_name}(session_id)
                """
            )
            conn.commit()

    @property
    def messages(self) -> list[BaseMessage]:
        conn = self._connect()
        with _conn_lock:
            rows = conn.execute(
                f"""
                SELECT message FROM {self.table_name}
                WHERE session_id = ?
                ORDER BY id ASC
                """,
                (self.session_id,),
            ).fetchall()
        raw = [json.loads(row["message"]) for row in rows]
        return messages_from_dict(raw)

    def add_message(self, message: BaseMessage) -> None:
        self.add_messages([message])

    def add_messages(self, messages: list[BaseMessage]) -> None:
        if not messages:
            return
        rows = [
            (self.session_id, json.dumps(message_to_dict(m), ensure_ascii=False))
            for m in messages
        ]
        conn = self._connect()
        with _conn_lock:
            conn.executemany(
                f"""
                INSERT INTO {self.table_name} (session_id, message)
                VALUES (?, ?)
                """,
                rows,
            )
            conn.commit()

    def clear(self) -> None:
        conn = self._connect()
        with _conn_lock:
            conn.execute(
                f"DELETE FROM {self.table_name} WHERE session_id = ?",
                (self.session_id,),
            )
            conn.commit()
