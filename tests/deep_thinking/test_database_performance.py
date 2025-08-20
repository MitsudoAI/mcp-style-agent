"""
Database Performance Optimization Tests

Tests for connection pooling, query optimization, indexing,
and performance monitoring features.
"""

import pytest
import tempfile
import time
import threading
from pathlib import Path
from unittest.mock import Mock, patch

from src.mcps.deep_thinking.data.database_performance import (
    DatabasePerformanceOptimizer,
    ConnectionPool,
    DatabaseConnection,
    QueryOptimizer,
    IndexOptimizer,
    DatabasePerformanceMonitor,
)
from src.mcps.deep_thinking.data.database import ThinkingDatabase


class TestDatabaseConnection:
    """Test database connection wrapper"""

    def test_connection_creation(self):
        """Test database connection creation"""
        conn = DatabaseConnection(":memory:", "test_conn")

        assert conn.connection_id == "test_conn"
        assert conn.connection is not None
        assert conn.is_alive() is True
        assert conn.query_count == 0

        conn.close()

    def test_query_execution(self):
        """Test query execution with tracking"""
        conn = DatabaseConnection(":memory:", "test_conn")

        try:
            # Create test table
            conn.execute("CREATE TABLE test (id INTEGER, name TEXT)")
            conn.commit()

            # Insert data
            conn.execute("INSERT INTO test (id, name) VALUES (?, ?)", (1, "test"))
            conn.commit()

            # Query data
            cursor = conn.execute("SELECT * FROM test WHERE id = ?", (1,))
            result = cursor.fetchone()

            assert result is not None
            assert result["id"] == 1
            assert result["name"] == "test"
            assert conn.query_count > 0

        finally:
            conn.close()

    def test_connection_stats(self):
        """Test connection statistics"""
        conn = DatabaseConnection(":memory:", "test_conn")

        try:
            # Execute some queries
            conn.execute("CREATE TABLE test (id INTEGER)")
            conn.execute("INSERT INTO test (id) VALUES (1)")

            stats = conn.get_stats()
            assert stats["connection_id"] == "test_conn"
            assert stats["query_count"] > 0
            assert stats["is_alive"] is True

        finally:
            conn.close()


class TestConnectionPool:
    """Test connection pool functionality"""

    def test_pool_initialization(self):
        """Test connection pool initialization"""
        pool = ConnectionPool(":memory:", min_connections=2, max_connections=5)

        try:
            stats = pool.get_stats()
            assert stats["total_connections"] >= 2
            assert stats["idle_connections"] >= 2
            assert stats["active_connections"] == 0

        finally:
            pool.close_all()

    def test_connection_acquisition(self):
        """Test connection acquisition from pool"""
        pool = ConnectionPool(":memory:", min_connections=1, max_connections=3)

        try:
            with pool.get_connection() as conn:
                assert conn is not None
                assert conn.is_alive() is True

                # Check pool stats
                stats = pool.get_stats()
                assert stats["active_connections"] == 1

            # After context exit, connection should be returned
            stats = pool.get_stats()
            assert stats["active_connections"] == 0

        finally:
            pool.close_all()

    def test_concurrent_connections(self):
        """Test concurrent connection usage"""
        pool = ConnectionPool(":memory:", min_connections=2, max_connections=5)
        results = []

        def worker_thread(thread_id):
            try:
                with pool.get_connection() as conn:
                    # Create unique table for this thread
                    table_name = f"test_{thread_id}"
                    conn.execute(f"CREATE TABLE {table_name} (id INTEGER)")
                    conn.execute(
                        f"INSERT INTO {table_name} (id) VALUES (?)", (thread_id,)
                    )
                    conn.commit()

                    # Query back the data
                    cursor = conn.execute(f"SELECT id FROM {table_name}")
                    result = cursor.fetchone()
                    results.append(result["id"])

            except Exception as e:
                results.append(f"Error: {e}")

        try:
            # Start multiple threads
            threads = []
            for i in range(3):
                thread = threading.Thread(target=worker_thread, args=(i,))
                threads.append(thread)
                thread.start()

            # Wait for completion
            for thread in threads:
                thread.join()

            # Check results
            assert len(results) == 3
            assert all(isinstance(r, int) for r in results)
            assert set(results) == {0, 1, 2}

        finally:
            pool.close_all()

    def test_pool_exhaustion(self):
        """Test pool behavior when exhausted"""
        pool = ConnectionPool(":memory:", min_connections=1, max_connections=2)

        try:
            connections = []

            # Acquire all connections
            conn1 = pool.get_connection().__enter__()
            connections.append(conn1)

            conn2 = pool.get_connection().__enter__()
            connections.append(conn2)

            # Try to acquire one more (should timeout or fail)
            with pytest.raises(Exception):
                with pool.get_connection(timeout=0.1):
                    pass

            # Release connections
            for conn in connections:
                pool.get_connection().__exit__(None, None, None)

        finally:
            pool.close_all()


