"""
Database Performance Optimizer

Implements connection pooling, query optimization, indexing,
and performance monitoring for the SQLite database.
"""

import logging
import sqlite3
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from queue import Queue, Empty
import weakref

logger = logging.getLogger(__name__)


@dataclass
class QueryStats:
    """Query performance statistics"""

    query_type: str
    execution_count: int = 0
    total_time: float = 0.0
    average_time: float = 0.0
    min_time: float = float("inf")
    max_time: float = 0.0
    last_executed: Optional[datetime] = None


@dataclass
class ConnectionStats:
    """Connection pool statistics"""

    total_connections: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    connections_created: int = 0
    connections_closed: int = 0
    connection_errors: int = 0
    average_wait_time: float = 0.0


class DatabaseConnection:
    """Wrapper for database connection with performance tracking"""

    def __init__(self, db_path: str, connection_id: str):
        self.db_path = db_path
        self.connection_id = connection_id
        self.connection = None
        self.created_at = datetime.now()
        self.last_used = datetime.now()
        self.query_count = 0
        self.is_active = False
        self.lock = threading.RLock()

        # Create connection
        self._create_connection()

    def _create_connection(self):
        """Create the actual database connection"""
        try:
            if self.db_path == ":memory:":
                # For in-memory databases, we need to maintain the connection
                self.connection = sqlite3.connect(":memory:", check_same_thread=False)
            else:
                self.connection = sqlite3.connect(self.db_path, check_same_thread=False)

            self.connection.row_factory = sqlite3.Row

            # Optimize connection settings
            self.connection.execute("PRAGMA foreign_keys=ON")
            self.connection.execute("PRAGMA journal_mode=WAL")
            self.connection.execute("PRAGMA synchronous=NORMAL")
            self.connection.execute("PRAGMA cache_size=10000")
            self.connection.execute("PRAGMA temp_store=memory")
            self.connection.execute("PRAGMA mmap_size=268435456")  # 256MB

            logger.debug(f"Created database connection {self.connection_id}")

        except Exception as e:
            logger.error(
                f"Failed to create database connection {self.connection_id}: {e}"
            )
            raise

    def execute(self, query: str, params: Tuple = ()) -> sqlite3.Cursor:
        """Execute a query with performance tracking"""
        with self.lock:
            if not self.connection:
                self._create_connection()

            self.is_active = True
            self.last_used = datetime.now()
            self.query_count += 1

            try:
                cursor = self.connection.execute(query, params)
                return cursor
            finally:
                self.is_active = False

    def executemany(self, query: str, params_list: List[Tuple]) -> sqlite3.Cursor:
        """Execute many queries with performance tracking"""
        with self.lock:
            if not self.connection:
                self._create_connection()

            self.is_active = True
            self.last_used = datetime.now()
            self.query_count += len(params_list)

            try:
                cursor = self.connection.executemany(query, params_list)
                return cursor
            finally:
                self.is_active = False

    def commit(self):
        """Commit transaction"""
        if self.connection:
            self.connection.commit()

    def rollback(self):
        """Rollback transaction"""
        if self.connection:
            self.connection.rollback()

    def close(self):
        """Close the connection"""
        with self.lock:
            if self.connection:
                try:
                    self.connection.close()
                    logger.debug(f"Closed database connection {self.connection_id}")
                except Exception as e:
                    logger.error(f"Error closing connection {self.connection_id}: {e}")
                finally:
                    self.connection = None

    def is_alive(self) -> bool:
        """Check if connection is alive"""
        try:
            if not self.connection:
                return False
            self.connection.execute("SELECT 1")
            return True
        except Exception:
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        return {
            "connection_id": self.connection_id,
            "created_at": self.created_at.isoformat(),
            "last_used": self.last_used.isoformat(),
            "query_count": self.query_count,
            "is_active": self.is_active,
            "is_alive": self.is_alive(),
        }


