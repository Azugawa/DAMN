#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库模块 - 使用 SQLite 存储对话历史
"""
import os
import json
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
from contextlib import contextmanager

from config import DATA_DIR


class Database:
    """SQLite 数据库管理类"""

    def __init__(self, db_path: str = None):
        """
        初始化数据库

        Args:
            db_path: 数据库文件路径
        """
        if db_path is None:
            db_path = os.path.join(DATA_DIR, "damn.db")

        self.db_path = db_path

        # 确保数据目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        # 初始化数据库
        self._init_db()

        print(f"✅ 数据库已初始化：{db_path}")

    @contextmanager
    def get_connection(self):
        """获取数据库连接的上下文管理器"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 返回字典形式的行
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def _init_db(self):
        """初始化数据库表"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 创建会话表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    mode TEXT DEFAULT 'free',
                    ielts_part INTEGER DEFAULT 1,
                    topic TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 创建消息表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    grammar_feedback TEXT,
                    search_used BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
                )
            """)

            # 创建索引
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_session_id
                ON messages(session_id)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_created_at
                ON messages(created_at)
            """)

            print("✅ 数据库表已创建")

    def create_session(self, title: str = "新对话", mode: str = "free",
                       ielts_part: int = 1, topic: str = None) -> int:
        """
        创建新会话

        Args:
            title: 会话标题
            mode: 模式 (free/ielts)
            ielts_part: 雅思部分
            topic: 雅思话题

        Returns:
            会话 ID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sessions (title, mode, ielts_part, topic)
                VALUES (?, ?, ?, ?)
            """, (title, mode, ielts_part, topic))
            return cursor.lastrowid

    def get_session(self, session_id: int) -> Optional[Dict]:
        """
        获取会话信息

        Args:
            session_id: 会话 ID

        Returns:
            会话信息字典，不存在则返回 None
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM sessions WHERE id = ?
            """, (session_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def list_sessions(self, limit: int = 50) -> List[Dict]:
        """
        获取会话列表

        Args:
            limit: 限制数量

        Returns:
            会话列表
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM sessions
                ORDER BY updated_at DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def delete_session(self, session_id: int) -> bool:
        """
        删除会话

        Args:
            session_id: 会话 ID

        Returns:
            True 表示成功
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM sessions WHERE id = ?
            """, (session_id,))
            return cursor.rowcount > 0

    def update_session(self, session_id: int, **kwargs) -> bool:
        """
        更新会话信息

        Args:
            session_id: 会话 ID
            **kwargs: 要更新的字段

        Returns:
            True 表示成功
        """
        if not kwargs:
            return False

        # 自动添加 updated_at
        kwargs['updated_at'] = datetime.now().isoformat()

        fields = ', '.join([f"{k} = ?" for k in kwargs.keys()])
        values = list(kwargs.values()) + [session_id]

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE sessions SET {fields} WHERE id = ?
            """, values)
            return cursor.rowcount > 0

    def add_message(self, session_id: int, role: str, content: str,
                    grammar_feedback: str = None, search_used: bool = False) -> int:
        """
        添加消息

        Args:
            session_id: 会话 ID
            role: 角色 (user/assistant)
            content: 消息内容
            grammar_feedback: 语法反馈
            search_used: 是否使用了搜索

        Returns:
            消息 ID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO messages (session_id, role, content, grammar_feedback, search_used)
                VALUES (?, ?, ?, ?, ?)
            """, (session_id, role, content, grammar_feedback, search_used))

            # 更新会话的更新时间
            self.update_session(session_id)

            return cursor.lastrowid

    def get_messages(self, session_id: int, limit: int = 100) -> List[Dict]:
        """
        获取会话消息

        Args:
            session_id: 会话 ID
            limit: 限制数量

        Returns:
            消息列表
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM messages
                WHERE session_id = ?
                ORDER BY created_at ASC
                LIMIT ?
            """, (session_id, limit))
            return [dict(row) for row in cursor.fetchall()]

    def get_messages_for_llm(self, session_id: int, limit: int = 20) -> List[Dict]:
        """
        获取用于 LLM 对话的消息格式

        Args:
            session_id: 会话 ID
            limit: 限制数量（最近的 N 条）

        Returns:
            LLM 对话格式的消息列表
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT role, content FROM messages
                WHERE session_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (session_id, limit))

            # 反转顺序，使其按时间正序排列
            rows = cursor.fetchall()
            return [{"role": row["role"], "content": row["content"]} for row in reversed(rows)]

    def clear_messages(self, session_id: int) -> bool:
        """
        清空会话消息

        Args:
            session_id: 会话 ID

        Returns:
            True 表示成功
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM messages WHERE session_id = ?
            """, (session_id,))
            return cursor.rowcount > 0

    def search_sessions(self, keyword: str, limit: int = 20) -> List[Dict]:
        """
        搜索会话

        Args:
            keyword: 关键词
            limit: 限制数量

        Returns:
            匹配的会话列表
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT s.* FROM sessions s
                JOIN messages m ON s.id = m.session_id
                WHERE s.title LIKE ? OR m.content LIKE ?
                ORDER BY s.updated_at DESC
                LIMIT ?
            """, (f"%{keyword}%", f"%{keyword}%", limit))
            return [dict(row) for row in cursor.fetchall()]

    def get_stats(self) -> Dict:
        """
        获取统计信息

        Returns:
            统计信息字典
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 会话总数
            cursor.execute("SELECT COUNT(*) as count FROM sessions")
            session_count = cursor.fetchone()["count"]

            # 消息总数
            cursor.execute("SELECT COUNT(*) as count FROM messages")
            message_count = cursor.fetchone()["count"]

            return {
                "total_sessions": session_count,
                "total_messages": message_count
            }


# 全局数据库实例
_db: Optional[Database] = None


def get_database() -> Database:
    """获取数据库实例"""
    global _db
    if _db is None:
        _db = Database()
    return _db


def init_database(db_path: str = None) -> Database:
    """初始化数据库"""
    global _db
    _db = Database(db_path)
    return _db