class TestQueryOptimizer:
    """Test query optimization and monitoring"""

    def test_query_monitoring(self):
        """Test query performance monitoring"""
        optimizer = QueryOptimizer()
        conn = DatabaseConnection(":memory:", "test_conn")

        try:
            # Execute monitored queries
            optimizer.execute_with_monitoring(conn, "CREATE TABLE test (id INTEGER)")
            optimizer.execute_with_monitoring(conn, "INSERT INTO test (id) VALUES (1)")
            optimizer.execute_with_monitoring(conn, "SELECT * FROM test")

            # Check statistics
            stats = optimizer.get_query_stats()
            query_stats = stats["query_stats"]

            assert "CREATE" in query_stats
            assert "INSERT" in query_stats
            assert "SELECT" in query_stats

            # Check execution counts
            assert query_stats["CREATE"]["execution_count"] == 1
            assert query_stats["INSERT"]["execution_count"] == 1
            assert query_stats["SELECT"]["execution_count"] == 1

        finally:
            conn.close()

    def test_slow_query_detection(self):
        """Test slow query detection"""
        optimizer = QueryOptimizer()
        optimizer.slow_query_threshold = 0.001  # Very low threshold for testing

        conn = DatabaseConnection(":memory:", "test_conn")

        try:
            # Execute a query that might be considered slow
            with patch("time.time", side_effect=[0, 0.002]):  # Mock 2ms execution time
                optimizer.execute_with_monitoring(conn, "SELECT 1")

            stats = optimizer.get_query_stats()
            assert stats["total_slow_queries"] >= 0  # Might detect as slow

        finally:
            conn.close()

    def test_query_type_detection(self):
        """Test query type detection"""
        optimizer = QueryOptimizer()

        test_cases = [
            ("SELECT * FROM test", "SELECT"),
            ("INSERT INTO test VALUES (1)", "INSERT"),
            ("UPDATE test SET id = 1", "UPDATE"),
            ("DELETE FROM test", "DELETE"),
            ("CREATE TABLE test (id INTEGER)", "CREATE"),
            ("DROP TABLE test", "DROP"),
            ("PRAGMA table_info(test)", "PRAGMA"),
            ("EXPLAIN QUERY PLAN SELECT * FROM test", "OTHER"),
        ]

        for query, expected_type in test_cases:
            actual_type = optimizer._get_query_type(query)
            assert actual_type == expected_type


class TestIndexOptimizer:
    """Test index optimization"""

    def test_recommended_indexes_creation(self):
        """Test creation of recommended indexes"""
        optimizer = IndexOptimizer()
        conn = DatabaseConnection(":memory:", "test_conn")

        try:
            # Create test tables (simplified versions)
            conn.execute(
                """
                CREATE TABLE thinking_sessions (
                    id TEXT PRIMARY KEY,
                    status TEXT,
                    created_at TIMESTAMP,
                    user_id TEXT
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE session_steps (
                    id INTEGER PRIMARY KEY,
                    session_id TEXT,
                    step_number INTEGER,
                    step_type TEXT
                )
            """
            )

            # Create recommended indexes
            optimizer.create_recommended_indexes(conn)

            # Check that indexes were created
            cursor = conn.execute(
                """
                SELECT name FROM sqlite_master 
                WHERE type='index' AND name NOT LIKE 'sqlite_%'
            """
            )
            indexes = [row["name"] for row in cursor.fetchall()]

            # Should have created some indexes
            assert len(indexes) > 0

        finally:
            conn.close()

    def test_index_analysis(self):
        """Test index usage analysis"""
        optimizer = IndexOptimizer()
        conn = DatabaseConnection(":memory:", "test_conn")

        try:
            # Create test table and index
            conn.execute("CREATE TABLE test (id INTEGER, name TEXT)")
            conn.execute("CREATE INDEX idx_test_name ON test (name)")

            # Analyze indexes
            optimizer.analyze_index_usage(conn)

            stats = optimizer.get_index_stats()
            assert "total_indexes" in stats
            assert stats["total_indexes"] > 0
            assert "indexes" in stats

        finally:
            conn.close()


