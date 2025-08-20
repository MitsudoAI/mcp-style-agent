"""
Tests for the SQLite database implementation
"""

import os
import tempfile

import pytest

from src.mcps.deep_thinking.data.database import DatabaseEncryption, ThinkingDatabase
from src.mcps.deep_thinking.sessions.session_manager import SessionManager


class TestDatabaseEncryption:
    """Test database encryption functionality"""

    def test_encryption_basic(self):
        """Test basic encryption/decryption"""
        encryption = DatabaseEncryption()

        original_text = "This is sensitive thinking data"
        encrypted = encryption.encrypt(original_text)
        decrypted = encryption.decrypt(encrypted)

        assert encrypted != original_text
        assert decrypted == original_text

    def test_encryption_json(self):
        """Test JSON encryption/decryption"""
        encryption = DatabaseEncryption()

        original_data = {
            "topic": "How to improve education",
            "thoughts": ["idea 1", "idea 2"],
            "quality_score": 0.85,
        }

        encrypted = encryption.encrypt_json(original_data)
        decrypted = encryption.decrypt_json(encrypted)

        assert decrypted == original_data

    def test_empty_data_handling(self):
        """Test handling of empty data"""
        encryption = DatabaseEncryption()

        assert encryption.encrypt("") == ""
        assert encryption.decrypt("") == ""
        assert encryption.decrypt_json("") == {}


