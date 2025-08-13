"""
Session Manager for Deep Thinking Engine
Provides high-level interface for session management with local storage
"""

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..config.exceptions import SessionNotFoundError, SessionStateError
from ..data.database import ThinkingDatabase
from ..models.mcp_models import SessionState

logger = logging.getLogger(__name__)


class SessionManager:
    """
    High-level session management for thinking processes
    Handles session lifecycle, state tracking, and persistence
    """

    def __init__(
        self, db_path: Optional[str] = None, encryption_key: Optional[bytes] = None
    ):
        # Use default path in user's data directory
        if db_path is None:
            data_dir = Path.home() / ".deep_thinking"
            data_dir.mkdir(exist_ok=True)
            db_path = str(data_dir / "sessions.db")

        self.db = ThinkingDatabase(db_path, encryption_key)
        self._active_sessions = {}  # In-memory cache for active sessions
        logger.info(f"SessionManager initialized with database: {db_path}")

    def create_session(self, session_state: SessionState) -> str:
        """
        Create a new thinking session from SessionState

        Args:
            session_state: SessionState object with session details

        Returns:
            Session ID
        """
        # Create session configuration
        configuration = {
            "complexity": session_state.context.get("complexity", "moderate"),
            "flow_type": session_state.flow_type,
            "settings": {
                "quality_threshold": (
                    0.8 if session_state.context.get("complexity") == "complex" else 0.7
                ),
                "max_steps": (
                    20 if session_state.context.get("complexity") == "complex" else 15
                ),
                "enable_bias_detection": True,
                "enable_innovation_thinking": session_state.context.get("complexity")
                in ["moderate", "complex"],
            },
        }

        # Store in database
        success = self.db.create_session(
            session_id=session_state.session_id,
            topic=session_state.topic,
            session_type=session_state.flow_type,
            user_id=None,  # Can be added later if needed
            configuration=configuration,
        )

        if not success:
            raise SessionStateError(
                f"Failed to create session for topic: {session_state}"
            )

        # Store in memory cache
        self._active_sessions[session_state.session_id] = session_state

        logger.info(
            f"Created session {session_state.session_id} for topic: {session_state.topic[:50]}..."
        )
        return session_state.session_id

    def get_session(self, session_id: str) -> SessionState:
        """
        Get session state

        Args:
            session_id: Session identifier

        Returns:
            SessionState object

        Raises:
            SessionNotFoundError: If session doesn't exist
        """
        # Check in-memory cache first
        if session_id in self._active_sessions:
            return self._active_sessions[session_id]

        # Load from database
        session_data = self.db.get_session(session_id)
        if not session_data:
            raise SessionNotFoundError(f"Session {session_id} not found")

        # Convert to SessionState object
        context_data = session_data.get("context") or {}
        quality_data = session_data.get("quality_metrics") or {}
        
        session_state = SessionState(
            session_id=session_data["id"],
            topic=session_data["topic"],
            current_step=session_data.get("current_step", "initialize"),
            step_number=session_data.get("step_number", 0),
            flow_type=session_data.get(
                "flow_type", session_data.get("session_type", "comprehensive_analysis")
            ),
            status=session_data.get("status", "active"),
            step_results=context_data.get("step_results", {}),
            context=context_data,
            quality_scores=quality_data,
            created_at=(
                datetime.fromisoformat(session_data["created_at"])
                if session_data.get("created_at")
                else datetime.now()
            ),
            updated_at=(
                datetime.fromisoformat(session_data["updated_at"])
                if session_data.get("updated_at")
                else datetime.now()
            ),
        )

        # Cache if active
        if session_state.status == "active":
            self._active_sessions[session_id] = session_state

        return session_state

    def update_session_step(
        self,
        session_id: str,
        step_name: str,
        step_result: Optional[str] = None,
        quality_score: Optional[float] = None,
        execution_time_ms: Optional[int] = None,
    ) -> bool:
        """
        Update session with new step information

        Args:
            session_id: Session identifier
            step_name: Name of the current step
            step_result: Result from the step (optional)
            quality_score: Quality score for the step (optional)
            execution_time_ms: Execution time in milliseconds (optional)

        Returns:
            True if successful
        """
        try:
            session = self.get_session(session_id)

            # Update session state
            session.current_step = step_name
            session.step_number += 1
            session.updated_at = datetime.now()

            if step_result:
                session.step_results[step_name] = step_result

            if quality_score is not None:
                session.quality_scores[step_name] = quality_score

            # Add step to database
            self.db.add_session_step(
                session_id=session_id,
                step_name=step_name,
                step_number=session.step_number,
                step_type=self._determine_step_type(step_name),
                input_data={"step_result": step_result} if step_result else None,
                quality_score=quality_score,
                execution_time_ms=execution_time_ms,
            )

            # Update session in database
            self.db.update_session(
                session_id,
                current_step=step_name,
                step_number=session.step_number,
                context=session.context,
                quality_metrics=session.quality_scores,
            )

            # Update cache
            self._active_sessions[session_id] = session

            logger.info(f"Updated session {session_id} to step {step_name}")
            return True

        except Exception as e:
            logger.error(f"Error updating session {session_id}: {e}")
            return False

    def add_step_result(
        self,
        session_id: str,
        step_name: str,
        result_content: str,
        result_type: str = "output",
        metadata: Optional[Dict[str, Any]] = None,
        quality_indicators: Optional[Dict[str, Any]] = None,
        citations: Optional[List[Dict[str, Any]]] = None,
        quality_score: Optional[float] = None,
    ) -> bool:
        """
        Add detailed result to a step

        Args:
            session_id: Session identifier
            step_name: Name of the step
            result_content: The actual result content
            result_type: Type of result (input, output, analysis, evidence)
            metadata: Additional metadata
            quality_indicators: Quality assessment data
            citations: Citation information

        Returns:
            True if successful
        """
        try:
            # Get the step ID, create step if it doesn't exist
            steps = self.db.get_session_steps(session_id)
            step_id = None
            for step in steps:
                if step["step_name"] == step_name:
                    step_id = step["id"]
                    break

            if step_id is None:
                # Create the step if it doesn't exist
                session = self.get_session(session_id)
                step_id = self.db.add_session_step(
                    session_id=session_id,
                    step_name=step_name,
                    step_number=session.step_number + 1,
                    step_type=self._determine_step_type(step_name),
                    quality_score=quality_score,
                )
                if step_id is None:
                    logger.warning(
                        f"Failed to create step {step_name} for session {session_id}"
                    )
                    return False

            # Update session state with result
            session = self.get_session(session_id)
            session.step_results[step_name] = {
                "result": result_content,
                "quality_score": quality_score,
                "timestamp": datetime.now(),
            }
            if quality_score is not None:
                session.quality_scores[step_name] = quality_score

            # Update cache
            self._active_sessions[session_id] = session

            # Add result to database
            result_id = self.db.add_step_result(
                session_id=session_id,
                step_id=step_id,
                result_type=result_type,
                content=result_content,
                metadata=metadata,
                quality_indicators=quality_indicators,
                citations=citations,
            )

            return result_id is not None

        except Exception as e:
            logger.error(f"Error adding result to session {session_id}: {e}")
            return False

    def complete_session(
        self, session_id: str, final_results: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Mark session as completed

        Args:
            session_id: Session identifier
            final_results: Final results and summary

        Returns:
            True if successful
        """
        try:
            session = self.get_session(session_id)
            session.status = "completed"
            session.updated_at = datetime.now()

            # Update database
            updates = {
                "status": "completed",
                "completed_at": datetime.now().isoformat(),
            }

            if final_results:
                # Store final results in context, not quality_metrics
                updated_context = session.context.copy()
                updated_context["final_results"] = final_results
                updates["context"] = updated_context
                updates["quality_metrics"] = session.quality_scores

            success = self.db.update_session(session_id, **updates)

            # Remove from active cache
            self._active_sessions.pop(session_id, None)

            logger.info(f"Completed session {session_id}")
            return success

        except Exception as e:
            logger.error(f"Error completing session {session_id}: {e}")
            return False

    def get_session_history(self, session_id: str) -> Dict[str, Any]:
        """
        Get complete session history including all steps and results

        Args:
            session_id: Session identifier

        Returns:
            Complete session history
        """
        try:
            session = self.get_session(session_id)
            steps = self.db.get_session_steps(session_id)
            results = self.db.get_step_results(session_id)

            # Organize results by step
            step_results = {}
            for result in results:
                step_id = result["step_id"]
                if step_id not in step_results:
                    step_results[step_id] = []
                step_results[step_id].append(result)

            # Combine steps with their results
            detailed_steps = []
            for step in steps:
                step_data = dict(step)
                step_data["results"] = step_results.get(step["id"], [])
                detailed_steps.append(step_data)

            return {
                "session": session.model_dump(),
                "steps": detailed_steps,
                "summary": {
                    "total_steps": len(steps),
                    "total_results": len(results),
                    "average_quality": (
                        sum(session.quality_scores.values())
                        / len(session.quality_scores)
                        if session.quality_scores
                        else 0
                    ),
                    "duration": (
                        (session.updated_at - session.created_at).total_seconds()
                        if session.updated_at
                        else 0
                    ),
                },
            }

        except Exception as e:
            logger.error(f"Error getting session history {session_id}: {e}")
            return {}

    def list_user_sessions(
        self,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        List sessions for a user

        Args:
            user_id: User identifier (optional)
            status: Filter by status (optional)
            limit: Maximum number of sessions to return

        Returns:
            List of session summaries
        """
        return self.db.list_sessions(user_id=user_id, status=status, limit=limit)

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session and all its data

        Args:
            session_id: Session identifier

        Returns:
            True if successful
        """
        try:
            # Remove from cache
            self._active_sessions.pop(session_id, None)

            # Delete from database
            success = self.db.delete_session(session_id)

            if success:
                logger.info(f"Deleted session {session_id}")

            return success

        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {e}")
            return False

    def get_session_context(self, session_id: str) -> Dict[str, Any]:
        """
        Get session context for use in prompts

        Args:
            session_id: Session identifier

        Returns:
            Context dictionary for prompt templates
        """
        try:
            session = self.get_session(session_id)
            steps = self.db.get_session_steps(session_id)

            # Build context summary
            context = {
                "session_id": session_id,
                "topic": session.topic,
                "current_step": session.current_step,
                "step_number": session.step_number,
                "flow_type": session.flow_type,
                "completed_steps": [step["step_name"] for step in steps],
                "step_results": session.step_results,
                "quality_scores": session.quality_scores,
                "progress": f"{len(steps)}/{self._get_expected_steps(session.flow_type)}",
                "session_duration": (
                    datetime.now() - session.created_at
                ).total_seconds()
                / 60,  # minutes
            }

            # Add recent step results for context
            if steps:
                recent_steps = steps[-3:]  # Last 3 steps
                context["recent_steps"] = [
                    {
                        "name": step["step_name"],
                        "result": session.step_results.get(step["step_name"], ""),
                        "quality": session.quality_scores.get(step["step_name"]),
                    }
                    for step in recent_steps
                ]

            return context

        except Exception as e:
            logger.error(f"Error getting session context {session_id}: {e}")
            return {}

    def cleanup_inactive_sessions(self, hours_inactive: int = 24) -> int:
        """
        Clean up sessions that have been inactive for too long

        Args:
            hours_inactive: Hours of inactivity before cleanup

        Returns:
            Number of sessions cleaned up
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours_inactive)

            # Get inactive sessions
            all_sessions = self.db.list_sessions(status="active", limit=1000)
            inactive_sessions = [
                s
                for s in all_sessions
                if datetime.fromisoformat(s["updated_at"]) < cutoff_time
            ]

            cleaned_count = 0
            for session in inactive_sessions:
                # Mark as abandoned rather than delete
                self.db.update_session(session["id"], status="abandoned")
                self._active_sessions.pop(session["id"], None)
                cleaned_count += 1

            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} inactive sessions")

            return cleaned_count

        except Exception as e:
            logger.error(f"Error cleaning up inactive sessions: {e}")
            return 0

    def get_statistics(self) -> Dict[str, Any]:
        """Get session management statistics"""
        try:
            db_stats = self.db.get_database_stats()

            stats = {
                **db_stats,
                "active_sessions_in_memory": len(self._active_sessions),
                "database_path": str(self.db.db_path),
                "encryption_enabled": self.db.encryption is not None,
            }

            return stats

        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}

    def search_sessions(
        self, 
        query: str, 
        search_fields: List[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search sessions by topic, content, or other fields
        
        Args:
            query: Search query string
            search_fields: Fields to search in (topic, configuration, etc.)
            limit: Maximum results to return
            
        Returns:
            List of matching sessions
        """
        try:
            if search_fields is None:
                search_fields = ["topic"]
                
            with self.db.get_connection() as conn:
                # Build search query
                where_clauses = []
                params = []
                
                for field in search_fields:
                    if field == "topic":
                        where_clauses.append("topic LIKE ?")
                        params.append(f"%{query}%")
                    elif field == "configuration":
                        where_clauses.append("configuration LIKE ?")
                        params.append(f"%{query}%")
                
                if not where_clauses:
                    return []
                
                sql = f"""
                    SELECT * FROM thinking_sessions 
                    WHERE {' OR '.join(where_clauses)}
                    ORDER BY created_at DESC 
                    LIMIT ?
                """
                params.append(limit)
                
                cursor = conn.execute(sql, params)
                sessions = []
                
                for row in cursor.fetchall():
                    session_data = dict(row)
                    
                    # Decrypt topic if encrypted
                    if self.db.encryption and session_data.get("topic_encrypted"):
                        session_data["topic"] = self.db._decrypt_if_enabled(
                            session_data["topic_encrypted"]
                        )
                    
                    sessions.append(session_data)
                
                return sessions
                
        except Exception as e:
            logger.error(f"Error searching sessions: {e}")
            return []

    def get_session_analytics(self, session_id: str) -> Dict[str, Any]:
        """
        Get detailed analytics for a session
        
        Args:
            session_id: Session identifier
            
        Returns:
            Analytics data including performance metrics, quality trends, etc.
        """
        try:
            session = self.get_session(session_id)
            steps = self.db.get_session_steps(session_id)
            results = self.db.get_step_results(session_id)
            
            analytics = {
                "session_id": session_id,
                "topic": session.topic,
                "flow_type": session.flow_type,
                "status": session.status,
                "duration_minutes": (
                    (session.updated_at - session.created_at).total_seconds() / 60
                    if session.updated_at and session.created_at
                    else 0
                ),
                "step_analytics": {
                    "total_steps": len(steps),
                    "completed_steps": len([s for s in steps if s.get("status") == "completed"]),
                    "average_execution_time": (
                        sum(s.get("execution_time_ms") or 0 for s in steps) / len(steps)
                        if steps else 0
                    ),
                    "step_quality_scores": {
                        step["step_name"]: step.get("quality_score", 0)
                        for step in steps if step.get("quality_score") is not None
                    }
                },
                "quality_analytics": {
                    "overall_quality": (
                        sum(session.quality_scores.values()) / len(session.quality_scores)
                        if session.quality_scores else 0
                    ),
                    "quality_trend": self._calculate_quality_trend(steps),
                    "low_quality_steps": [
                        step["step_name"] for step in steps 
                        if step.get("quality_score", 1.0) < 0.7
                    ]
                },
                "content_analytics": {
                    "total_results": len(results),
                    "result_types": {},
                    "content_volume": sum(len(r.get("content", "")) for r in results)
                }
            }
            
            # Analyze result types
            for result in results:
                result_type = result.get("result_type", "unknown")
                analytics["content_analytics"]["result_types"][result_type] = (
                    analytics["content_analytics"]["result_types"].get(result_type, 0) + 1
                )
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting session analytics for {session_id}: {e}")
            return {}

    def _calculate_quality_trend(self, steps: List[Dict[str, Any]]) -> str:
        """Calculate quality trend across steps"""
        quality_scores = [
            step.get("quality_score", 0) for step in steps 
            if step.get("quality_score") is not None
        ]
        
        if len(quality_scores) < 2:
            return "insufficient_data"
        
        # Simple trend calculation
        first_half = quality_scores[:len(quality_scores)//2]
        second_half = quality_scores[len(quality_scores)//2:]
        
        first_avg = sum(first_half) / len(first_half)
        second_avg = sum(second_half) / len(second_half)
        
        if second_avg > first_avg + 0.1:
            return "improving"
        elif second_avg < first_avg - 0.1:
            return "declining"
        else:
            return "stable"

    def archive_session(self, session_id: str, archive_reason: str = "") -> bool:
        """
        Archive a session (mark as archived but don't delete)
        
        Args:
            session_id: Session to archive
            archive_reason: Reason for archiving
            
        Returns:
            True if successful
        """
        try:
            session = self.get_session(session_id)
            
            # Update session status and add archive metadata
            archive_context = session.context.copy()
            archive_context.update({
                "archived": True,
                "archive_timestamp": datetime.now().isoformat(),
                "archive_reason": archive_reason,
                "original_status": session.status
            })
            
            success = self.db.update_session(
                session_id,
                status="archived",
                context=archive_context
            )
            
            # Remove from active cache
            self._active_sessions.pop(session_id, None)
            
            if success:
                logger.info(f"Archived session {session_id}: {archive_reason}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error archiving session {session_id}: {e}")
            return False

    def restore_session(self, session_id: str) -> bool:
        """
        Restore an archived session
        
        Args:
            session_id: Session to restore
            
        Returns:
            True if successful
        """
        try:
            session = self.get_session(session_id)
            
            if session.status != "archived":
                logger.warning(f"Session {session_id} is not archived")
                return False
            
            # Restore original status
            original_status = session.context.get("original_status", "active")
            
            # Update context to remove archive metadata
            restore_context = session.context.copy()
            restore_context.pop("archived", None)
            restore_context.pop("archive_timestamp", None)
            restore_context.pop("archive_reason", None)
            restore_context.pop("original_status", None)
            restore_context["restored"] = True
            restore_context["restore_timestamp"] = datetime.now().isoformat()
            
            success = self.db.update_session(
                session_id,
                status=original_status,
                context=restore_context
            )
            
            if success:
                logger.info(f"Restored session {session_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error restoring session {session_id}: {e}")
            return False

    def bulk_update_sessions(
        self, 
        session_ids: List[str], 
        updates: Dict[str, Any]
    ) -> Dict[str, bool]:
        """
        Update multiple sessions in bulk
        
        Args:
            session_ids: List of session IDs to update
            updates: Updates to apply to all sessions
            
        Returns:
            Dictionary mapping session_id to success status
        """
        results = {}
        
        for session_id in session_ids:
            try:
                success = self.db.update_session(session_id, **updates)
                results[session_id] = success
                
                # Update cache if session is active
                if session_id in self._active_sessions:
                    session = self._active_sessions[session_id]
                    for key, value in updates.items():
                        if hasattr(session, key):
                            setattr(session, key, value)
                        elif key in ["context", "quality_metrics"]:
                            if key == "context":
                                session.context.update(value if isinstance(value, dict) else {})
                            elif key == "quality_metrics":
                                session.quality_scores.update(value if isinstance(value, dict) else {})
                
            except Exception as e:
                logger.error(f"Error updating session {session_id}: {e}")
                results[session_id] = False
        
        successful_updates = sum(1 for success in results.values() if success)
        logger.info(f"Bulk updated {successful_updates}/{len(session_ids)} sessions")
        
        return results

    def get_session_timeline(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get chronological timeline of session events
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of timeline events
        """
        try:
            session = self.get_session(session_id)
            steps = self.db.get_session_steps(session_id)
            results = self.db.get_step_results(session_id)
            
            timeline = []
            
            # Add session creation event
            timeline.append({
                "timestamp": session.created_at.isoformat() if session.created_at else "",
                "event_type": "session_created",
                "description": f"Session created for topic: {session.topic}",
                "details": {
                    "flow_type": session.flow_type,
                    "status": "active"
                }
            })
            
            # Add step events
            for step in steps:
                timeline.append({
                    "timestamp": step.get("created_at", ""),
                    "event_type": "step_completed",
                    "description": f"Completed step: {step['step_name']}",
                    "details": {
                        "step_type": step.get("step_type"),
                        "quality_score": step.get("quality_score"),
                        "execution_time_ms": step.get("execution_time_ms")
                    }
                })
            
            # Add result events
            for result in results:
                timeline.append({
                    "timestamp": result.get("created_at", ""),
                    "event_type": "result_added",
                    "description": f"Added {result.get('result_type', 'unknown')} result",
                    "details": {
                        "result_type": result.get("result_type"),
                        "content_length": len(result.get("content", "")),
                        "step_id": result.get("step_id")
                    }
                })
            
            # Add session completion event if completed
            if session.status == "completed":
                timeline.append({
                    "timestamp": session.updated_at.isoformat() if session.updated_at else "",
                    "event_type": "session_completed",
                    "description": "Session completed",
                    "details": {
                        "final_status": session.status,
                        "total_steps": len(steps),
                        "total_results": len(results)
                    }
                })
            
            # Sort by timestamp (handle empty timestamps)
            timeline.sort(key=lambda x: x["timestamp"] or "")
            
            return timeline
            
        except Exception as e:
            logger.error(f"Error getting session timeline for {session_id}: {e}")
            return []

    def _determine_step_type(self, step_name: str) -> str:
        """Determine step type from step name"""
        step_type_mapping = {
            "decompose": "analysis",
            "evidence": "research",
            "debate": "reasoning",
            "evaluate": "assessment",
            "bias": "validation",
            "innovation": "creativity",
            "reflect": "metacognition",
        }

        for key, step_type in step_type_mapping.items():
            if key in step_name.lower():
                return step_type

        return "general"

    def _get_expected_steps(self, flow_type: str) -> int:
        """Get expected number of steps for a flow type"""
        flow_steps = {
            "comprehensive_analysis": 12,
            "quick_analysis": 6,
            "creative_thinking": 8,
            "critical_evaluation": 10,
        }
        return flow_steps.get(flow_type, 10)

    def get_step_summary(self, session_id: str) -> str:
        """Get a summary of completed steps"""
        try:
            session = self.get_session(session_id)
            if not session:
                return "会话未找到"

            steps = self.db.get_session_steps(session_id)

            summary_parts = []
            for step in steps:
                step_name = step.get("step_name", "unknown_step")
                quality = session.quality_scores.get(step_name, "N/A")
                summary_parts.append(f"- {step_name}: 完成 (质量: {quality})")

            return "\n".join(summary_parts) if summary_parts else "暂无完成的步骤"

        except Exception as e:
            logger.error(f"Error getting step summary for {session_id}: {e}")
            return "获取步骤摘要时出错"

    def get_full_trace(self, session_id: str) -> Dict[str, Any]:
        """Get full thinking trace for the session"""
        try:
            session = self.get_session(session_id)
            if not session:
                return {"error": "Session not found"}

            steps = self.db.get_session_steps(session_id)
            results = self.db.get_step_results(session_id)

            trace = {
                "session_id": session_id,
                "topic": session.topic,
                "flow_type": session.flow_type,
                "status": session.status,
                "steps": [],
                "quality_summary": session.quality_scores,
                "total_duration": (
                    (session.updated_at - session.created_at).total_seconds()
                    if session.updated_at and session.created_at
                    else 0
                ),
            }

            # Organize results by step
            step_results = {}
            for result in results:
                step_id = result.get("step_id")
                if step_id and step_id not in step_results:
                    step_results[step_id] = []
                if step_id:
                    step_results[step_id].append(result)

            # Build detailed step trace
            for step in steps:
                step_trace = {
                    "step_name": step.get("step_name", "unknown"),
                    "step_type": step.get("step_type", "general"),
                    "quality_score": step.get("quality_score"),
                    "execution_time_ms": step.get("execution_time_ms"),
                    "results": step_results.get(step.get("id"), []),
                    "timestamp": step.get("created_at"),
                }
                trace["steps"].append(step_trace)

            return trace

        except Exception as e:
            logger.error(f"Error getting full trace for {session_id}: {e}")
            return {"error": str(e)}

    def recover_session(
        self, session_id: str, recovery_data: Dict[str, Any]
    ) -> bool:
        """
        Attempt to recover a session from provided recovery data
        
        Args:
            session_id: Session ID to recover
            recovery_data: Data to use for recovery including:
                - topic: The original topic
                - current_step: Current step name
                - completed_steps: List of completed steps (optional)
                - context: Session context (optional)
                - flow_type: Flow type (optional)
                
        Returns:
            True if recovery successful, False otherwise
        """
        try:
            # Validate required recovery data
            if not recovery_data.get("topic"):
                logger.warning(f"Recovery data missing topic for session {session_id}")
                return False
                
            if not recovery_data.get("current_step"):
                logger.warning(f"Recovery data missing current_step for session {session_id}")
                return False

            # Create new session state from recovery data
            session_state = SessionState(
                session_id=session_id,
                topic=recovery_data["topic"],
                current_step=recovery_data.get("current_step", "decompose_problem"),
                flow_type=recovery_data.get("flow_type", "comprehensive_analysis"),
                context=recovery_data.get("context", {}),
                step_number=len(recovery_data.get("completed_steps", [])),
                status="active",
                created_at=datetime.now(),
            )

            # Add completed steps if provided
            completed_steps = recovery_data.get("completed_steps", [])
            if completed_steps:
                for i, step_name in enumerate(completed_steps):
                    session_state.step_results[step_name] = {
                        "result": f"Recovered step: {step_name}",
                        "quality_score": 0.8,  # Default quality score for recovered steps
                        "timestamp": datetime.now().isoformat(),
                        "recovered": True,
                    }

            # Create the session in database
            configuration = {
                "complexity": session_state.context.get("complexity", "moderate"),
                "flow_type": session_state.flow_type,
                "focus": session_state.context.get("focus", ""),
                "recovered": True,
                "recovery_timestamp": datetime.now().isoformat(),
                "original_session_id": session_id,
            }

            # Create session in database
            success = self.db.create_session(
                session_id=session_id,
                topic=session_state.topic,
                session_type=session_state.flow_type,
                user_id="recovered_user",
                configuration=configuration,
            )

            if not success:
                logger.error(f"Failed to create recovered session in database")
                return False

            # Add recovered steps to database
            for step_name in completed_steps:
                step_id = self.db.add_session_step(
                    session_id=session_state.session_id,
                    step_name=step_name,
                    step_number=completed_steps.index(step_name) + 1,
                    step_type=self._determine_step_type(step_name),
                    quality_score=0.8,
                )
                
                if step_id:
                    # Add a recovery marker result
                    self.db.add_step_result(
                        step_id=step_id,
                        result_type="recovery",
                        content=f"Step {step_name} recovered from session recovery",
                        metadata={"recovered": True, "recovery_timestamp": datetime.now().isoformat()},
                    )

            # Cache the recovered session
            self._active_sessions[session_state.session_id] = session_state

            logger.info(f"Successfully recovered session {session_state.session_id}")
            return True

        except Exception as e:
            logger.error(f"Error recovering session {session_id}: {e}")
            return False

    def detect_flow_interruption(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Detect if a flow has been interrupted and needs recovery
        
        Args:
            session_id: Session ID to check
            
        Returns:
            Dictionary with interruption details if detected, None otherwise
        """
        try:
            session = self.get_session(session_id)
        except SessionNotFoundError:
            return {
                "interrupted": True,
                "reason": "session_not_found",
                "session_id": session_id,
                "recovery_needed": True
            }
        except Exception as e:
            logger.error(f"Error detecting flow interruption for session {session_id}: {e}")
            return {
                "interrupted": True,
                "reason": "detection_error",
                "error": str(e),
                "session_id": session_id,
                "recovery_needed": True
            }
        
        if not session:
            return {
                "interrupted": True,
                "reason": "session_not_found",
                "session_id": session_id,
                "recovery_needed": True
            }
        
        # Check for various interruption indicators
        interruption_details = {
            "interrupted": False,
            "session_id": session_id,
            "current_step": session.current_step,
            "completed_steps": list(session.step_results.keys()),
            "reasons": []
        }
            
        # Check for session timeout (inactive for too long)
        if session.updated_at:
            time_since_update = datetime.now() - session.updated_at
            if time_since_update.total_seconds() > 1800:  # 30 minutes
                interruption_details["interrupted"] = True
                interruption_details["reasons"].append("session_timeout")
                interruption_details["timeout_duration"] = f"{time_since_update.total_seconds() / 60:.1f} minutes"
                interruption_details["last_activity"] = session.updated_at.isoformat()
        
        # Check for incomplete step execution
        if session.current_step and session.current_step not in session.step_results:
            interruption_details["interrupted"] = True
            interruption_details["reasons"].append("incomplete_step_execution")
            interruption_details["incomplete_step"] = session.current_step
        
        # Check for quality gate failures
        if session.quality_scores:
            low_quality_steps = [
                step for step, score in session.quality_scores.items() 
                if score < 0.6
            ]
            if low_quality_steps:
                interruption_details["interrupted"] = True
                interruption_details["reasons"].append("quality_gate_failure")
                interruption_details["low_quality_steps"] = low_quality_steps
        
        # Check for flow state inconsistencies
        expected_steps = self._get_expected_steps_for_flow(session.flow_type)
        completed_steps = list(session.step_results.keys())
        
        # Check for missing prerequisite steps
        missing_prerequisites = []
        for step in completed_steps:
            prerequisites = self._get_step_prerequisites(step)
            for prereq in prerequisites:
                if prereq not in completed_steps:
                    missing_prerequisites.append((step, prereq))
        
        if missing_prerequisites:
            interruption_details["interrupted"] = True
            interruption_details["reasons"].append("missing_prerequisites")
            interruption_details["missing_prerequisites"] = missing_prerequisites
        
        # Check for unexpected step sequence (only if current step is not in completed steps)
        if len(completed_steps) > 0 and session.current_step not in session.step_results:
            last_completed = completed_steps[-1]
            if session.current_step:
                expected_next = self._get_expected_next_step(last_completed, session.flow_type)
                if expected_next and session.current_step != expected_next:
                    interruption_details["interrupted"] = True
                    interruption_details["reasons"].append("unexpected_step_sequence")
                    interruption_details["expected_step"] = expected_next
                    interruption_details["actual_step"] = session.current_step
        
        if interruption_details["interrupted"]:
            interruption_details["recovery_needed"] = True
            interruption_details["recovery_options"] = self._generate_recovery_options(interruption_details)
            logger.warning(f"Flow interruption detected for session {session_id}: {interruption_details['reasons']}")
        
        return interruption_details if interruption_details["interrupted"] else None

    def rollback_to_step(self, session_id: str, target_step: str) -> bool:
        """
        Rollback session state to a specific step
        
        Args:
            session_id: Session ID to rollback
            target_step: Step to rollback to
            
        Returns:
            True if rollback successful, False otherwise
        """
        try:
            session = self.get_session(session_id)
            if not session:
                logger.error(f"Cannot rollback: session {session_id} not found")
                return False
            
            # Validate target step exists in completed steps
            if target_step not in session.step_results:
                logger.error(f"Cannot rollback to step {target_step}: step not found in session {session_id}")
                return False
            
            # Get all steps completed after the target step
            completed_steps = list(session.step_results.keys())
            target_index = completed_steps.index(target_step)
            steps_to_remove = completed_steps[target_index + 1:]
            
            # Remove steps after target step
            for step_to_remove in steps_to_remove:
                if step_to_remove in session.step_results:
                    del session.step_results[step_to_remove]
                if step_to_remove in session.quality_scores:
                    del session.quality_scores[step_to_remove]
            
            # Update session state
            session.current_step = target_step
            session.step_number = target_index + 1
            session.updated_at = datetime.now()
            
            # Add rollback metadata to context
            if "rollback_history" not in session.context:
                session.context["rollback_history"] = []
            
            session.context["rollback_history"].append({
                "timestamp": datetime.now().isoformat(),
                "target_step": target_step,
                "removed_steps": steps_to_remove,
                "reason": "manual_rollback"
            })
            
            # Update in database if available
            if self.db:
                try:
                    self.db.update_session(
                        session_id=session_id,
                        current_step=session.current_step,
                        step_number=session.step_number,
                        configuration={
                            **session.context,
                            "rolled_back": True,
                            "rollback_timestamp": datetime.now().isoformat()
                        }
                    )
                    
                    # Mark removed steps as rolled back in database
                    for step_name in steps_to_remove:
                        step_id = self.db.add_session_step(
                            session_id=session_id,
                            step_name=step_name,
                            step_type="rollback_marker",
                            quality_score=0.0
                        )
                        if step_id:
                            self.db.add_step_result(
                                step_id=step_id,
                                result_type="rollback",
                                content=f"Step {step_name} rolled back to {target_step}",
                                metadata={
                                    "rolled_back": True,
                                    "rollback_timestamp": datetime.now().isoformat(),
                                    "target_step": target_step
                                }
                            )
                except Exception as db_error:
                    logger.error(f"Error updating database during rollback: {db_error}")
                    # Continue with in-memory rollback even if database update fails
            
            logger.info(f"Successfully rolled back session {session_id} to step {target_step}")
            return True
            
        except Exception as e:
            logger.error(f"Error rolling back session {session_id} to step {target_step}: {e}")
            return False

    def create_recovery_checkpoint(self, session_id: str) -> Optional[str]:
        """
        Create a recovery checkpoint for the current session state
        
        Args:
            session_id: Session ID to create checkpoint for
            
        Returns:
            Checkpoint ID if successful, None otherwise
        """
        try:
            session = self.get_session(session_id)
            if not session:
                logger.error(f"Cannot create checkpoint: session {session_id} not found")
                return None
            
            checkpoint_id = f"{session_id}_checkpoint_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Create checkpoint data
            checkpoint_data = {
                "checkpoint_id": checkpoint_id,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "session_state": {
                    "topic": session.topic,
                    "current_step": session.current_step,
                    "flow_type": session.flow_type,
                    "context": session.context.copy(),
                    "step_results": session.step_results.copy(),
                    "quality_scores": session.quality_scores.copy(),
                    "step_number": session.step_number,
                    "status": session.status
                }
            }
            
            # Store checkpoint in session context
            if "checkpoints" not in session.context:
                session.context["checkpoints"] = []
            
            session.context["checkpoints"].append(checkpoint_data)
            
            # Store in database if available
            if self.db:
                try:
                    # Store as a special step result
                    step_id = self.db.add_session_step(
                        session_id=session_id,
                        step_name=f"checkpoint_{checkpoint_id}",
                        step_type="checkpoint",
                        quality_score=1.0
                    )
                    if step_id:
                        self.db.add_step_result(
                            step_id=step_id,
                            result_type="checkpoint",
                            content=f"Recovery checkpoint created: {checkpoint_id}",
                            metadata=checkpoint_data
                        )
                except Exception as db_error:
                    logger.error(f"Error storing checkpoint in database: {db_error}")
                    # Continue with in-memory checkpoint even if database storage fails
            
            logger.info(f"Created recovery checkpoint {checkpoint_id} for session {session_id}")
            return checkpoint_id
            
        except Exception as e:
            logger.error(f"Error creating recovery checkpoint for session {session_id}: {e}")
            return None

    def restore_from_checkpoint(self, session_id: str, checkpoint_id: str) -> bool:
        """
        Restore session state from a recovery checkpoint
        
        Args:
            session_id: Session ID to restore
            checkpoint_id: Checkpoint ID to restore from
            
        Returns:
            True if restore successful, False otherwise
        """
        try:
            session = self.get_session(session_id)
            if not session:
                logger.error(f"Cannot restore checkpoint: session {session_id} not found")
                return False
            
            # Find checkpoint in session context
            checkpoint_data = None
            if "checkpoints" in session.context:
                for checkpoint in session.context["checkpoints"]:
                    if checkpoint["checkpoint_id"] == checkpoint_id:
                        checkpoint_data = checkpoint
                        break
            
            if not checkpoint_data:
                logger.error(f"Checkpoint {checkpoint_id} not found for session {session_id}")
                return False
            
            # Restore session state from checkpoint
            saved_state = checkpoint_data["session_state"]
            session.topic = saved_state["topic"]
            session.current_step = saved_state["current_step"]
            session.flow_type = saved_state["flow_type"]
            session.context = saved_state["context"].copy()
            session.step_results = saved_state["step_results"].copy()
            session.quality_scores = saved_state["quality_scores"].copy()
            session.step_number = saved_state["step_number"]
            session.status = saved_state["status"]
            session.updated_at = datetime.now()
            
            # Add restore metadata
            session.context["restored_from_checkpoint"] = {
                "checkpoint_id": checkpoint_id,
                "restore_timestamp": datetime.now().isoformat(),
                "original_checkpoint_timestamp": checkpoint_data["timestamp"]
            }
            
            # Update in database if available
            if self.db:
                try:
                    self.db.update_session(
                        session_id=session_id,
                        current_step=session.current_step,
                        step_number=session.step_number,
                        configuration={
                            **session.context,
                            "restored_from_checkpoint": True,
                            "restore_timestamp": datetime.now().isoformat()
                        }
                    )
                except Exception as db_error:
                    logger.error(f"Error updating database during checkpoint restore: {db_error}")
                    # Continue with in-memory restore even if database update fails
            
            logger.info(f"Successfully restored session {session_id} from checkpoint {checkpoint_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error restoring session {session_id} from checkpoint {checkpoint_id}: {e}")
            return False

    def _get_expected_steps_for_flow(self, flow_type: str) -> List[str]:
        """Get expected steps for a flow type"""
        flow_steps = {
            "comprehensive_analysis": [
                "decompose_problem",
                "collect_evidence", 
                "multi_perspective_debate",
                "critical_evaluation",
                "bias_detection",
                "innovation_thinking",
                "reflection"
            ],
            "quick_analysis": [
                "simple_decompose",
                "basic_evidence",
                "quick_evaluation",
                "brief_reflection"
            ]
        }
        return flow_steps.get(flow_type, [])

    def _get_step_prerequisites(self, step: str) -> List[str]:
        """Get prerequisite steps for a given step"""
        prerequisites = {
            "collect_evidence": ["decompose_problem"],
            "multi_perspective_debate": ["collect_evidence"],
            "critical_evaluation": ["multi_perspective_debate"],
            "bias_detection": ["critical_evaluation"],
            "innovation_thinking": ["bias_detection"],
            "reflection": ["innovation_thinking"],
            "basic_evidence": ["simple_decompose"],
            "quick_evaluation": ["basic_evidence"],
            "brief_reflection": ["quick_evaluation"]
        }
        return prerequisites.get(step, [])

    def _get_expected_next_step(self, current_step: str, flow_type: str) -> Optional[str]:
        """Get expected next step after current step"""
        expected_steps = self._get_expected_steps_for_flow(flow_type)
        try:
            current_index = expected_steps.index(current_step)
            if current_index + 1 < len(expected_steps):
                return expected_steps[current_index + 1]
        except ValueError:
            pass
        return None

    def _generate_recovery_options(self, interruption_details: Dict[str, Any]) -> List[str]:
        """Generate recovery options based on interruption details"""
        options = []
        reasons = interruption_details.get("reasons", [])
        
        if "session_timeout" in reasons:
            options.extend(["resume_from_last_step", "restart_flow", "create_new_session"])
        
        if "incomplete_step_execution" in reasons:
            options.extend(["retry_current_step", "skip_current_step", "rollback_to_previous"])
        
        if "quality_gate_failure" in reasons:
            options.extend(["improve_quality", "rollback_and_retry", "continue_with_warning"])
        
        if "missing_prerequisites" in reasons:
            options.extend(["execute_missing_steps", "rollback_to_valid_state", "restart_flow"])
        
        if "unexpected_step_sequence" in reasons:
            options.extend(["correct_step_sequence", "rollback_to_expected", "manual_override"])
        
        # Always include basic recovery options
        if not options:
            options = ["retry_current_step", "rollback_to_previous", "restart_flow"]
        
        return list(set(options))  # Remove duplicates

    def repair_session_state(
        self, session_id: str, repair_data: Dict[str, Any]
    ) -> bool:
        """
        Repair corrupted session state
        
        Args:
            session_id: Session ID to repair
            repair_data: Data to use for repair including:
                - current_step: Corrected current step
                - context: Updated context
                - step_results: Corrected step results
                
        Returns:
            True if repair successful, False otherwise
        """
        try:
            # Get existing session
            session = self.get_session(session_id)
            if not session:
                logger.warning(f"Cannot repair non-existent session {session_id}")
                return False

            # Apply repairs
            if "current_step" in repair_data:
                session.current_step = repair_data["current_step"]
                
            if "context" in repair_data:
                session.context.update(repair_data["context"])
                
            if "step_results" in repair_data:
                session.step_results.update(repair_data["step_results"])

            # Update session in database
            success = self.db.update_session(
                session_id=session_id,
                status=session.status,
                configuration={
                    **session.context,
                    "repaired": True,
                    "repair_timestamp": datetime.now().isoformat(),
                }
            )

            if success:
                # Update cached session
                self._active_sessions[session_id] = session
                logger.info(f"Successfully repaired session {session_id}")
                return True
            else:
                logger.error(f"Failed to update repaired session {session_id} in database")
                return False

        except Exception as e:
            logger.error(f"Error repairing session {session_id}: {e}")
            return False