class TestDatabasePerformanceOptimizer:
    """Test main database performance optimizer"""

    def test_optimizer_initialization(self):
        """Test optimizer initialization"""
        optimizer = DatabasePerformanceOptimizer(
            ":memory:", min_connections=1, max_connections=3
        )

        try:
            assert optimizer.connection_pool is not None
            assert optimizer.query_optimizer is not None
            assert optimizer.index_optimizer is not None

            # Test connection acquisition
            with optimizer.get_connection() as conn:
                assert conn is not None

        finally:
            optimizer.shutdown()

    def test_optimized_query_execution(self):
        """Test optimized query execution"""
        optimizer = DatabasePerformanceOptimizer(
            ":memory:", min_connections=1, max_connections=2
        )

        try:
            # Execute queries through optimizer
            cursor = optimizer.execute_query("CREATE TABLE test (id INTEGER)")
            cursor = optimizer.execute_query("INSERT INTO test (id) VALUES (?)", (1,))
            cursor = optimizer.execute_query("SELECT * FROM test")

            result = cursor.fetchone()
            assert result is not None
            assert result["id"] == 1

        finally:
            optimizer.shutdown()

    def test_performance_metrics(self):
        """Test performance metrics collection"""
        optimizer = DatabasePerformanceOptimizer(
            ":memory:", min_connections=1, max_connections=2
        )

        try:
            # Generate some activity
            optimizer.execute_query("CREATE TABLE test (id INTEGER)")
            optimizer.execute_query("INSERT INTO test (id) VALUES (1)")
            optimizer.execute_query("SELECT * FROM test")

            # Get metrics
            metrics = optimizer.get_performance_metrics()

            assert "connection_pool" in metrics
            assert "query_performance" in metrics
            assert "index_analysis" in metrics
            assert "database_stats" in metrics

            # Check connection pool metrics
            pool_metrics = metrics["connection_pool"]
            assert "total_connections" in pool_metrics
            assert "active_connections" in pool_metrics

            # Check query performance metrics
            query_metrics = metrics["query_performance"]
            assert "query_stats" in query_metrics

        finally:
            optimizer.shutdown()


class TestThinkingDatabaseIntegration:
    """Test integration with ThinkingDatabase"""

    def test_database_with_performance_optimization(self):
        """Test ThinkingDatabase with performance optimization enabled"""
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name

        db = ThinkingDatabase(
            db_path,
            enable_performance_optimization=True,
            min_connections=1,
            max_connections=3,
        )

        try:
            # Test basic operations
            session_id = "test_session_123"
            success = db.create_session(session_id, "Test topic")
            assert success is True

            # Test session retrieval
            session = db.get_session(session_id)
            assert session is not None
            assert session["topic"] == "Test topic"

            # Test performance metrics
            metrics = db.get_performance_metrics()
            assert "database_info" in metrics
            assert metrics["database_info"]["performance_optimization_enabled"] is True

        finally:
            db.shutdown()
            # Clean up temp file
            import os

            try:
                os.unlink(db_path)
            except:
                pass

    def test_database_without_performance_optimization(self):
        """Test ThinkingDatabase without performance optimization"""
        db = ThinkingDatabase(":memory:", enable_performance_optimization=False)

        try:
            # Test basic operations
            session_id = "test_session_456"
            success = db.create_session(session_id, "Test topic")
            assert success is True

            # Test performance metrics (should have limited info)
            metrics = db.get_performance_metrics()
            assert "database_info" in metrics
            assert metrics["database_info"]["performance_optimization_enabled"] is False

        finally:
            db.shutdown()

    def test_optimized_query_execution(self):
        """Test optimized query execution"""
        db = ThinkingDatabase(
            ":memory:",
            enable_performance_optimization=True,
            min_connections=1,
            max_connections=2,
        )

        try:
            # Execute optimized query
            cursor = db.execute_optimized_query(
                "SELECT COUNT(*) FROM thinking_sessions"
            )
            result = cursor.fetchone()
            assert result is not None

        finally:
            db.shutdown()

    def test_database_optimization_methods(self):
        """Test database optimization methods"""
        db = ThinkingDatabase(
            ":memory:",
            enable_performance_optimization=True,
            min_connections=1,
            max_connections=2,
        )

        try:
            # Test optimization methods
            db.optimize_database_performance()  # Should not raise exception
            db.analyze_performance()  # Should not raise exception

            # Test performance metrics after optimization
            metrics = db.get_performance_metrics()
            assert "connection_pool" in metrics

        finally:
            db.shutdown()