class TestThinkingDatabase:
    """Test the SQLite database implementation"""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        db = ThinkingDatabase(db_path)
        yield db

        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)

    @pytest.fixture
    def encrypted_db(self):
        """Create a temporary encrypted database for testing"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        from cryptography.fernet import Fernet

        key = Fernet.generate_key()
        db = ThinkingDatabase(db_path, key)
        yield db

        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)

    def test_create_session(self, temp_db):
        """Test session creation"""
        session_id = "test-session-123"
        topic = "How to improve critical thinking"

        success = temp_db.create_session(session_id, topic)
        assert success

        # Test duplicate creation fails
        success = temp_db.create_session(session_id, topic)
        assert not success

    def test_get_session(self, temp_db):
        """Test session retrieval"""
        session_id = "test-session-456"
        topic = "Deep learning fundamentals"
        config = {"complexity": "moderate", "flow_type": "comprehensive"}

        temp_db.create_session(session_id, topic, configuration=config)

        session = temp_db.get_session(session_id)
        assert session is not None
        assert session["id"] == session_id
        assert session["topic"] == topic
        assert session["configuration"]["complexity"] == "moderate"

    def test_update_session(self, temp_db):
        """Test session updates"""
        session_id = "test-session-789"
        topic = "Machine learning ethics"

        temp_db.create_session(session_id, topic)

        # Update session
        success = temp_db.update_session(
            session_id,
            current_step="evidence_collection",
            step_number=2,
            status="active",
            context={"progress": "50%"},
        )
        assert success

        # Verify update
        session = temp_db.get_session(session_id)
        assert session["current_step"] == "evidence_collection"
        assert session["step_number"] == 2
        assert session["context"]["progress"] == "50%"

    def test_session_steps(self, temp_db):
        """Test session step management"""
        session_id = "test-session-steps"
        topic = "AI safety considerations"

        temp_db.create_session(session_id, topic)

        # Add steps
        step1_id = temp_db.add_session_step(
            session_id,
            "decompose_problem",
            1,
            "analysis",
            input_data={"topic": topic},
            output_data={"sub_questions": ["q1", "q2"]},
            quality_score=0.8,
        )
        assert step1_id is not None

        step2_id = temp_db.add_session_step(
            session_id, "collect_evidence", 2, "research", quality_score=0.9
        )
        assert step2_id is not None

        # Get steps
        steps = temp_db.get_session_steps(session_id)
        assert len(steps) == 2
        assert steps[0]["step_name"] == "decompose_problem"
        assert steps[1]["step_name"] == "collect_evidence"
        assert steps[0]["quality_score"] == 0.8

    def test_step_results(self, temp_db):
        """Test step result management"""
        session_id = "test-session-results"
        topic = "Climate change solutions"

        temp_db.create_session(session_id, topic)
        step_id = temp_db.add_session_step(session_id, "analysis", 1, "analysis")

        # Add results
        result_id = temp_db.add_step_result(
            session_id,
            step_id,
            "output",
            "Detailed analysis of climate solutions",
            metadata={"word_count": 500},
            quality_indicators={"clarity": 0.9, "depth": 0.8},
            citations=[{"url": "example.com", "title": "Climate Study"}],
        )
        assert result_id is not None

        # Get results
        results = temp_db.get_step_results(session_id, step_id)
        assert len(results) == 1
        assert results[0]["result_type"] == "output"
        assert results[0]["metadata"]["word_count"] == 500
        assert results[0]["quality_indicators"]["clarity"] == 0.9

    def test_list_sessions(self, temp_db):
        """Test session listing"""
        # Create multiple sessions
        for i in range(5):
            temp_db.create_session(f"session-{i}", f"Topic {i}", user_id="user1")

        # Create session for different user
        temp_db.create_session("session-other", "Other topic", user_id="user2")

        # List all sessions
        all_sessions = temp_db.list_sessions()
        assert len(all_sessions) == 6

        # List sessions for specific user
        user1_sessions = temp_db.list_sessions(user_id="user1")
        assert len(user1_sessions) == 5

        # Test pagination
        limited_sessions = temp_db.list_sessions(limit=3)
        assert len(limited_sessions) == 3

    def test_delete_session(self, temp_db):
        """Test session deletion"""
        session_id = "test-delete-session"
        topic = "Test deletion"

        temp_db.create_session(session_id, topic)
        step_id = temp_db.add_session_step(session_id, "test_step", 1, "test")
        temp_db.add_step_result(session_id, step_id, "output", "test result")

        # Verify session exists
        assert temp_db.get_session(session_id) is not None

        # Delete session
        success = temp_db.delete_session(session_id)
        assert success

        # Verify session is gone
        assert temp_db.get_session(session_id) is None

        # Verify related data is also deleted (cascade)
        steps = temp_db.get_session_steps(session_id)
        assert len(steps) == 0

    def test_database_stats(self, temp_db):
        """Test database statistics"""
        # Create some test data
        temp_db.create_session("stats-test-1", "Topic 1")
        temp_db.create_session("stats-test-2", "Topic 2")
        temp_db.update_session("stats-test-1", status="completed")

        stats = temp_db.get_database_stats()

        assert "sessions_by_status" in stats
        assert "total_steps" in stats
        assert "total_results" in stats
        assert "db_size_bytes" in stats
        assert stats["sessions_by_status"]["active"] >= 1
        assert stats["sessions_by_status"]["completed"] >= 1

    def test_encrypted_storage(self, encrypted_db):
        """Test encrypted data storage"""
        session_id = "encrypted-session"
        topic = "Sensitive thinking topic"

        encrypted_db.create_session(session_id, topic)

        # Retrieve and verify
        session = encrypted_db.get_session(session_id)
        assert session["topic"] == topic  # Should be decrypted automatically

        # Add step with sensitive data
        encrypted_db.add_session_step(
            session_id,
            "sensitive_analysis",
            1,
            "analysis",
            input_data={"sensitive_info": "confidential data"},
            output_data={"analysis": "private thoughts"},
        )

        steps = encrypted_db.get_session_steps(session_id)
        assert steps[0]["input_data"]["sensitive_info"] == "confidential data"

    def test_data_security_features(self, encrypted_db):
        """Test additional data security features"""
        session_id = "security-test"
        topic = "Confidential research topic"

        # Create session with sensitive configuration
        config = {
            "api_keys": "secret-key-123",
            "user_preferences": {"privacy_level": "high"},
            "internal_notes": "This is confidential information",
        }

        encrypted_db.create_session(session_id, topic, configuration=config)

        # Verify data is stored and retrieved correctly
        session = encrypted_db.get_session(session_id)
        assert session["configuration"]["api_keys"] == "secret-key-123"
        assert session["configuration"]["user_preferences"]["privacy_level"] == "high"

        # Test that raw database doesn't contain unencrypted sensitive data
        # This would require direct database access to verify encryption

    def test_transaction_management(self, temp_db):
        """Test database transaction management"""
        session_id = "transaction-test"
        topic = "Transaction testing"

        # Test successful transaction
        success = temp_db.create_session(session_id, topic)
        assert success

        # Test that duplicate creation fails (integrity constraint)
        success = temp_db.create_session(session_id, topic)
        assert not success

        # Verify original session still exists
        session = temp_db.get_session(session_id)
        assert session is not None
        assert session["topic"] == topic

    def test_data_cleanup_and_archival(self, temp_db):
        """Test data cleanup and archival functionality"""
        from datetime import datetime, timedelta

        # Create multiple sessions with different statuses
        for i in range(5):
            session_id = f"cleanup-test-{i}"
            temp_db.create_session(session_id, f"Topic {i}")

            # Mark some as completed with completed_at timestamp
            if i < 3:
                old_date = (datetime.now() - timedelta(days=1)).isoformat()
                temp_db.update_session(
                    session_id, status="completed", completed_at=old_date
                )

        # Test cleanup of old sessions
        cleaned = temp_db.cleanup_old_sessions(days_old=0)  # Clean all completed
        assert cleaned >= 3  # Should clean at least the 3 completed sessions

        # Verify active sessions remain
        active_sessions = temp_db.list_sessions(status="active")
        assert len(active_sessions) >= 2

    def test_data_export_functionality(self, temp_db):
        """Test data export functionality"""
        session_id = "export-test"
        topic = "Export testing topic"

        # Create session with steps and results
        temp_db.create_session(session_id, topic)
        step_id = temp_db.add_session_step(session_id, "analysis", 1, "analysis")
        temp_db.add_step_result(session_id, step_id, "output", "Analysis result")

        # Export session data
        export_data = temp_db.export_session_data(session_id)

        assert export_data is not None
        assert export_data["session"]["id"] == session_id
        assert export_data["session"]["topic"] == topic
        assert len(export_data["steps"]) == 1
        assert len(export_data["results"]) == 1
        assert "export_timestamp" in export_data

    def test_data_integrity_verification(self, temp_db):
        """Test data integrity verification"""
        # Create some test data
        session_id = "integrity-test"
        temp_db.create_session(session_id, "Integrity test")
        step_id = temp_db.add_session_step(session_id, "test_step", 1, "test")
        temp_db.add_step_result(session_id, step_id, "output", "test result")

        # Run integrity check
        integrity_results = temp_db.verify_data_integrity()

        assert integrity_results["database_integrity"] is True
        assert len(integrity_results["foreign_key_violations"]) == 0
        assert len(integrity_results["orphaned_records"]) == 0
        assert integrity_results["data_consistency"] is True


class TestSessionManager:
    """Test the session manager"""

    @pytest.fixture
    def temp_session_manager(self):
        """Create a temporary session manager for testing"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        manager = SessionManager(db_path)
        yield manager

        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)

    def test_create_and_get_session(self, temp_session_manager):
        """Test session creation and retrieval"""
        from src.mcps.deep_thinking.models.mcp_models import SessionState
        import uuid

        topic = "How to improve learning efficiency"
        session_id = str(uuid.uuid4())

        # Create SessionState object as expected by the current interface
        session_state = SessionState(
            session_id=session_id,
            topic=topic,
            current_step="initialize",
            flow_type="comprehensive_analysis",
            context={"complexity": "moderate"},
        )

        created_session_id = temp_session_manager.create_session(session_state)
        assert created_session_id == session_id

        session = temp_session_manager.get_session(session_id)
        assert session.topic == topic
        assert session.status == "active"
        assert session.flow_type == "comprehensive_analysis"

    def test_update_session_step(self, temp_session_manager):
        """Test session step updates"""
        from src.mcps.deep_thinking.models.mcp_models import SessionState
        import uuid

        topic = "AI ethics framework"
        session_id = str(uuid.uuid4())

        # Create SessionState object
        session_state = SessionState(
            session_id=session_id,
            topic=topic,
            current_step="initialize",
            flow_type="comprehensive_analysis",
            context={"complexity": "moderate"},
        )

        created_session_id = temp_session_manager.create_session(session_state)

        success = temp_session_manager.update_session_step(
            session_id,
            "problem_decomposition",
            step_result="Identified 5 key ethical dimensions",
            quality_score=0.85,
        )
        assert success

        session = temp_session_manager.get_session(session_id)
        assert session.current_step == "problem_decomposition"
        assert session.step_number == 1
        assert session.quality_scores["problem_decomposition"] == 0.85

    def test_session_context(self, temp_session_manager):
        """Test session context generation"""
        from src.mcps.deep_thinking.models.mcp_models import SessionState
        import uuid

        topic = "Sustainable development goals"
        session_id = str(uuid.uuid4())

        # Create SessionState object
        session_state = SessionState(
            session_id=session_id,
            topic=topic,
            current_step="initialize",
            flow_type="comprehensive_analysis",
            context={"complexity": "moderate"},
        )

        temp_session_manager.create_session(session_state)

        # Add some steps
        temp_session_manager.update_session_step(
            session_id, "decompose", "Step 1 result"
        )
        temp_session_manager.update_session_step(
            session_id, "evidence", "Step 2 result"
        )

        context = temp_session_manager.get_session_context(session_id)

        assert context["topic"] == topic
        assert context["current_step"] == "evidence"
        assert len(context["completed_steps"]) == 2
        assert "recent_steps" in context

    def test_complete_session(self, temp_session_manager):
        """Test session completion"""
        from src.mcps.deep_thinking.models.mcp_models import SessionState
        import uuid

        topic = "Innovation in education"
        session_id = str(uuid.uuid4())

        # Create SessionState object
        session_state = SessionState(
            session_id=session_id,
            topic=topic,
            current_step="initialize",
            flow_type="comprehensive_analysis",
            context={"complexity": "moderate"},
        )

        temp_session_manager.create_session(session_state)

        final_results = {
            "summary": "Comprehensive analysis completed",
            "key_insights": ["insight 1", "insight 2"],
            "recommendations": ["rec 1", "rec 2"],
        }

        success = temp_session_manager.complete_session(session_id, final_results)
        assert success

        session = temp_session_manager.get_session(session_id)
        assert session.status == "completed"

    def test_session_history(self, temp_session_manager):
        """Test session history retrieval"""
        from src.mcps.deep_thinking.models.mcp_models import SessionState
        import uuid

        topic = "Future of work"
        session_id = str(uuid.uuid4())

        # Create SessionState object
        session_state = SessionState(
            session_id=session_id,
            topic=topic,
            current_step="initialize",
            flow_type="comprehensive_analysis",
            context={"complexity": "moderate"},
        )

        temp_session_manager.create_session(session_state)

        # Add steps and results
        temp_session_manager.update_session_step(
            session_id, "analysis", "Analysis result"
        )
        temp_session_manager.add_step_result(
            session_id,
            "analysis",
            "Detailed analysis content",
            metadata={"word_count": 300},
        )

        history = temp_session_manager.get_session_history(session_id)

        assert "session" in history
        assert "steps" in history
        assert "summary" in history
        assert history["summary"]["total_steps"] == 1
        assert len(history["steps"][0]["results"]) == 1

    def test_session_search(self, temp_session_manager):
        """Test session search functionality"""
        from src.mcps.deep_thinking.models.mcp_models import SessionState
        import uuid

        # Create multiple sessions with different topics
        topics = ["Machine Learning", "Artificial Intelligence", "Data Science"]
        session_ids = []

        for topic in topics:
            session_id = str(uuid.uuid4())
            session_state = SessionState(
                session_id=session_id,
                topic=topic,
                current_step="initialize",
                flow_type="comprehensive_analysis",
                context={"complexity": "moderate"},
            )
            temp_session_manager.create_session(session_state)
            session_ids.append(session_id)

        # Search for sessions
        ml_sessions = temp_session_manager.search_sessions("Machine")
        assert len(ml_sessions) >= 1
        assert any("Machine Learning" in session["topic"] for session in ml_sessions)

        ai_sessions = temp_session_manager.search_sessions("Intelligence")
        assert len(ai_sessions) >= 1
        assert any(
            "Artificial Intelligence" in session["topic"] for session in ai_sessions
        )

    def test_session_analytics(self, temp_session_manager):
        """Test session analytics functionality"""
        from src.mcps.deep_thinking.models.mcp_models import SessionState
        import uuid

        session_id = str(uuid.uuid4())
        topic = "Analytics test topic"

        # Create session
        session_state = SessionState(
            session_id=session_id,
            topic=topic,
            current_step="initialize",
            flow_type="comprehensive_analysis",
            context={"complexity": "moderate"},
        )
        temp_session_manager.create_session(session_state)

        # Add some steps with quality scores
        temp_session_manager.update_session_step(
            session_id, "analysis", "Analysis result", quality_score=0.8
        )
        temp_session_manager.update_session_step(
            session_id, "evaluation", "Evaluation result", quality_score=0.9
        )

        # Get analytics
        analytics = temp_session_manager.get_session_analytics(session_id)

        assert analytics["session_id"] == session_id
        assert analytics["topic"] == topic
        assert analytics["step_analytics"]["total_steps"] == 2
        assert analytics["quality_analytics"]["overall_quality"] > 0
        assert "step_quality_scores" in analytics["step_analytics"]

    def test_session_archival_and_restoration(self, temp_session_manager):
        """Test session archival and restoration"""
        from src.mcps.deep_thinking.models.mcp_models import SessionState
        import uuid

        session_id = str(uuid.uuid4())
        topic = "Archival test topic"

        # Create session
        session_state = SessionState(
            session_id=session_id,
            topic=topic,
            current_step="initialize",
            flow_type="comprehensive_analysis",
            context={"complexity": "moderate"},
        )
        temp_session_manager.create_session(session_state)

        # Archive session
        success = temp_session_manager.archive_session(session_id, "Testing archival")
        assert success

        # Verify session is archived
        session = temp_session_manager.get_session(session_id)
        assert session.status == "archived"
        assert session.context.get("archived") is True
        assert "archive_reason" in session.context

        # Restore session
        success = temp_session_manager.restore_session(session_id)
        assert success

        # Verify session is restored
        session = temp_session_manager.get_session(session_id)
        assert session.status == "active"
        assert session.context.get("restored") is True

    def test_bulk_session_updates(self, temp_session_manager):
        """Test bulk session updates"""
        from src.mcps.deep_thinking.models.mcp_models import SessionState
        import uuid

        # Create multiple sessions
        session_ids = []
        for i in range(3):
            session_id = str(uuid.uuid4())
            session_state = SessionState(
                session_id=session_id,
                topic=f"Bulk test topic {i}",
                current_step="initialize",
                flow_type="comprehensive_analysis",
                context={"complexity": "moderate"},
            )
            temp_session_manager.create_session(session_state)
            session_ids.append(session_id)

        # Bulk update
        updates = {"status": "paused"}
        results = temp_session_manager.bulk_update_sessions(session_ids, updates)

        # Verify all updates succeeded
        assert len(results) == 3
        assert all(results.values())

        # Verify sessions were updated
        for session_id in session_ids:
            session = temp_session_manager.get_session(session_id)
            assert session.status == "paused"

    def test_session_timeline(self, temp_session_manager):
        """Test session timeline functionality"""
        from src.mcps.deep_thinking.models.mcp_models import SessionState
        import uuid

        session_id = str(uuid.uuid4())
        topic = "Timeline test topic"

        # Create session
        session_state = SessionState(
            session_id=session_id,
            topic=topic,
            current_step="initialize",
            flow_type="comprehensive_analysis",
            context={"complexity": "moderate"},
        )
        temp_session_manager.create_session(session_state)

        # Add steps and results
        temp_session_manager.update_session_step(
            session_id, "analysis", "Analysis result"
        )
        temp_session_manager.add_step_result(
            session_id, "analysis", "Detailed analysis"
        )

        # Get timeline
        timeline = temp_session_manager.get_session_timeline(session_id)

        assert len(timeline) >= 3  # session_created, step_completed, result_added

        # Check that all expected event types are present
        event_types = [event["event_type"] for event in timeline]
        assert "session_created" in event_types
        assert "step_completed" in event_types
        assert "result_added" in event_types

        # Verify timeline is sorted by timestamp
        timestamps = [event["timestamp"] for event in timeline if event["timestamp"]]
        assert timestamps == sorted(timestamps)


if __name__ == "__main__":
    pytest.main([__file__])
