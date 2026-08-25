from pathlib import Path
import sqlite3


class ConversationMemory:
    def __init__(self, max_messages=12):
        self.max_messages = max_messages

        project_root = Path(__file__).resolve().parents[3]

        data_dir = project_root / "data"
        data_dir.mkdir(parents=True, exist_ok=True)

        self.db_path = data_dir / "zyron_memory.db"

        self._create_table()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _create_table(self):
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS conversation_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            connection.commit()

    def add(self, role, content):
        """
        Add a conversation message.

        Normal conversation messages are limited to max_messages.
        Explicit memories are NOT deleted by this limit.
        """

        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO conversation_memory (role, content)
                VALUES (?, ?)
                """,
                (role, content)
            )

            connection.execute(
                """
                DELETE FROM conversation_memory
                WHERE role != 'memory'
                AND id NOT IN (
                    SELECT id
                    FROM conversation_memory
                    WHERE role != 'memory'
                    ORDER BY id DESC
                    LIMIT ?
                )
                """,
                (self.max_messages,)
            )

            connection.commit()

    def remember(self, content):
        """
        Store an explicit user memory.
        """

        self.add("memory", content)

    def get_context(self):
        """
        Return recent conversation history plus saved memories.
        """

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT role, content
                FROM conversation_memory
                ORDER BY id ASC
                """
            ).fetchall()

        if not rows:
            return ""

        lines = []

        for role, content in rows:
            role_name = role.capitalize()
            lines.append(f"{role_name}: {content}")

        return "\n".join(lines)

    def get_memories(self):
        """
        Return only explicitly saved memories.
        """

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, content, created_at
                FROM conversation_memory
                WHERE role = 'memory'
                ORDER BY id ASC
                """
            ).fetchall()

        return rows

    def forget(self, text=None):
        """
        Forget explicit memories.

        If text is None:
            Delete all explicit memories.

        If text is provided:
            Delete memories containing that text.
        """

        with self._connect() as connection:

            if text is None:
                connection.execute(
                    """
                    DELETE FROM conversation_memory
                    WHERE role = 'memory'
                    """
                )

            else:
                connection.execute(
                    """
                    DELETE FROM conversation_memory
                    WHERE role = 'memory'
                    AND LOWER(content) LIKE LOWER(?)
                    """,
                    (f"%{text}%",)
                )

            connection.commit()

    def forget_by_id(self, memory_id):
        """
        Delete exactly one permanent memory by its database ID.

        Returns True if a memory was deleted, otherwise False.
        """

        with self._connect() as connection:

            cursor = connection.execute(
                """
                DELETE FROM conversation_memory
                WHERE id = ?
                AND role = 'memory'
                """,
                (int(memory_id),)
            )

            connection.commit()

            return cursor.rowcount > 0

    def clear(self):
        """
        Clear the entire conversation history.

        This also removes explicit memories.
        """

        with self._connect() as connection:
            connection.execute(
                "DELETE FROM conversation_memory"
            )

            connection.commit()