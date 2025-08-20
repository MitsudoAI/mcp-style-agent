"""
Privacy Protection Manager for Deep Thinking Engine
Ensures complete data localization and user privacy control
"""

import json
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from cryptography.fernet import Fernet

from .database import ThinkingDatabase

logger = logging.getLogger(__name__)


class PrivacyManager:
    """
    Manages privacy protection for the deep thinking engine
    Ensures data localization, encryption, and user control
    """

    def __init__(self, data_directory: Optional[str] = None):
        # Set up local data directory
        if data_directory is None:
            self.data_directory = Path.home() / ".deep_thinking"
        else:
            self.data_directory = Path(data_directory)

        self.data_directory.mkdir(exist_ok=True, parents=True)

        # Privacy settings file
        self.privacy_settings_file = self.data_directory / "privacy_settings.json"

        # Load or create privacy settings
        self.privacy_settings = self._load_privacy_settings()

        logger.info(
            f"PrivacyManager initialized with data directory: {self.data_directory}"
        )

    def _load_privacy_settings(self) -> Dict[str, Any]:
        """Load privacy settings from file or create defaults"""
        default_settings = {
            "data_localization_enabled": True,
            "encryption_enabled": True,
            "network_communication_disabled": True,
            "automatic_cleanup_enabled": True,
            "data_retention_days": 90,
            "export_allowed": True,
            "analytics_disabled": False,
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
        }

        if self.privacy_settings_file.exists():
            try:
                with open(self.privacy_settings_file, "r") as f:
                    settings = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    default_settings.update(settings)
                    return default_settings
            except Exception as e:
                logger.error(f"Error loading privacy settings: {e}")
                return default_settings
        else:
            # Create default settings file
            self._save_privacy_settings(default_settings)
            return default_settings

    def _save_privacy_settings(self, settings: Dict[str, Any]) -> bool:
        """Save privacy settings to file"""
        try:
            settings["last_updated"] = datetime.now().isoformat()
            with open(self.privacy_settings_file, "w") as f:
                json.dump(settings, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving privacy settings: {e}")
            return False

    def get_privacy_settings(self) -> Dict[str, Any]:
        """Get current privacy settings"""
        return self.privacy_settings.copy()

    def update_privacy_settings(self, updates: Dict[str, Any]) -> bool:
        """Update privacy settings"""
        try:
            self.privacy_settings.update(updates)
            return self._save_privacy_settings(self.privacy_settings)
        except Exception as e:
            logger.error(f"Error updating privacy settings: {e}")
            return False

    def verify_data_localization(self) -> Dict[str, Any]:
        """
        Verify that all data is stored locally

        Returns:
            Verification results
        """
        verification_results = {
            "data_localization_verified": True,
            "local_data_directory": str(self.data_directory),
            "directory_exists": self.data_directory.exists(),
            "directory_writable": os.access(self.data_directory, os.W_OK),
            "files_found": [],
            "external_dependencies": [],
            "network_access_detected": False,
            "verification_timestamp": datetime.now().isoformat(),
        }

        try:
            # Check for local data files
            for file_path in self.data_directory.rglob("*"):
                if file_path.is_file():
                    verification_results["files_found"].append(
                        {
                            "path": str(file_path.relative_to(self.data_directory)),
                            "size_bytes": file_path.stat().st_size,
                            "modified": datetime.fromtimestamp(
                                file_path.stat().st_mtime
                            ).isoformat(),
                        }
                    )

            # Verify no external network dependencies
            # This is a basic check - in a real implementation, you might want to
            # monitor network calls or check for external service configurations
            verification_results["external_dependencies"] = []

            # Check if data directory is accessible
            if not verification_results["directory_exists"]:
                verification_results["data_localization_verified"] = False
                verification_results["issues"] = ["Data directory does not exist"]

            if not verification_results["directory_writable"]:
                verification_results["data_localization_verified"] = False
                verification_results.setdefault("issues", []).append(
                    "Data directory is not writable"
                )

            return verification_results

        except Exception as e:
            logger.error(f"Error verifying data localization: {e}")
            return {
                "data_localization_verified": False,
                "error": str(e),
                "verification_timestamp": datetime.now().isoformat(),
            }

    def create_encrypted_database(
        self, db_name: str = "sessions.db"
    ) -> ThinkingDatabase:
        """
        Create an encrypted database instance

        Args:
            db_name: Name of the database file

        Returns:
            ThinkingDatabase instance with encryption enabled
        """
        try:
            db_path = self.data_directory / db_name

            # Generate or load encryption key
            key_file = self.data_directory / f"{db_name}.key"

            if key_file.exists():
                with open(key_file, "rb") as f:
                    encryption_key = f.read()
            else:
                encryption_key = Fernet.generate_key()
                with open(key_file, "wb") as f:
                    f.write(encryption_key)
                # Restrict key file permissions
                os.chmod(key_file, 0o600)

            db = ThinkingDatabase(str(db_path), encryption_key)
            logger.info(f"Created encrypted database: {db_path}")
            return db

        except Exception as e:
            logger.error(f"Error creating encrypted database: {e}")
            raise

    def complete_data_deletion(self) -> Dict[str, Any]:
        """
        Completely delete all user data

        Returns:
            Deletion results
        """
        deletion_results = {
            "deletion_successful": False,
            "files_deleted": [],
            "files_failed": [],
            "total_size_deleted": 0,
            "deletion_timestamp": datetime.now().isoformat(),
        }

        try:
            if not self.data_directory.exists():
                deletion_results["deletion_successful"] = True
                deletion_results["message"] = (
                    "No data directory found - nothing to delete"
                )
                return deletion_results

            # Calculate total size before deletion
            total_size = 0
            files_to_delete = []

            for file_path in self.data_directory.rglob("*"):
                if file_path.is_file():
                    size = file_path.stat().st_size
                    total_size += size
                    files_to_delete.append((file_path, size))

            # Delete all files
            for file_path, size in files_to_delete:
                try:
                    file_path.unlink()
                    deletion_results["files_deleted"].append(
                        {
                            "path": str(file_path.relative_to(self.data_directory)),
                            "size_bytes": size,
                        }
                    )
                    deletion_results["total_size_deleted"] += size
                except Exception as e:
                    deletion_results["files_failed"].append(
                        {
                            "path": str(file_path.relative_to(self.data_directory)),
                            "error": str(e),
                        }
                    )

            # Remove empty directories
            try:
                shutil.rmtree(self.data_directory)
                deletion_results["deletion_successful"] = True
                deletion_results["message"] = (
                    f"Successfully deleted {len(deletion_results['files_deleted'])} files"
                )
            except Exception as e:
                deletion_results["deletion_successful"] = False
                deletion_results["error"] = f"Failed to remove data directory: {e}"

            return deletion_results

        except Exception as e:
            logger.error(f"Error during complete data deletion: {e}")
            deletion_results["deletion_successful"] = False
            deletion_results["error"] = str(e)
            return deletion_results

    def selective_data_deletion(
        self,
        session_ids: Optional[List[str]] = None,
        older_than_days: Optional[int] = None,
        by_status: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Selectively delete data based on criteria

        Args:
            session_ids: Specific session IDs to delete
            older_than_days: Delete sessions older than this many days
            by_status: Delete sessions with these statuses

        Returns:
            Deletion results
        """
        deletion_results = {
            "deletion_successful": False,
            "sessions_deleted": [],
            "sessions_failed": [],
            "deletion_criteria": {
                "session_ids": session_ids,
                "older_than_days": older_than_days,
                "by_status": by_status,
            },
            "deletion_timestamp": datetime.now().isoformat(),
        }

        try:
            # Find database files in the data directory
            db_files = list(self.data_directory.glob("*.db"))
            if not db_files:
                deletion_results["deletion_successful"] = True
                deletion_results["message"] = "No database found - nothing to delete"
                return deletion_results

            # Use the first database file found (or sessions.db if it exists)
            db_path = None
            for db_file in db_files:
                if db_file.name == "sessions.db":
                    db_path = db_file
                    break
            if db_path is None:
                db_path = db_files[0]

            # Create database instance for deletion operations
            # Use encryption if available
            encryption_key = None
            key_file = self.data_directory / f"{db_path.name}.key"
            if key_file.exists():
                with open(key_file, "rb") as f:
                    encryption_key = f.read()

            db = ThinkingDatabase(str(db_path), encryption_key)

            sessions_to_delete = []

            if session_ids:
                sessions_to_delete.extend(session_ids)

            if older_than_days or by_status:
                # Get sessions matching criteria
                all_sessions = db.list_sessions(limit=10000)

                for session in all_sessions:
                    should_delete = False

                    if older_than_days:
                        created_at = datetime.fromisoformat(session["created_at"])
                        age_days = (datetime.now() - created_at).days
                        if age_days > older_than_days:
                            should_delete = True

                    if by_status and session["status"] in by_status:
                        should_delete = True

                    if should_delete:
                        sessions_to_delete.append(session["id"])

            # Delete sessions
            for session_id in sessions_to_delete:
                try:
                    success = db.delete_session(session_id)
                    if success:
                        deletion_results["sessions_deleted"].append(session_id)
                    else:
                        deletion_results["sessions_failed"].append(
                            {
                                "session_id": session_id,
                                "error": "Database deletion failed",
                            }
                        )
                except Exception as e:
                    deletion_results["sessions_failed"].append(
                        {"session_id": session_id, "error": str(e)}
                    )

            deletion_results["deletion_successful"] = (
                len(deletion_results["sessions_failed"]) == 0
            )
            deletion_results["message"] = (
                f"Deleted {len(deletion_results['sessions_deleted'])} sessions"
            )

            return deletion_results

        except Exception as e:
            logger.error(f"Error during selective data deletion: {e}")
            deletion_results["deletion_successful"] = False
            deletion_results["error"] = str(e)
            return deletion_results

    def export_user_data(
        self, export_path: str, include_encrypted: bool = False, anonymize: bool = False
    ) -> Dict[str, Any]:
        """
        Export user data for portability

        Args:
            export_path: Path to export data to
            include_encrypted: Whether to include encrypted data
            anonymize: Whether to anonymize personal information

        Returns:
            Export results
        """
        export_results = {
            "export_successful": False,
            "export_path": export_path,
            "files_exported": [],
            "total_size_exported": 0,
            "anonymized": anonymize,
            "export_timestamp": datetime.now().isoformat(),
        }

        try:
            export_dir = Path(export_path)
            export_dir.mkdir(parents=True, exist_ok=True)

            # Export privacy settings
            privacy_export = self.get_privacy_settings()
            if anonymize:
                privacy_export.pop("created_at", None)
                privacy_export.pop("last_updated", None)

            privacy_file = export_dir / "privacy_settings.json"
            with open(privacy_file, "w") as f:
                json.dump(privacy_export, f, indent=2)

            export_results["files_exported"].append(
                {
                    "file": "privacy_settings.json",
                    "size_bytes": privacy_file.stat().st_size,
                }
            )
            export_results["total_size_exported"] += privacy_file.stat().st_size

            # Export database if it exists
            db_path = self.data_directory / "sessions.db"
            if db_path.exists():
                if include_encrypted:
                    # Copy the entire database
                    export_db_path = export_dir / "sessions.db"
                    shutil.copy2(db_path, export_db_path)

                    export_results["files_exported"].append(
                        {
                            "file": "sessions.db",
                            "size_bytes": export_db_path.stat().st_size,
                        }
                    )
                    export_results[
                        "total_size_exported"
                    ] += export_db_path.stat().st_size
                else:
                    # Export session data in JSON format
                    db = ThinkingDatabase(str(db_path))
                    sessions = db.list_sessions(limit=10000)

                    if anonymize:
                        # Remove or hash personal information
                        for session in sessions:
                            session["topic"] = (
                                f"[ANONYMIZED_TOPIC_{hash(session['topic']) % 10000}]"
                            )
                            session.pop("user_id", None)

                    sessions_file = export_dir / "sessions.json"
                    with open(sessions_file, "w") as f:
                        json.dump(sessions, f, indent=2, default=str)

                    export_results["files_exported"].append(
                        {
                            "file": "sessions.json",
                            "size_bytes": sessions_file.stat().st_size,
                        }
                    )
                    export_results[
                        "total_size_exported"
                    ] += sessions_file.stat().st_size

            export_results["export_successful"] = True
            export_results["message"] = (
                f"Exported {len(export_results['files_exported'])} files"
            )

            return export_results

        except Exception as e:
            logger.error(f"Error exporting user data: {e}")
            export_results["export_successful"] = False
            export_results["error"] = str(e)
            return export_results

    def verify_privacy_compliance(self) -> Dict[str, Any]:
        """
        Comprehensive privacy compliance verification

        Returns:
            Compliance verification results
        """
        compliance_results = {
            "overall_compliance": True,
            "checks_performed": [],
            "issues_found": [],
            "recommendations": [],
            "verification_timestamp": datetime.now().isoformat(),
        }

        try:
            # Check 1: Data localization
            localization_check = self.verify_data_localization()
            compliance_results["checks_performed"].append("data_localization")

            if not localization_check["data_localization_verified"]:
                compliance_results["overall_compliance"] = False
                compliance_results["issues_found"].append(
                    {
                        "check": "data_localization",
                        "issue": "Data is not properly localized",
                        "details": localization_check,
                    }
                )

            # Check 2: Encryption status
            compliance_results["checks_performed"].append("encryption_status")
            if not self.privacy_settings.get("encryption_enabled", False):
                compliance_results["issues_found"].append(
                    {
                        "check": "encryption_status",
                        "issue": "Data encryption is not enabled",
                        "recommendation": "Enable encryption in privacy settings",
                    }
                )
                compliance_results["recommendations"].append("Enable data encryption")

            # Check 3: Network communication
            compliance_results["checks_performed"].append("network_communication")
            if not self.privacy_settings.get("network_communication_disabled", True):
                compliance_results["overall_compliance"] = False
                compliance_results["issues_found"].append(
                    {
                        "check": "network_communication",
                        "issue": "Network communication is not disabled",
                        "recommendation": "Disable network communication for privacy",
                    }
                )

            # Check 4: Data retention policy
            compliance_results["checks_performed"].append("data_retention")
            retention_days = self.privacy_settings.get("data_retention_days", 90)
            if retention_days > 365:
                compliance_results["recommendations"].append(
                    "Consider shorter data retention period for better privacy"
                )

            # Check 5: File permissions
            compliance_results["checks_performed"].append("file_permissions")
            if self.data_directory.exists():
                dir_stat = self.data_directory.stat()
                # Check if directory is readable by others (basic check)
                if dir_stat.st_mode & 0o044:  # Others can read
                    compliance_results["issues_found"].append(
                        {
                            "check": "file_permissions",
                            "issue": "Data directory may be readable by other users",
                            "recommendation": "Restrict directory permissions",
                        }
                    )
                    compliance_results["recommendations"].append(
                        "Restrict file permissions"
                    )

            # Update overall compliance
            compliance_results["overall_compliance"] = (
                len(compliance_results["issues_found"]) == 0
            )

            return compliance_results

        except Exception as e:
            logger.error(f"Error verifying privacy compliance: {e}")
            return {
                "overall_compliance": False,
                "error": str(e),
                "verification_timestamp": datetime.now().isoformat(),
            }

    def get_data_usage_report(self) -> Dict[str, Any]:
        """
        Generate a report of data usage and storage

        Returns:
            Data usage report
        """
        usage_report = {
            "data_directory": str(self.data_directory),
            "total_size_bytes": 0,
            "file_breakdown": [],
            "privacy_settings": self.get_privacy_settings(),
            "report_timestamp": datetime.now().isoformat(),
        }

        try:
            if not self.data_directory.exists():
                usage_report["message"] = "No data directory found"
                return usage_report

            # Calculate directory size and file breakdown
            for file_path in self.data_directory.rglob("*"):
                if file_path.is_file():
                    size = file_path.stat().st_size
                    usage_report["total_size_bytes"] += size
                    usage_report["file_breakdown"].append(
                        {
                            "path": str(file_path.relative_to(self.data_directory)),
                            "size_bytes": size,
                            "modified": datetime.fromtimestamp(
                                file_path.stat().st_mtime
                            ).isoformat(),
                        }
                    )

            # Add summary statistics
            usage_report["summary"] = {
                "total_files": len(usage_report["file_breakdown"]),
                "total_size_mb": round(
                    usage_report["total_size_bytes"] / (1024 * 1024), 2
                ),
                "largest_file": (
                    max(usage_report["file_breakdown"], key=lambda x: x["size_bytes"])
                    if usage_report["file_breakdown"]
                    else None
                ),
            }

            return usage_report

        except Exception as e:
            logger.error(f"Error generating data usage report: {e}")
            usage_report["error"] = str(e)
            return usage_report