class ConnectionPool:
    """Database connection pool for improved performance"""

    def __init__(
        self, db_path: str, min_connections: int = 2, max_connections: int = 10
    ):
        self.db_path = db_path
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.connections = Queue(maxsize=max_connections)
        self.all_connections = weakref.WeakSet()
        self.stats = ConnectionStats()
        self.lock = threading.RLock()
        self._connection_counter = 0

        # Initialize minimum connections
        self._initialize_pool()

    def _initialize_pool(self):
        """Initialize the connection pool with minimum connections"""
        for _ in range(self.min_connections):
            conn = self._create_connection()
            self.connections.put(conn)
            self.stats.idle_connections += 1

    def _create_connection(self) -> DatabaseConnection:
        """Create a new database connection"""
        with self.lock:
            self._connection_counter += 1
            connection_id = f"conn_{self._connection_counter}"

            try:
                conn = DatabaseConnection(self.db_path, connection_id)
                self.all_connections.add(conn)
                self.stats.connections_created += 1
                self.stats.total_connections += 1
                return conn
            except Exception as e:
                self.stats.connection_errors += 1
                logger.error(f"Failed to create connection: {e}")
                raise

    @contextmanager
    def get_connection(self, timeout: float = 30.0):
        """Get a connection from the pool"""
        start_time = time.time()
        connection = None

        try:
            # Try to get an existing connection
            try:
                connection = self.connections.get(timeout=timeout)
                wait_time = time.time() - start_time

                with self.lock:
                    self.stats.idle_connections -= 1
                    self.stats.active_connections += 1

                    # Update average wait time
                    if self.stats.connections_created > 0:
                        total_wait = self.stats.average_wait_time * (
                            self.stats.connections_created - 1
                        )
                        self.stats.average_wait_time = (
                            total_wait + wait_time
                        ) / self.stats.connections_created

            except Empty:
                # No connections available, create new one if under limit
                with self.lock:
                    if self.stats.total_connections < self.max_connections:
                        connection = self._create_connection()
                        self.stats.active_connections += 1
                    else:
                        raise Exception(
                            f"Connection pool exhausted (max: {self.max_connections})"
                        )

            # Verify connection is alive
            if not connection.is_alive():
                logger.warning(f"Dead connection detected: {connection.connection_id}")
                connection.close()
                connection = self._create_connection()

            yield connection

        except Exception as e:
            logger.error(f"Error getting database connection: {e}")
            raise
        finally:
            # Return connection to pool
            if connection:
                try:
                    # Check if connection is still alive before returning
                    if connection.is_alive():
                        self.connections.put(connection)
                        with self.lock:
                            self.stats.active_connections -= 1
                            self.stats.idle_connections += 1
                    else:
                        # Connection is dead, close it and create a new one
                        connection.close()
                        with self.lock:
                            self.stats.active_connections -= 1
                            self.stats.total_connections -= 1
                            self.stats.connections_closed += 1

                        # Create replacement connection if below minimum
                        if self.stats.total_connections < self.min_connections:
                            try:
                                new_conn = self._create_connection()
                                self.connections.put(new_conn)
                                self.stats.idle_connections += 1
                            except Exception as e:
                                logger.error(
                                    f"Failed to create replacement connection: {e}"
                                )

                except Exception as e:
                    logger.error(f"Error returning connection to pool: {e}")

    def close_all(self):
        """Close all connections in the pool"""
        with self.lock:
            # Close all connections in queue
            while not self.connections.empty():
                try:
                    conn = self.connections.get_nowait()
                    conn.close()
                    self.stats.connections_closed += 1
                except Empty:
                    break
                except Exception as e:
                    logger.error(f"Error closing pooled connection: {e}")

            # Close any remaining connections
            for conn in list(self.all_connections):
                try:
                    conn.close()
                except Exception as e:
                    logger.error(f"Error closing connection: {e}")

            # Reset stats
            self.stats.total_connections = 0
            self.stats.active_connections = 0
            self.stats.idle_connections = 0

    def get_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        with self.lock:
            return {
                "total_connections": self.stats.total_connections,
                "active_connections": self.stats.active_connections,
                "idle_connections": self.stats.idle_connections,
                "connections_created": self.stats.connections_created,
                "connections_closed": self.stats.connections_closed,
                "connection_errors": self.stats.connection_errors,
                "average_wait_time": self.stats.average_wait_time,
                "pool_utilization": self.stats.active_connections
                / max(self.stats.total_connections, 1),
                "min_connections": self.min_connections,
                "max_connections": self.max_connections,
            }


