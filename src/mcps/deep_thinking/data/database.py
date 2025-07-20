"""
SQLite database implementation for local session storage
Zero-cost local storage with encryption support
"""

import json
import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)


class DatabaseEncryption:
    """Handle local data encryption for privacy protection"""

    def __init__(self, key: Optional[bytes] = None):
        if key is None:
            # Generate a new key for this session
            key = Fernet.generate_key()
        self.cipher = Fernet(key)
        self._key = key

    @property
    def key(self) -> bytes:
        """Get the encryption key"""
        return self._key

    def encrypt(self, data: str) -> str:
        """Encrypt string data"""
        if not data:
            return data
        return self.cipher.encrypt(data.encode()).decode()

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt string data"""
        if not encrypted_data:
            return encrypted_data
        return self.cipher.decrypt(encrypted_data.encode()).decode()

    def encrypt_json(self, data: Dict[str, Any]) -> str:
        """Encrypt JSON data"""
        json_str = json.dumps(data, default=str)
        return self.encrypt(json_str)

    def decrypt_json(self, encrypted_data: str) -> Dict[str, Any]:
        """Decrypt JSON data"""
        json_str = self.decrypt(encrypted_data)
        return json.loads(json_str) if json_str else {}


class ThinkingDatabase:
    """
    Lightweight SQLite database for local session storage
    Implements zero-cost local persistence with encryption
    """

    def __init__(
        self,
        db_path: str = "thinking_sessions.db",
        encryption_key: Optional[bytes] = None,
    ):
        self.db_path = Path(db_path) if db_path != ":memory:" else db_path
        self.encryption = DatabaseEncryption(encryption_key) if encryption_key else None
        self._memory_conn = None  # For persistent in-memory connections
        self._init_database()

    def _init_database(self):
        """Initialize database with required tables"""
        try:
            with self.get_connection() as conn:
                # Enable WAL mode for better concurrent performance (skip for memory db)
                if self.db_path != ":memory:":
                    conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA synchronous=NORMAL")
                conn.execute("PRAGMA cache_size=10000")
                conn.execute("PRAGMA temp_store=memory")

                # Create tables
                self._create_tables(conn)
                logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    def _create_tables(self, conn: sqlite3.Connection):
        """Create database tables"""

        try:
            # Main thinking sessions table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS thinking_sessions (
                    id TEXT PRIMARY KEY,
                    user_id TEXT,
                    topic TEXT NOT NULL,
                    topic_encrypted TEXT,
                    session_type TEXT DEFAULT 'comprehensive_analysis',
                    current_step TEXT DEFAULT '',
                    step_number INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'active',
                    flow_type TEXT DEFAULT 'comprehensive_analysis',
                    configuration TEXT,  -- JSON
                    context TEXT,        -- JSON (encrypted if encryption enabled)
                    quality_metrics TEXT, -- JSON
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP NULL
                )
            """
            )
            logger.info("Created thinking_sessions table")

            # Session steps tracking
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS session_steps (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    step_name TEXT NOT NULL,
                    step_number INTEGER NOT NULL,
                    step_type TEXT NOT NULL,
                    template_used TEXT,
                    input_data TEXT,      -- JSON (encrypted)
                    output_data TEXT,     -- JSON (encrypted)
                    quality_score REAL,
                    execution_time_ms INTEGER,
                    status TEXT DEFAULT 'completed',
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES thinking_sessions (id) ON DELETE CASCADE
                )
            """
            )

            # Step results storage
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS step_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    step_id INTEGER NOT NULL,
                    result_type TEXT NOT NULL,  -- 'input', 'output', 'analysis', 'evidence'
                    content TEXT NOT NULL,      -- Encrypted content
                    metadata TEXT,              -- JSON metadata
                    quality_indicators TEXT,    -- JSON quality metrics
                    citations TEXT,             -- JSON citation data
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES thinking_sessions (id) ON DELETE CASCADE,
                    FOREIGN KEY (step_id) REFERENCES session_steps (id) ON DELETE CASCADE
                )
            """
            )

            # Evidence sources tracking
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS evidence_sources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    step_id INTEGER,
                    url TEXT,
                    title TEXT,
                    summary TEXT,           -- Encrypted
                    credibility_score REAL DEFAULT 0.0,
                    source_type TEXT,
                    publication_date TEXT,
                    key_claims TEXT,        -- JSON (encrypted)
                    citation_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES thinking_sessions (id) ON DELETE CASCADE,
                    FOREIGN KEY (step_id) REFERENCES session_steps (id) ON DELETE SET NULL
                )
            """
            )

            # Create indexes for performance
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_sessions_status ON thinking_sessions (status)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_sessions_created ON thinking_sessions (created_at)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_steps_session ON session_steps (session_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_steps_number ON session_steps (session_id, step_number)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_results_session ON step_results (session_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_evidence_session ON evidence_sources (session_id)"
            )

            conn.commit()
            logger.info("All database tables created successfully")

        except Exception as e:
            logger.error(f"Error creating database tables: {e}")
            raise

    @contextmanager
    def get_connection(self):
        """Get database connection with proper cleanup"""
        if self.db_path == ":memory:":
            # For in-memory databases, maintain a persistent connection
            if self._memory_conn is None:
                self._memory_conn = sqlite3.connect(":memory:")
                self._memory_conn.row_factory = sqlite3.Row
            yield self._memory_conn
        else:
            # For file databases, create new connections
            db_path = (
                self.db_path if isinstance(self.db_path, str) else str(self.db_path)
            )
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            try:
                yield conn
            finally:
                conn.close()

    def _encrypt_if_enabled(self, data: str) -> str:
        """Encrypt data if encryption is enabled"""
        if self.encryption and data:
            return self.encryption.encrypt(data)
        return data

    def _decrypt_if_enabled(self, data: str) -> str:
        """Decrypt data if encryption is enabled"""
        if self.encryption and data:
            return self.encryption.decrypt(data)
        return data

    def _encrypt_json_if_enabled(self, data: Dict[str, Any]) -> str:
        """Encrypt JSON data if encryption is enabled"""
        if self.encryption:
            return self.encryption.encrypt_json(data)
        return json.dumps(data, default=str)

    def _decrypt_json_if_enabled(self, data: str) -> Dict[str, Any]:
        """Decrypt JSON data if encryption is enabled"""
        if not data:
            return {}
        if self.encryption:
            return self.encryption.decrypt_json(data)
        return json.loads(data)

    def create_session(
        self,
        session_id: str,
        topic: str,
        session_type: str = "comprehensive_analysis",
        user_id: Optional[str] = None,
        configuration: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Create a new thinking session"""
        try:
            with self.get_connection() as conn:
                # Encrypt sensitive data
                topic_encrypted = (
                    self._encrypt_if_enabled(topic) if self.encryption else None
                )
                config_json = self._encrypt_json_if_enabled(configuration or {})

                conn.execute(
                    """
                    INSERT INTO thinking_sessions 
                    (id, user_id, topic, topic_encrypted, session_type, configuration, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        session_id,
                        user_id,
                        (
                            topic if not self.encryption else ""
                        ),  # Store empty if encrypted
                        topic_encrypted,
                        session_type,
                        config_json,
                        datetime.now().isoformat(),
                        datetime.now().isoformat(),
                    ),
                )
                conn.commit()
                logger.info(f"Created session {session_id} for topic: {topic[:50]}...")
                return True
        except sqlite3.IntegrityError as e:
            logger.error(f"Session {session_id} already exists: {e}")
            return False
        except Exception as e:
            logger.error(f"Error creating session {session_id}: {e}")
            return False

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session information"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    """
                    SELECT * FROM thinking_sessions WHERE id = ?
                """,
                    (session_id,),
                )
                row = cursor.fetchone()

                if not row:
                    return None

                session_data = dict(row)

                # Decrypt sensitive data
                if self.encryption and session_data.get("topic_encrypted"):
                    session_data["topic"] = self._decrypt_if_enabled(
                        session_data["topic_encrypted"]
                    )

                if session_data.get("configuration"):
                    session_data["configuration"] = self._decrypt_json_if_enabled(
                        session_data["configuration"]
                    )

                if session_data.get("context"):
                    session_data["context"] = self._decrypt_json_if_enabled(
                        session_data["context"]
                    )

                if session_data.get("quality_metrics"):
                    session_data["quality_metrics"] = self._decrypt_json_if_enabled(
                        session_data["quality_metrics"]
                    )

                return session_data

        except Exception as e:
            logger.error(f"Error retrieving session {session_id}: {e}")
            return None

    def update_session(self, session_id: str, **updates) -> bool:
        """Update session information"""
        try:
            if not updates:
                return True

            # Prepare update fields
            set_clauses = []
            values = []

            for key, value in updates.items():
                if key in [
                    "context",
                    "quality_metrics",
                    "configuration",
                ] and isinstance(value, dict):
                    set_clauses.append(f"{key} = ?")
                    values.append(self._encrypt_json_if_enabled(value))
                elif key == "topic" and self.encryption:
                    set_clauses.append("topic_encrypted = ?")
                    values.append(self._encrypt_if_enabled(value))
                    set_clauses.append("topic = ?")
                    values.append("")  # Clear unencrypted topic
                else:
                    set_clauses.append(f"{key} = ?")
                    values.append(value)

            # Always update timestamp
            set_clauses.append("updated_at = ?")
            values.append(datetime.now().isoformat())
            values.append(session_id)

            with self.get_connection() as conn:
                query = f"UPDATE thinking_sessions SET {', '.join(set_clauses)} WHERE id = ?"
                conn.execute(query, values)
                conn.commit()

                return conn.total_changes > 0

        except Exception as e:
            logger.error(f"Error updating session {session_id}: {e}")
            return False

    def add_session_step(
        self,
        session_id: str,
        step_name: str,
        step_number: int,
        step_type: str,
        template_used: Optional[str] = None,
        input_data: Optional[Dict[str, Any]] = None,
        output_data: Optional[Dict[str, Any]] = None,
        quality_score: Optional[float] = None,
        execution_time_ms: Optional[int] = None,
    ) -> Optional[int]:
        """Add a step to the session"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO session_steps 
                    (session_id, step_name, step_number, step_type, template_used, 
                     input_data, output_data, quality_score, execution_time_ms)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        session_id,
                        step_name,
                        step_number,
                        step_type,
                        template_used,
                        self._encrypt_json_if_enabled(input_data or {}),
                        self._encrypt_json_if_enabled(output_data or {}),
                        quality_score,
                        execution_time_ms,
                    ),
                )
                conn.commit()
                step_id = cursor.lastrowid
                logger.info(f"Added step {step_name} to session {session_id}")
                return step_id

        except Exception as e:
            logger.error(f"Error adding step to session {session_id}: {e}")
            return None

    def get_session_steps(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all steps for a session"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    """
                    SELECT * FROM session_steps 
                    WHERE session_id = ? 
                    ORDER BY step_number ASC
                """,
                    (session_id,),
                )

                steps = []
                for row in cursor.fetchall():
                    step_data = dict(row)

                    # Decrypt data
                    if step_data.get("input_data"):
                        step_data["input_data"] = self._decrypt_json_if_enabled(
                            step_data["input_data"]
                        )
                    if step_data.get("output_data"):
                        step_data["output_data"] = self._decrypt_json_if_enabled(
                            step_data["output_data"]
                        )

                    steps.append(step_data)

                return steps

        except Exception as e:
            logger.error(f"Error retrieving steps for session {session_id}: {e}")
            return []

    def add_step_result(
        self,
        session_id: str,
        step_id: int,
        result_type: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        quality_indicators: Optional[Dict[str, Any]] = None,
        citations: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[int]:
        """Add a result to a step"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO step_results 
                    (session_id, step_id, result_type, content, metadata, quality_indicators, citations)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        session_id,
                        step_id,
                        result_type,
                        self._encrypt_if_enabled(content),
                        json.dumps(metadata or {}, default=str),
                        json.dumps(quality_indicators or {}, default=str),
                        json.dumps(citations or [], default=str),
                    ),
                )
                conn.commit()
                result_id = cursor.lastrowid
                logger.info(f"Added {result_type} result to step {step_id}")
                return result_id

        except Exception as e:
            logger.error(f"Error adding result to step {step_id}: {e}")
            return None

    def get_step_results(
        self, session_id: str, step_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get results for a step or all steps in session"""
        try:
            with self.get_connection() as conn:
                if step_id:
                    cursor = conn.execute(
                        """
                        SELECT * FROM step_results 
                        WHERE session_id = ? AND step_id = ?
                        ORDER BY created_at ASC
                    """,
                        (session_id, step_id),
                    )
                else:
                    cursor = conn.execute(
                        """
                        SELECT * FROM step_results 
                        WHERE session_id = ?
                        ORDER BY step_id ASC, created_at ASC
                    """,
                        (session_id,),
                    )

                results = []
                for row in cursor.fetchall():
                    result_data = dict(row)

                    # Decrypt content
                    if result_data.get("content"):
                        result_data["content"] = self._decrypt_if_enabled(
                            result_data["content"]
                        )

                    # Parse JSON fields
                    for field in ["metadata", "quality_indicators", "citations"]:
                        if result_data.get(field):
                            result_data[field] = json.loads(result_data[field])

                    results.append(result_data)

                return results

        except Exception as e:
            logger.error(f"Error retrieving results for session {session_id}: {e}")
            return []

    def list_sessions(
        self,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List sessions with optional filtering"""
        try:
            with self.get_connection() as conn:
                query = "SELECT * FROM thinking_sessions WHERE 1=1"
                params = []

                if user_id:
                    query += " AND user_id = ?"
                    params.append(user_id)

                if status:
                    query += " AND status = ?"
                    params.append(status)

                query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
                params.extend([limit, offset])

                cursor = conn.execute(query, params)
                sessions = []

                for row in cursor.fetchall():
                    session_data = dict(row)

                    # Decrypt topic if encrypted
                    if self.encryption and session_data.get("topic_encrypted"):
                        session_data["topic"] = self._decrypt_if_enabled(
                            session_data["topic_encrypted"]
                        )

                    # Don't include full configuration in list view
                    session_data.pop("configuration", None)
                    session_data.pop("context", None)

                    sessions.append(session_data)

                return sessions

        except Exception as e:
            logger.error(f"Error listing sessions: {e}")
            return []

    def delete_session(self, session_id: str) -> bool:
        """Delete a session and all related data"""
        try:
            with self.get_connection() as conn:
                # Foreign key constraints will handle cascading deletes
                cursor = conn.execute(
                    "DELETE FROM thinking_sessions WHERE id = ?", (session_id,)
                )
                conn.commit()

                deleted = cursor.rowcount > 0
                if deleted:
                    logger.info(f"Deleted session {session_id}")
                return deleted

        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {e}")
            return False

    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            with self.get_connection() as conn:
                stats = {}

                # Count sessions by status
                cursor = conn.execute(
                    """
                    SELECT status, COUNT(*) as count 
                    FROM thinking_sessions 
                    GROUP BY status
                """
                )
                stats["sessions_by_status"] = dict(cursor.fetchall())

                # Total steps
                cursor = conn.execute("SELECT COUNT(*) FROM session_steps")
                stats["total_steps"] = cursor.fetchone()[0]

                # Total results
                cursor = conn.execute("SELECT COUNT(*) FROM step_results")
                stats["total_results"] = cursor.fetchone()[0]

                # Database size
                stats["db_size_bytes"] = (
                    self.db_path.stat().st_size if self.db_path.exists() else 0
                )

                # Encryption status
                stats["encryption_enabled"] = self.encryption is not None

                return stats

        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {}

    def cleanup_old_sessions(self, days_old: int = 30) -> int:
        """Clean up old completed sessions"""
        try:
            with self.get_connection() as conn:
                cutoff_date = datetime.now().replace(day=datetime.now().day - days_old)

                cursor = conn.execute(
                    """
                    DELETE FROM thinking_sessions 
                    WHERE status = 'completed' 
                    AND completed_at < ?
                """,
                    (cutoff_date.isoformat(),),
                )

                conn.commit()
                deleted_count = cursor.rowcount

                if deleted_count > 0:
                    logger.info(f"Cleaned up {deleted_count} old sessions")

                return deleted_count

        except Exception as e:
            logger.error(f"Error cleaning up old sessions: {e}")
            return 0
