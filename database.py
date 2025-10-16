import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
import json


class Database:
    """Database manager for content generation service"""

    def __init__(self, db_path: str = "content_generator.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create ideas table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ideas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic TEXT NOT NULL UNIQUE,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                content_generated BOOLEAN DEFAULT FALSE
            )
        """)

        # Create content table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS content (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                idea_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (idea_id) REFERENCES ideas (id)
            )
        """)

        # Create index for faster lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_ideas_topic ON ideas (topic)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_ideas_content_generated
            ON ideas (content_generated)
        """)

        conn.commit()
        conn.close()

    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)

    def add_idea(self, topic: str, description: str = "") -> Optional[int]:
        """
        Add a new idea to the database
        Returns the idea ID if successful, None if duplicate
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO ideas (topic, description) VALUES (?, ?)",
                (topic.strip(), description.strip())
            )
            idea_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return idea_id
        except sqlite3.IntegrityError:
            # Duplicate topic
            return None

    def idea_exists(self, topic: str) -> bool:
        """Check if an idea already exists in the database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM ideas WHERE topic = ?",
            (topic.strip(),)
        )
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0

    def get_pending_ideas(self, limit: Optional[int] = None) -> List[Dict]:
        """Get ideas that haven't had content generated yet"""
        conn = self.get_connection()
        cursor = conn.cursor()

        query = """
            SELECT id, topic, description, created_at
            FROM ideas
            WHERE content_generated = FALSE
            ORDER BY created_at ASC
        """

        if limit:
            query += f" LIMIT {limit}"

        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "id": row[0],
                "topic": row[1],
                "description": row[2],
                "created_at": row[3]
            }
            for row in rows
        ]

    def add_content(self, idea_id: int, title: str, content: str) -> int:
        """Add generated content for an idea"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Insert content
        cursor.execute(
            "INSERT INTO content (idea_id, title, content) VALUES (?, ?, ?)",
            (idea_id, title, content)
        )
        content_id = cursor.lastrowid

        # Mark idea as having content generated
        cursor.execute(
            "UPDATE ideas SET content_generated = TRUE WHERE id = ?",
            (idea_id,)
        )

        conn.commit()
        conn.close()
        return content_id

    def get_all_ideas(self) -> List[Dict]:
        """Get all ideas from the database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, topic, description, created_at, content_generated
            FROM ideas
            ORDER BY created_at DESC
        """)
        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "id": row[0],
                "topic": row[1],
                "description": row[2],
                "created_at": row[3],
                "content_generated": bool(row[4])
            }
            for row in rows
        ]

    def get_content_by_idea(self, idea_id: int) -> Optional[Dict]:
        """Get generated content for a specific idea"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.id, c.title, c.content, c.created_at, i.topic
            FROM content c
            JOIN ideas i ON c.idea_id = i.id
            WHERE c.idea_id = ?
        """, (idea_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                "id": row[0],
                "title": row[1],
                "content": row[2],
                "created_at": row[3],
                "topic": row[4]
            }
        return None

    def get_stats(self) -> Dict:
        """Get database statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM ideas")
        total_ideas = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM ideas WHERE content_generated = TRUE")
        ideas_with_content = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM content")
        total_content = cursor.fetchone()[0]

        conn.close()

        return {
            "total_ideas": total_ideas,
            "ideas_with_content": ideas_with_content,
            "pending_ideas": total_ideas - ideas_with_content,
            "total_content_pieces": total_content
        }