class QueryOptimizer:
    """Query optimization and performance monitoring"""

    def __init__(self):
        self.query_stats = {}
        self.slow_query_threshold = 1.0  # 1 second
        self.slow_queries = []
        self.lock = threading.RLock()

    def execute_with_monitoring(
        self, connection: DatabaseConnection, query: str, params: Tuple = ()
    ) -> sqlite3.Cursor:
        """Execute query with performance monitoring"""
        start_time = time.time()
        query_type = self._get_query_type(query)

        try:
            cursor = connection.execute(query, params)
            execution_time = time.time() - start_time

            # Update statistics
            self._update_query_stats(query_type, execution_time)

            # Check for slow queries
            if execution_time > self.slow_query_threshold:
                self._record_slow_query(query, params, execution_time)

            return cursor

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                f"Query failed after {execution_time:.3f}s: {query[:100]}... Error: {e}"
            )
            raise

    def _get_query_type(self, query: str) -> str:
        """Determine query type from SQL"""
        query_upper = query.strip().upper()
        if query_upper.startswith("SELECT"):
            return "SELECT"
        elif query_upper.startswith("INSERT"):
            return "INSERT"
        elif query_upper.startswith("UPDATE"):
            return "UPDATE"
        elif query_upper.startswith("DELETE"):
            return "DELETE"
        elif query_upper.startswith("CREATE"):
            return "CREATE"
        elif query_upper.startswith("DROP"):
            return "DROP"
        elif query_upper.startswith("PRAGMA"):
            return "PRAGMA"
        else:
            return "OTHER"

    def _update_query_stats(self, query_type: str, execution_time: float):
        """Update query statistics"""
        with self.lock:
            if query_type not in self.query_stats:
                self.query_stats[query_type] = QueryStats(query_type)

            stats = self.query_stats[query_type]
            stats.execution_count += 1
            stats.total_time += execution_time
            stats.average_time = stats.total_time / stats.execution_count
            stats.min_time = min(stats.min_time, execution_time)
            stats.max_time = max(stats.max_time, execution_time)
            stats.last_executed = datetime.now()

    def _record_slow_query(self, query: str, params: Tuple, execution_time: float):
        """Record slow query for analysis"""
        with self.lock:
            slow_query = {
                "query": query[:500],  # Truncate long queries
                "params": str(params)[:200],  # Truncate long params
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat(),
            }

            self.slow_queries.append(slow_query)

            # Keep only recent slow queries (last 100)
            if len(self.slow_queries) > 100:
                self.slow_queries = self.slow_queries[-100:]

            logger.warning(
                f"Slow query detected ({execution_time:.3f}s): {query[:100]}..."
            )

    def get_query_stats(self) -> Dict[str, Any]:
        """Get query performance statistics"""
        with self.lock:
            stats = {}
            for query_type, query_stats in self.query_stats.items():
                stats[query_type] = {
                    "execution_count": query_stats.execution_count,
                    "total_time": query_stats.total_time,
                    "average_time": query_stats.average_time,
                    "min_time": (
                        query_stats.min_time
                        if query_stats.min_time != float("inf")
                        else 0
                    ),
                    "max_time": query_stats.max_time,
                    "last_executed": (
                        query_stats.last_executed.isoformat()
                        if query_stats.last_executed
                        else None
                    ),
                }

            return {
                "query_stats": stats,
                "slow_queries": self.slow_queries[-10:],  # Last 10 slow queries
                "slow_query_threshold": self.slow_query_threshold,
                "total_slow_queries": len(self.slow_queries),
            }

    def reset_stats(self):
        """Reset all query statistics"""
        with self.lock:
            self.query_stats.clear()
            self.slow_queries.clear()


