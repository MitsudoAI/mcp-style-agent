"""
Tests for privacy protection mechanisms
"""

import json
import os
import tempfile
from pathlib import Path

import pytest

from src.mcps.deep_thinking.data.privacy_manager import PrivacyManager
from src.mcps.deep_thinking.data.database import ThinkingDatabase


class TestPrivacyManager:
    """Test privacy protection functionality"""

    @pytest.fixture
    def temp_privacy_manager(self):
        """Create a temporary privacy manager for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = PrivacyManager(temp_dir)
            yield manager

    def test_privacy_settings_initialization(self, temp_privacy_manager):
        """Test privacy settings are properly initialized"""
        settings = temp_privacy_manager.get_privacy_settings()

        # Check default settings
        assert settings["data_localization_enabled"] is True
        assert settings["encryption_enabled"] is True
        assert settings["network_communication_disabled"] is True
        assert settings["automatic_cleanup_enabled"] is True
        assert "created_at" in settings
        assert "last_updated" in settings

    def test_privacy_settings_update(self, temp_privacy_manager):
        """Test updating privacy settings"""
        updates = {"data_retention_days": 30, "analytics_disabled": True}

        success = temp_privacy_manager.update_privacy_settings(updates)
        assert success

        # Verify updates
        settings = temp_privacy_manager.get_privacy_settings()
        assert settings["data_retention_days"] == 30
        assert settings["analytics_disabled"] is True

    def test_data_localization_verification(self, temp_privacy_manager):
        """Test data localization verification"""
        verification = temp_privacy_manager.verify_data_localization()

        assert "data_localization_verified" in verification
        assert "local_data_directory" in verification
        assert "directory_exists" in verification
        assert "directory_writable" in verification
        assert "files_found" in verification
        assert "verification_timestamp" in verification

        # Should be verified since we're using local temp directory
        assert verification["data_localization_verified"] is True
        assert verification["directory_exists"] is True

    def test_encrypted_database_creation(self, temp_privacy_manager):
        """Test creation of encrypted database"""
        db = temp_privacy_manager.create_encrypted_database("test.db")

        assert db is not None
        assert db.encryption is not None

        # Verify key file was created
        key_file = Path(temp_privacy_manager.data_directory) / "test.db.key"
        assert key_file.exists()

        # Verify key file permissions are restricted
        key_stat = key_file.stat()
        assert oct(key_stat.st_mode)[-3:] == "600"  # Owner read/write only

    def test_complete_data_deletion(self, temp_privacy_manager):
        """Test complete data deletion"""
        # Create some test data
        test_file = Path(temp_privacy_manager.data_directory) / "test_data.txt"
        test_file.write_text("test data")

        # Create encrypted database
        temp_privacy_manager.create_encrypted_database("test.db")

        # Verify data exists
        assert test_file.exists()
        assert len(list(Path(temp_privacy_manager.data_directory).iterdir())) > 0

        # Delete all data
        deletion_results = temp_privacy_manager.complete_data_deletion()

        assert deletion_results["deletion_successful"] is True
        assert len(deletion_results["files_deleted"]) > 0
        assert deletion_results["total_size_deleted"] > 0

        # Verify data directory is gone
        assert not Path(temp_privacy_manager.data_directory).exists()

    def test_selective_data_deletion(self, temp_privacy_manager):
        """Test selective data deletion"""
        # Create encrypted database with test data
        db = temp_privacy_manager.create_encrypted_database("sessions.db")

        # Create test sessions
        session_ids = []
        for i in range(3):
            session_id = f"test-session-{i}"
            db.create_session(session_id, f"Test topic {i}")
            session_ids.append(session_id)

        # Delete specific sessions
        deletion_results = temp_privacy_manager.selective_data_deletion(
            session_ids=[session_ids[0], session_ids[1]]
        )

        assert deletion_results["deletion_successful"] is True
        assert len(deletion_results["sessions_deleted"]) == 2

        # Verify remaining session still exists
        remaining_session = db.get_session(session_ids[2])
        assert remaining_session is not None

    def test_user_data_export(self, temp_privacy_manager):
        """Test user data export functionality"""
        # Create some test data
        db = temp_privacy_manager.create_encrypted_database("sessions.db")
        db.create_session("export-test", "Export test topic")

        with tempfile.TemporaryDirectory() as export_dir:
            export_results = temp_privacy_manager.export_user_data(
                export_dir, include_encrypted=False, anonymize=False
            )

            assert export_results["export_successful"] is True
            assert len(export_results["files_exported"]) > 0
            assert export_results["total_size_exported"] > 0

            # Verify exported files exist
            export_path = Path(export_dir)
            assert (export_path / "privacy_settings.json").exists()
            assert (export_path / "sessions.json").exists()

    def test_anonymized_data_export(self, temp_privacy_manager):
        """Test anonymized data export"""
        # Create test data
        db = temp_privacy_manager.create_encrypted_database("sessions.db")
        db.create_session("anon-test", "Sensitive topic information")

        with tempfile.TemporaryDirectory() as export_dir:
            export_results = temp_privacy_manager.export_user_data(
                export_dir, include_encrypted=False, anonymize=True
            )

            assert export_results["export_successful"] is True
            assert export_results["anonymized"] is True

            # Verify data is anonymized
            sessions_file = Path(export_dir) / "sessions.json"
            with open(sessions_file, "r") as f:
                sessions_data = json.load(f)

            # Topic should be anonymized
            assert "ANONYMIZED_TOPIC" in sessions_data[0]["topic"]
            assert "Sensitive topic information" not in sessions_data[0]["topic"]

    def test_privacy_compliance_verification(self, temp_privacy_manager):
        """Test comprehensive privacy compliance verification"""
        compliance_results = temp_privacy_manager.verify_privacy_compliance()

        assert "overall_compliance" in compliance_results
        assert "checks_performed" in compliance_results
        assert "issues_found" in compliance_results
        assert "recommendations" in compliance_results
        assert "verification_timestamp" in compliance_results

        # Should pass basic compliance checks
        expected_checks = [
            "data_localization",
            "encryption_status",
            "network_communication",
            "data_retention",
            "file_permissions",
        ]

        for check in expected_checks:
            assert check in compliance_results["checks_performed"]

    def test_data_usage_report(self, temp_privacy_manager):
        """Test data usage reporting"""
        # Create some test data
        db = temp_privacy_manager.create_encrypted_database("sessions.db")
        db.create_session("usage-test", "Usage test topic")

        usage_report = temp_privacy_manager.get_data_usage_report()

        assert "data_directory" in usage_report
        assert "total_size_bytes" in usage_report
        assert "file_breakdown" in usage_report
        assert "privacy_settings" in usage_report
        assert "summary" in usage_report
        assert "report_timestamp" in usage_report

        # Should have some files
        assert usage_report["total_size_bytes"] > 0
        assert len(usage_report["file_breakdown"]) > 0
        assert usage_report["summary"]["total_files"] > 0

    def test_zero_network_communication_verification(self, temp_privacy_manager):
        """Test verification that no network communication occurs"""
        # This test verifies the privacy manager itself doesn't make network calls
        # In a real implementation, you might want to use network monitoring

        settings = temp_privacy_manager.get_privacy_settings()
        assert settings["network_communication_disabled"] is True

        # Verify privacy manager operations don't require network
        verification = temp_privacy_manager.verify_data_localization()
        assert verification["network_access_detected"] is False

        compliance = temp_privacy_manager.verify_privacy_compliance()
        # Should be able to verify compliance without network access
        assert "network_communication" in compliance["checks_performed"]

    def test_user_data_control(self, temp_privacy_manager):
        """Test that users have complete control over their data"""
        # Create test data
        db = temp_privacy_manager.create_encrypted_database("sessions.db")
        session_id = "control-test"
        db.create_session(session_id, "User control test")

        # User should be able to:

        # 1. View their data
        usage_report = temp_privacy_manager.get_data_usage_report()
        assert usage_report["summary"]["total_files"] > 0

        # 2. Export their data
        with tempfile.TemporaryDirectory() as export_dir:
            export_results = temp_privacy_manager.export_user_data(export_dir)
            assert export_results["export_successful"] is True

        # 3. Delete specific data
        deletion_results = temp_privacy_manager.selective_data_deletion(
            session_ids=[session_id]
        )
        assert deletion_results["deletion_successful"] is True
        assert session_id in deletion_results["sessions_deleted"]

        # 4. Delete all data
        deletion_results = temp_privacy_manager.complete_data_deletion()
        assert deletion_results["deletion_successful"] is True

    def test_encryption_key_security(self, temp_privacy_manager):
        """Test encryption key security measures"""
        db = temp_privacy_manager.create_encrypted_database("secure.db")

        key_file = Path(temp_privacy_manager.data_directory) / "secure.db.key"
        assert key_file.exists()

        # Check file permissions
        key_stat = key_file.stat()
        # Should be readable/writable by owner only
        assert oct(key_stat.st_mode)[-3:] == "600"

        # Key should be different each time (if we create a new one)
        with tempfile.TemporaryDirectory() as temp_dir2:
            manager2 = PrivacyManager(temp_dir2)
            db2 = manager2.create_encrypted_database("secure.db")

            key_file2 = Path(temp_dir2) / "secure.db.key"

            # Keys should be different
            with open(key_file, "rb") as f1, open(key_file2, "rb") as f2:
                key1 = f1.read()
                key2 = f2.read()
                assert key1 != key2

    def test_privacy_settings_persistence(self, temp_privacy_manager):
        """Test that privacy settings persist across instances"""
        # Update settings
        updates = {"data_retention_days": 60, "custom_setting": "test_value"}
        temp_privacy_manager.update_privacy_settings(updates)

        # Create new instance with same data directory
        manager2 = PrivacyManager(temp_privacy_manager.data_directory)
        settings2 = manager2.get_privacy_settings()

        # Settings should be preserved
        assert settings2["data_retention_days"] == 60
        assert settings2["custom_setting"] == "test_value"

    def test_data_integrity_after_operations(self, temp_privacy_manager):
        """Test data integrity is maintained after privacy operations"""
        # Create test data
        db = temp_privacy_manager.create_encrypted_database("integrity.db")

        # Create multiple sessions
        session_ids = []
        for i in range(5):
            session_id = f"integrity-test-{i}"
            db.create_session(session_id, f"Integrity test topic {i}")
            session_ids.append(session_id)

        # Perform various operations

        # 1. Export data
        with tempfile.TemporaryDirectory() as export_dir:
            export_results = temp_privacy_manager.export_user_data(export_dir)
            assert export_results["export_successful"] is True

        # 2. Selective deletion
        deletion_results = temp_privacy_manager.selective_data_deletion(
            session_ids=[session_ids[0], session_ids[1]]
        )
        assert deletion_results["deletion_successful"] is True
        assert len(deletion_results["sessions_deleted"]) == 2

        # 3. Verify remaining data integrity using the original database instance
        remaining_sessions = db.list_sessions()

        # Should have 3 sessions remaining (5 - 2 deleted)
        assert len(remaining_sessions) == 3

        # Verify database integrity
        integrity_results = db.verify_data_integrity()
        assert integrity_results["database_integrity"] is True
        assert integrity_results["data_consistency"] is True


if __name__ == "__main__":
    pytest.main([__file__])