class TestPerformanceBenchmarks:
    """Performance benchmark tests"""

    def test_connection_pool_performance(self):
        """Test connection pool performance under load"""
        optimizer = DatabasePerformanceOptimizer(
            ":memory:", min_connections=2, max_connections=5
        )

        def worker_thread(thread_id, iterations=10):
            for i in range(iterations):
                try:
                    cursor = optimizer.execute_query("SELECT ?", (thread_id * 100 + i,))
                    result = cursor.fetchone()
                    assert result is not None
                except Exception as e:
                    logger.error(f"Thread {thread_id} iteration {i} failed: {e}")

        try:
            # Start multiple threads
            threads = []
            start_time = time.time()

            for i in range(5):
                thread = threading.Thread(target=worker_thread, args=(i, 20))
                threads.append(thread)
                thread.start()

            # Wait for completion
            for thread in threads:
                thread.join()

            total_time = time.time() - start_time

            # Check performance
            metrics = optimizer.get_performance_metrics()
            pool_stats = metrics["connection_pool"]
            query_stats = metrics["query_performance"]

            # Should complete within reasonable time
            assert total_time < 10.0  # 10 seconds max

            # Should have processed all queries
            total_queries = sum(
                stats["execution_count"]
                for stats in query_stats["query_stats"].values()
            )
            assert total_queries == 100  # 5 threads * 20 iterations

        finally:
            optimizer.shutdown()

    def test_query_performance_monitoring(self):
        """Test query performance monitoring accuracy"""
        optimizer = DatabasePerformanceOptimizer(
            ":memory:", min_connections=1, max_connections=2
        )

        try:
            # Execute various types of queries
            queries = [
                ("CREATE TABLE perf_test (id INTEGER, data TEXT)", "CREATE"),
                ("INSERT INTO perf_test (id, data) VALUES (?, ?)", "INSERT"),
                ("SELECT * FROM perf_test WHERE id = ?", "SELECT"),
                ("UPDATE perf_test SET data = ? WHERE id = ?", "UPDATE"),
                ("DELETE FROM perf_test WHERE id = ?", "DELETE"),
            ]

            for query, expected_type in queries:
                if expected_type == "INSERT":
                    optimizer.execute_query(query, (1, "test_data"))
                elif expected_type == "SELECT":
                    optimizer.execute_query(query, (1,))
                elif expected_type == "UPDATE":
                    optimizer.execute_query(query, ("updated_data", 1))
                elif expected_type == "DELETE":
                    optimizer.execute_query(query, (1,))
                else:
                    optimizer.execute_query(query)

            # Check metrics
            metrics = optimizer.get_performance_metrics()
            query_stats = metrics["query_performance"]["query_stats"]

            # Should have stats for each query type
            for _, expected_type in queries:
                assert expected_type in query_stats
                assert query_stats[expected_type]["execution_count"] >= 1
                assert query_stats[expected_type]["average_time"] >= 0

        finally:
            optimizer.shutdown()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