class DatabasePerformanceOptimizer:
    """Main database performance optimizer"""

    def __init__(
        self, db_path: str, min_connections: int = 2, max_connections: int = 10
    ):
        self.db_path = db_path
        self.connection_pool = ConnectionPool(db_path, min_connections, max_connections)
        self.query_optimizer = QueryOptimizer()
        self.index_optimizer = IndexOptimizer()
        self.performance_monitor = DatabasePerformanceMonitor()

        # Initialize optimizations
        self._initialize_optimizations()

    def _initialize_optimizations(self):
        """Initialize database optimizations"""
        try:
            # Note: Indexes and analysis will be done after tables are created
            # This is called from the database initialization
            logger.info("Database performance optimizer ready")
        except Exception as e:
            logger.error(f"Failed to initialize database optimizations: {e}")

    def initialize_after_tables_created(self):
        """Initialize optimizations after database tables are created"""
        try:
            with self.get_connection() as conn:
                # Create recommended indexes
                self.index_optimizer.create_recommended_indexes(conn)

                # Analyze database for optimization opportunities
                self.analyze_database_performance()

            logger.info(
                "Database performance optimizations initialized after table creation"
            )
        except Exception as e:
            logger.error(
                f"Failed to initialize database optimizations after table creation: {e}"
            )

    @contextmanager
    def get_connection(self, timeout: float = 30.0):
        """Get optimized database connection"""
        with self.connection_pool.get_connection(timeout) as conn:
            yield conn

    def execute_query(self, query: str, params: Tuple = ()) -> sqlite3.Cursor:
        """Execute query with full optimization"""
        with self.get_connection() as conn:
            return self.query_optimizer.execute_with_monitoring(conn, query, params)

    def analyze_database_performance(self):
        """Analyze database performance and suggest optimizations"""
        try:
            with self.get_connection() as conn:
                # Analyze table statistics
                self.performance_monitor.analyze_table_stats(conn)

                # Check index usage
                self.index_optimizer.analyze_index_usage(conn)

                # Check for missing indexes
                missing_indexes = self.index_optimizer.suggest_missing_indexes(conn)
                if missing_indexes:
                    logger.info(f"Suggested missing indexes: {missing_indexes}")

        except Exception as e:
            logger.error(f"Error analyzing database performance: {e}")

    def optimize_database(self):
        """Run comprehensive database optimization"""
        try:
            with self.get_connection() as conn:
                # Vacuum database
                logger.info("Running VACUUM to optimize database...")
                conn.execute("VACUUM")

                # Analyze tables for query planner
                logger.info("Running ANALYZE to update statistics...")
                conn.execute("ANALYZE")

                # Optimize WAL checkpoint
                conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")

                conn.commit()

            logger.info("Database optimization completed")
        except Exception as e:
            logger.error(f"Error optimizing database: {e}")

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics"""
        return {
            "connection_pool": self.connection_pool.get_stats(),
            "query_performance": self.query_optimizer.get_query_stats(),
            "index_analysis": self.index_optimizer.get_index_stats(),
            "database_stats": self.performance_monitor.get_database_stats(),
        }

    def shutdown(self):
        """Shutdown the performance optimizer"""
        try:
            self.connection_pool.close_all()
            logger.info("Database performance optimizer shutdown complete")
        except Exception as e:
            logger.error(f"Error during database optimizer shutdown: {e}")


class IndexOptimizer:
    """Database index optimization"""

    def __init__(self):
        self.index_stats = {}
        self.recommended_indexes = [
            # Session indexes
            ("idx_sessions_status", "thinking_sessions", ["status"]),
            ("idx_sessions_created", "thinking_sessions", ["created_at"]),
            ("idx_sessions_user_status", "thinking_sessions", ["user_id", "status"]),
            # Step indexes
            ("idx_steps_session", "session_steps", ["session_id"]),
            (
                "idx_steps_session_number",
                "session_steps",
                ["session_id", "step_number"],
            ),
            ("idx_steps_type", "session_steps", ["step_type"]),
            # Result indexes
            ("idx_results_session", "step_results", ["session_id"]),
            ("idx_results_step", "step_results", ["step_id"]),
            ("idx_results_type", "step_results", ["result_type"]),
            # Evidence indexes
            ("idx_evidence_session", "evidence_sources", ["session_id"]),
            ("idx_evidence_credibility", "evidence_sources", ["credibility_score"]),
        ]

    def create_recommended_indexes(self, connection: DatabaseConnection):
        """Create recommended indexes for performance"""
        for index_name, table_name, columns in self.recommended_indexes:
            try:
                # Check if index already exists
                cursor = connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='index' AND name=?",
                    (index_name,),
                )
                if cursor.fetchone():
                    continue  # Index already exists

                # Create index
                columns_str = ", ".join(columns)
                create_sql = f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name} ({columns_str})"
                connection.execute(create_sql)

                logger.debug(f"Created index: {index_name}")

            except Exception as e:
                logger.error(f"Failed to create index {index_name}: {e}")

    def analyze_index_usage(self, connection: DatabaseConnection):
        """Analyze index usage statistics"""
        try:
            # Get index usage stats (SQLite doesn't have detailed stats, so we check existence)
            cursor = connection.execute(
                """
                SELECT name, tbl_name, sql 
                FROM sqlite_master 
                WHERE type='index' AND name NOT LIKE 'sqlite_%'
            """
            )

            indexes = cursor.fetchall()
            self.index_stats = {
                "total_indexes": len(indexes),
                "indexes": [
                    {"name": row["name"], "table": row["tbl_name"], "sql": row["sql"]}
                    for row in indexes
                ],
            }

        except Exception as e:
            logger.error(f"Error analyzing index usage: {e}")

    def suggest_missing_indexes(self, connection: DatabaseConnection) -> List[str]:
        """Suggest missing indexes based on query patterns"""
        missing_indexes = []

        try:
            # Check which recommended indexes are missing
            cursor = connection.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'"
            )
            existing_indexes = {row["name"] for row in cursor.fetchall()}

            for index_name, table_name, columns in self.recommended_indexes:
                if index_name not in existing_indexes:
                    missing_indexes.append(
                        f"{index_name} ON {table_name}({', '.join(columns)})"
                    )

        except Exception as e:
            logger.error(f"Error suggesting missing indexes: {e}")

        return missing_indexes

    def get_index_stats(self) -> Dict[str, Any]:
        """Get index statistics"""
        return self.index_stats


class DatabasePerformanceMonitor:
    """Database performance monitoring"""

    def __init__(self):
        self.database_stats = {}

    def analyze_table_stats(self, connection: DatabaseConnection):
        """Analyze table statistics"""
        try:
            tables = [
                "thinking_sessions",
                "session_steps",
                "step_results",
                "evidence_sources",
            ]
            table_stats = {}

            for table in tables:
                # Get row count
                cursor = connection.execute(f"SELECT COUNT(*) FROM {table}")
                row_count = cursor.fetchone()[0]

                # Get table info
                cursor = connection.execute(f"PRAGMA table_info({table})")
                columns = cursor.fetchall()

                table_stats[table] = {
                    "row_count": row_count,
                    "column_count": len(columns),
                    "columns": [col["name"] for col in columns],
                }

            self.database_stats["table_stats"] = table_stats

        except Exception as e:
            logger.error(f"Error analyzing table stats: {e}")

    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        return self.database_stats
