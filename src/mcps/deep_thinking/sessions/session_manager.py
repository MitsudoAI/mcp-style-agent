"""
Session Manager for Deep Thinking Engine
Provides high-level interface for session management with local storage
"""

import uuid
import time
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import logging

from ..data.database import ThinkingDatabase
from ..models.mcp_models import SessionState, MCPToolOutput
from ..config.exceptions import SessionNotFoundError, SessionStateError

logger = logging.getLogger(__name__)


class SessionManager:
    """
    High-level session management for thinking processes
    Handles session lifecycle, state tracking, and persistence
    """
    
    def __init__(self, db_path: Optional[str] = None, encryption_key: Optional[bytes] = None):
        # Use default path in user's data directory
        if db_path is None:
            data_dir = Path.home() / ".deep_thinking"
            data_dir.mkdir(exist_ok=True)
            db_path = str(data_dir / "sessions.db")
        
        self.db = ThinkingDatabase(db_path, encryption_key)
        self._active_sessions = {}  # In-memory cache for active sessions
        logger.info(f"SessionManager initialized with database: {db_path}")
    
    def create_session(self, topic: str, complexity: str = "moderate", 
                      flow_type: str = "comprehensive_analysis",
                      user_id: Optional[str] = None) -> str:
        """
        Create a new thinking session
        
        Args:
            topic: The main topic or question to analyze
            complexity: Complexity level (simple, moderate, complex)
            flow_type: Type of thinking flow to use
            user_id: Optional user identifier
            
        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())
        
        # Create session configuration
        configuration = {
            "complexity": complexity,
            "flow_type": flow_type,
            "created_by": user_id,
            "settings": {
                "quality_threshold": 0.8 if complexity == "complex" else 0.7,
                "max_steps": 20 if complexity == "complex" else 15,
                "enable_bias_detection": True,
                "enable_innovation_thinking": complexity in ["moderate", "complex"]
            }
        }
        
        # Store in database
        success = self.db.create_session(
            session_id=session_id,
            topic=topic,
            session_type=flow_type,
            user_id=user_id,
            configuration=configuration
        )
        
        if not success:
            raise SessionStateError(f"Failed to create session for topic: {topic}")
        
        # Create in-memory session state
        session_state = SessionState(
            session_id=session_id,
            topic=topic,
            current_step="initialize",
            step_number=0,
            flow_type=flow_type,
            status="active"
        )
        
        self._active_sessions[session_id] = session_state
        
        logger.info(f"Created session {session_id} for topic: {topic[:50]}...")
        return session_id
    
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
        session_state = SessionState(
            session_id=session_data['id'],
            topic=session_data['topic'],
            current_step=session_data['current_step'],
            step_number=session_data['step_number'],
            flow_type=session_data['flow_type'],
            status=session_data['status'],
            step_results=session_data.get('context', {}).get('step_results', {}),
            context=session_data.get('context', {}),
            quality_scores=session_data.get('quality_metrics', {}),
            created_at=datetime.fromisoformat(session_data['created_at']),
            updated_at=datetime.fromisoformat(session_data['updated_at'])
        )
        
        # Cache if active
        if session_state.status == "active":
            self._active_sessions[session_id] = session_state
        
        return session_state
    
    def update_session_step(self, session_id: str, step_name: str, 
                           step_result: Optional[str] = None,
                           quality_score: Optional[float] = None,
                           execution_time_ms: Optional[int] = None) -> bool:
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
            step_id = self.db.add_session_step(
                session_id=session_id,
                step_name=step_name,
                step_number=session.step_number,
                step_type=self._determine_step_type(step_name),
                input_data={"step_result": step_result} if step_result else None,
                quality_score=quality_score,
                execution_time_ms=execution_time_ms
            )
            
            # Update session in database
            self.db.update_session(
                session_id,
                current_step=step_name,
                step_number=session.step_number,
                context=session.context,
                quality_metrics=session.quality_scores
            )
            
            # Update cache
            self._active_sessions[session_id] = session
            
            logger.info(f"Updated session {session_id} to step {step_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating session {session_id}: {e}")
            return False
    
    def add_step_result(self, session_id: str, step_name: str, 
                       result_content: str, result_type: str = "output",
                       metadata: Optional[Dict[str, Any]] = None,
                       quality_indicators: Optional[Dict[str, Any]] = None,
                       citations: Optional[List[Dict[str, Any]]] = None) -> bool:
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
            # Get the step ID
            steps = self.db.get_session_steps(session_id)
            step_id = None
            for step in steps:
                if step['step_name'] == step_name:
                    step_id = step['id']
                    break
            
            if step_id is None:
                logger.warning(f"Step {step_name} not found for session {session_id}")
                return False
            
            # Add result to database
            result_id = self.db.add_step_result(
                session_id=session_id,
                step_id=step_id,
                result_type=result_type,
                content=result_content,
                metadata=metadata,
                quality_indicators=quality_indicators,
                citations=citations
            )
            
            return result_id is not None
            
        except Exception as e:
            logger.error(f"Error adding result to session {session_id}: {e}")
            return False
    
    def complete_session(self, session_id: str, final_results: Optional[Dict[str, Any]] = None) -> bool:
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
                "completed_at": datetime.now().isoformat()
            }
            
            if final_results:
                updates["quality_metrics"] = {
                    **session.quality_scores,
                    "final_results": final_results
                }
            
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
                step_id = result['step_id']
                if step_id not in step_results:
                    step_results[step_id] = []
                step_results[step_id].append(result)
            
            # Combine steps with their results
            detailed_steps = []
            for step in steps:
                step_data = dict(step)
                step_data['results'] = step_results.get(step['id'], [])
                detailed_steps.append(step_data)
            
            return {
                "session": session.dict(),
                "steps": detailed_steps,
                "summary": {
                    "total_steps": len(steps),
                    "total_results": len(results),
                    "average_quality": sum(session.quality_scores.values()) / len(session.quality_scores) if session.quality_scores else 0,
                    "duration": (session.updated_at - session.created_at).total_seconds() if session.updated_at else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting session history {session_id}: {e}")
            return {}
    
    def list_user_sessions(self, user_id: Optional[str] = None, 
                          status: Optional[str] = None,
                          limit: int = 50) -> List[Dict[str, Any]]:
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
                "completed_steps": [step['step_name'] for step in steps],
                "step_results": session.step_results,
                "quality_scores": session.quality_scores,
                "progress": f"{len(steps)}/{self._get_expected_steps(session.flow_type)}",
                "session_duration": (datetime.now() - session.created_at).total_seconds() / 60  # minutes
            }
            
            # Add recent step results for context
            if steps:
                recent_steps = steps[-3:]  # Last 3 steps
                context["recent_steps"] = [
                    {
                        "name": step['step_name'],
                        "result": session.step_results.get(step['step_name'], ""),
                        "quality": session.quality_scores.get(step['step_name'])
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
                s for s in all_sessions 
                if datetime.fromisoformat(s['updated_at']) < cutoff_time
            ]
            
            cleaned_count = 0
            for session in inactive_sessions:
                # Mark as abandoned rather than delete
                self.db.update_session(session['id'], status="abandoned")
                self._active_sessions.pop(session['id'], None)
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
                "encryption_enabled": self.db.encryption is not None
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}
    
    def _determine_step_type(self, step_name: str) -> str:
        """Determine step type from step name"""
        step_type_mapping = {
            "decompose": "analysis",
            "evidence": "research", 
            "debate": "reasoning",
            "evaluate": "assessment",
            "bias": "validation",
            "innovation": "creativity",
            "reflect": "metacognition"
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
            "critical_evaluation": 10
        }
        return flow_steps.get(flow_type, 10)