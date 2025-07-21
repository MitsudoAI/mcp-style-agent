"""
Flow management system for deep thinking processes
Handles the orchestration and state management of thinking flows
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from ..config.exceptions import ConfigurationError, FlowExecutionError, InvalidTransitionError
from ..data.database import ThinkingDatabase

logger = logging.getLogger(__name__)


class FlowStepStatus(str, Enum):
    """Status of a flow step"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class FlowStatus(str, Enum):
    """Status of a flow"""

    INITIALIZED = "initialized"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class FlowStep:
    """Represents a single step in a thinking flow"""

    def __init__(
        self,
        step_id: str,
        step_name: str,
        step_type: str,
        template_name: str,
        dependencies: List[str] = None,
    ):
        self.step_id = step_id
        self.step_name = step_name
        self.step_type = step_type
        self.template_name = template_name
        self.dependencies = dependencies or []
        self.status = FlowStepStatus.PENDING
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.result: Optional[str] = None
        self.error_message: Optional[str] = None
        self.quality_score: Optional[float] = None
        self.retry_count = 0
        self.max_retries = 3

    def start(self):
        """Mark step as started"""
        self.status = FlowStepStatus.IN_PROGRESS
        self.start_time = datetime.now()

    def complete(self, result: str, quality_score: Optional[float] = None):
        """Mark step as completed"""
        self.status = FlowStepStatus.COMPLETED
        self.end_time = datetime.now()
        self.result = result
        self.quality_score = quality_score

    def fail(self, error_message: str):
        """Mark step as failed"""
        self.status = FlowStepStatus.FAILED
        self.end_time = datetime.now()
        self.error_message = error_message
        self.retry_count += 1

    def can_retry(self) -> bool:
        """Check if step can be retried"""
        return (
            self.retry_count < self.max_retries and self.status == FlowStepStatus.FAILED
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert step to dictionary"""
        return {
            "step_id": self.step_id,
            "step_name": self.step_name,
            "step_type": self.step_type,
            "template_name": self.template_name,
            "dependencies": self.dependencies,
            "status": self.status.value,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "result": self.result,
            "error_message": self.error_message,
            "quality_score": self.quality_score,
            "retry_count": self.retry_count,
        }


class ThinkingFlow:
    """Represents a complete thinking flow with state management"""

    def __init__(self, flow_id: str, flow_name: str, session_id: str):
        self.flow_id = flow_id
        self.flow_name = flow_name
        self.session_id = session_id
        self.status = FlowStatus.INITIALIZED
        self.steps: Dict[str, FlowStep] = {}
        self.step_order: List[str] = []
        self.current_step_index = 0
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.context: Dict[str, Any] = {}

    def add_step(self, step: FlowStep):
        """Add a step to the flow"""
        self.steps[step.step_id] = step
        self.step_order.append(step.step_id)

    def start(self):
        """Start the flow"""
        self.status = FlowStatus.RUNNING
        self.start_time = datetime.now()
        logger.info(f"Started thinking flow {self.flow_id}")

    def pause(self):
        """Pause the flow"""
        if self.status == FlowStatus.RUNNING:
            self.status = FlowStatus.PAUSED
            logger.info(f"Paused thinking flow {self.flow_id}")

    def resume(self):
        """Resume the flow"""
        if self.status == FlowStatus.PAUSED:
            self.status = FlowStatus.RUNNING
            logger.info(f"Resumed thinking flow {self.flow_id}")

    def complete(self):
        """Complete the flow"""
        self.status = FlowStatus.COMPLETED
        self.end_time = datetime.now()
        logger.info(f"Completed thinking flow {self.flow_id}")

    def fail(self, error_message: str):
        """Fail the flow"""
        self.status = FlowStatus.FAILED
        self.end_time = datetime.now()
        logger.error(f"Failed thinking flow {self.flow_id}: {error_message}")

    def get_current_step(self) -> Optional[FlowStep]:
        """Get the current step"""
        if self.current_step_index < len(self.step_order):
            step_id = self.step_order[self.current_step_index]
            return self.steps[step_id]
        return None

    def get_next_step(self) -> Optional[FlowStep]:
        """Get the next step to execute"""
        for i in range(self.current_step_index, len(self.step_order)):
            step_id = self.step_order[i]
            step = self.steps[step_id]

            if step.status == FlowStepStatus.PENDING:
                if self._check_dependencies(step):
                    return step
                else:
                    break
            elif step.status == FlowStepStatus.FAILED and step.can_retry():
                return step

        return None

    def advance_step(self):
        """Advance to the next step"""
        self.current_step_index += 1

    def _check_dependencies(self, step: FlowStep) -> bool:
        """Check if step dependencies are satisfied"""
        for dep_id in step.dependencies:
            if dep_id in self.steps:
                dep_step = self.steps[dep_id]
                if dep_step.status != FlowStepStatus.COMPLETED:
                    return False
            else:
                logger.warning(f"Dependency {dep_id} not found for step {step.step_id}")
                return False
        return True

    def get_progress(self) -> Dict[str, Any]:
        """Get flow progress information"""
        completed_steps = sum(
            1 for step in self.steps.values() if step.status == FlowStepStatus.COMPLETED
        )
        failed_steps = sum(
            1 for step in self.steps.values() if step.status == FlowStepStatus.FAILED
        )
        total_steps = len(self.steps)

        return {
            "flow_id": self.flow_id,
            "status": self.status.value,
            "total_steps": total_steps,
            "completed_steps": completed_steps,
            "failed_steps": failed_steps,
            "progress_percentage": (
                (completed_steps / total_steps * 100) if total_steps > 0 else 0
            ),
            "current_step_index": self.current_step_index,
            "current_step": (
                self.get_current_step().step_name if self.get_current_step() else None
            ),
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "duration_seconds": (
                (datetime.now() - self.start_time).total_seconds()
                if self.start_time
                else 0
            ),
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert flow to dictionary"""
        return {
            "flow_id": self.flow_id,
            "flow_name": self.flow_name,
            "session_id": self.session_id,
            "status": self.status.value,
            "steps": {step_id: step.to_dict() for step_id, step in self.steps.items()},
            "step_order": self.step_order,
            "current_step_index": self.current_step_index,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "context": self.context,
            "progress": self.get_progress(),
        }


class FlowManager:
    """
    Manages thinking flows and their state transitions
    Provides flow orchestration and state tracking
    """

    def __init__(self, db: Optional[ThinkingDatabase] = None):
        self.active_flows: Dict[str, ThinkingFlow] = {}
        self.flow_definitions: Dict[str, Dict[str, Any]] = {}
        self.db = db
        self._load_default_flows()
        
        # Initialize state machine if database is provided
        from .flow_state_machine import FlowStateMachine
        self.state_machine = FlowStateMachine(db)
        
        logger.info("FlowManager initialized")

    def _load_default_flows(self):
        """Load default flow definitions"""

        # Comprehensive analysis flow
        comprehensive_flow = {
            "name": "comprehensive_analysis",
            "description": "Complete deep thinking analysis flow",
            "steps": [
                {
                    "step_id": "decompose",
                    "step_name": "Problem Decomposition",
                    "step_type": "analysis",
                    "template_name": "decomposition",
                    "dependencies": [],
                },
                {
                    "step_id": "collect_evidence",
                    "step_name": "Evidence Collection",
                    "step_type": "research",
                    "template_name": "evidence_collection",
                    "dependencies": ["decompose"],
                },
                {
                    "step_id": "evaluate",
                    "step_name": "Critical Evaluation",
                    "step_type": "assessment",
                    "template_name": "critical_evaluation",
                    "dependencies": ["collect_evidence"],
                },
                {
                    "step_id": "reflect",
                    "step_name": "Reflection",
                    "step_type": "metacognition",
                    "template_name": "reflection",
                    "dependencies": ["evaluate"],
                },
            ],
        }

        # Quick analysis flow
        quick_flow = {
            "name": "quick_analysis",
            "description": "Fast analysis for simple problems",
            "steps": [
                {
                    "step_id": "simple_decompose",
                    "step_name": "Simple Problem Analysis",
                    "step_type": "analysis",
                    "template_name": "decomposition",
                    "dependencies": [],
                },
                {
                    "step_id": "basic_evaluate",
                    "step_name": "Basic Evaluation",
                    "step_type": "assessment",
                    "template_name": "critical_evaluation",
                    "dependencies": ["simple_decompose"],
                },
            ],
        }

        self.flow_definitions["comprehensive_analysis"] = comprehensive_flow
        self.flow_definitions["quick_analysis"] = quick_flow

    def create_flow(
        self, session_id: str, flow_type: str = "comprehensive_analysis"
    ) -> str:
        """Create a new thinking flow"""
        if flow_type not in self.flow_definitions:
            raise ConfigurationError(f"Unknown flow type: {flow_type}")

        flow_def = self.flow_definitions[flow_type]
        flow_id = f"{session_id}_{flow_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Create flow
        flow = ThinkingFlow(flow_id, flow_def["name"], session_id)

        # Add steps
        for step_def in flow_def["steps"]:
            step = FlowStep(
                step_id=step_def["step_id"],
                step_name=step_def["step_name"],
                step_type=step_def["step_type"],
                template_name=step_def["template_name"],
                dependencies=step_def.get("dependencies", []),
            )
            flow.add_step(step)

        # Store flow
        self.active_flows[flow_id] = flow

        logger.info(f"Created flow {flow_id} of type {flow_type}")
        return flow_id

    def get_flow(self, flow_id: str) -> Optional[ThinkingFlow]:
        """Get a flow by ID"""
        return self.active_flows.get(flow_id)

    def start_flow(self, flow_id: str):
        """Start a flow"""
        flow = self.get_flow(flow_id)
        if not flow:
            raise FlowExecutionError(f"Flow not found: {flow_id}")

        # Use state machine to transition flow to running state
        from .flow_state_machine import FlowEvent
        try:
            new_state, success = self.state_machine.transition(flow, FlowEvent.START)
            if not success:
                logger.warning(f"Failed to start flow {flow_id}")
        except InvalidTransitionError as e:
            logger.error(f"Invalid transition when starting flow {flow_id}: {e}")
            flow.start()  # Fallback to direct method if transition fails

    def get_next_step_in_flow(self, flow_id: str) -> Optional[FlowStep]:
        """Get the next step to execute in a flow"""
        flow = self.get_flow(flow_id)
        if not flow:
            raise FlowExecutionError(f"Flow not found: {flow_id}")

        return flow.get_next_step()

    def complete_step(
        self,
        flow_id: str,
        step_id: str,
        result: str,
        quality_score: Optional[float] = None,
    ):
        """Mark a step as completed"""
        flow = self.get_flow(flow_id)
        if not flow:
            raise FlowExecutionError(f"Flow not found: {flow_id}")

        if step_id not in flow.steps:
            raise FlowExecutionError(f"Step not found: {step_id}")

        # Use state machine to handle step completion
        from .flow_state_machine import FlowEvent
        try:
            metadata = {
                "step_id": step_id,
                "result": result,
                "quality_score": quality_score
            }
            new_state, success = self.state_machine.transition(flow, FlowEvent.COMPLETE_STEP, metadata)
            if not success:
                logger.warning(f"Failed to complete step {step_id} in flow {flow_id}")
                # Fallback to direct method
                step = flow.steps[step_id]
                step.complete(result, quality_score)
        except InvalidTransitionError as e:
            logger.error(f"Invalid transition when completing step {step_id} in flow {flow_id}: {e}")
            # Fallback to direct method
            step = flow.steps[step_id]
            step.complete(result, quality_score)
            
            # Check if flow is complete
            if all(
                step.status in [FlowStepStatus.COMPLETED, FlowStepStatus.SKIPPED]
                for step in flow.steps.values()
            ):
                flow.complete()

        logger.info(f"Completed step {step_id} in flow {flow_id}")

    def fail_step(self, flow_id: str, step_id: str, error_message: str, critical: bool = False):
        """Mark a step as failed"""
        flow = self.get_flow(flow_id)
        if not flow:
            raise FlowExecutionError(f"Flow not found: {flow_id}")

        if step_id not in flow.steps:
            raise FlowExecutionError(f"Step not found: {step_id}")

        # Use state machine to handle step failure
        from .flow_state_machine import FlowEvent
        try:
            metadata = {
                "step_id": step_id,
                "error_message": error_message,
                "critical": critical
            }
            new_state, success = self.state_machine.transition(flow, FlowEvent.FAIL_STEP, metadata)
            if not success:
                logger.warning(f"Failed to mark step {step_id} as failed in flow {flow_id}")
                # Fallback to direct method
                step = flow.steps[step_id]
                step.fail(error_message)
        except InvalidTransitionError as e:
            logger.error(f"Invalid transition when failing step {step_id} in flow {flow_id}: {e}")
            # Fallback to direct method
            step = flow.steps[step_id]
            step.fail(error_message)

        logger.warning(f"Failed step {step_id} in flow {flow_id}: {error_message}")

    def pause_flow(self, flow_id: str):
        """Pause a flow"""
        flow = self.get_flow(flow_id)
        if not flow:
            logger.warning(f"Flow not found when trying to pause: {flow_id}")
            return

        # Use state machine to handle flow pause
        from .flow_state_machine import FlowEvent
        try:
            new_state, success = self.state_machine.transition(flow, FlowEvent.PAUSE)
            if not success:
                logger.warning(f"Failed to pause flow {flow_id}")
                # Fallback to direct method
                flow.pause()
        except InvalidTransitionError as e:
            logger.error(f"Invalid transition when pausing flow {flow_id}: {e}")
            # Fallback to direct method if in valid state
            if flow.status == FlowStatus.RUNNING:
                flow.pause()

    def resume_flow(self, flow_id: str):
        """Resume a flow"""
        flow = self.get_flow(flow_id)
        if not flow:
            logger.warning(f"Flow not found when trying to resume: {flow_id}")
            return

        # Use state machine to handle flow resume
        from .flow_state_machine import FlowEvent
        try:
            new_state, success = self.state_machine.transition(flow, FlowEvent.RESUME)
            if not success:
                logger.warning(f"Failed to resume flow {flow_id}")
                # Fallback to direct method
                flow.resume()
        except InvalidTransitionError as e:
            logger.error(f"Invalid transition when resuming flow {flow_id}: {e}")
            # Fallback to direct method if in valid state
            if flow.status == FlowStatus.PAUSED:
                flow.resume()

    def get_flow_progress(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """Get flow progress"""
        flow = self.get_flow(flow_id)
        if not flow:
            return None
            
        # Use state machine to get detailed flow state summary
        try:
            return self.state_machine.get_flow_state_summary(flow)
        except Exception as e:
            logger.error(f"Error getting flow state summary for {flow_id}: {e}")
            # Fallback to basic progress info
            return flow.get_progress()

    def list_active_flows(
        self, session_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List active flows"""
        flows = []
        for flow in self.active_flows.values():
            if session_id is None or flow.session_id == session_id:
                flows.append(flow.get_progress())
        return flows

    def get_flow_statistics(self) -> Dict[str, Any]:
        """Get flow management statistics"""
        status_counts = {}
        for flow in self.active_flows.values():
            status = flow.status.value
            status_counts[status] = status_counts.get(status, 0) + 1

        return {
            "total_flows": len(self.active_flows),
            "status_distribution": status_counts,
            "available_flow_types": list(self.flow_definitions.keys()),
        }

    def list_flows(self) -> List[str]:
        """List available flow types"""
        return list(self.flow_definitions.keys())

    def get_flow_info(self, flow_type: str) -> Optional[Dict[str, Any]]:
        """Get information about a flow type"""
        if flow_type not in self.flow_definitions:
            return None

        flow_def = self.flow_definitions[flow_type]
        return {
            "name": flow_def["name"],
            "description": flow_def["description"],
            "total_steps": len(flow_def["steps"]),
            "steps": flow_def["steps"],
        }

    def get_next_step(
        self, flow_type: str, current_step: str, step_result: str
    ) -> Optional[Dict[str, Any]]:
        """Get next step information for a flow type"""
        if flow_type not in self.flow_definitions:
            return None

        flow_def = self.flow_definitions[flow_type]
        steps = flow_def["steps"]

        # Find current step index - handle different step name formats
        current_index = -1
        for i, step in enumerate(steps):
            step_id = step["step_id"]
            step_name = step["step_name"]

            # Check various formats: step_id, step_name, or partial matches
            if (
                step_id == current_step
                or step_name == current_step
                or current_step == "decompose_problem"
                and step_id == "decompose"
                or current_step == "collect_evidence"
                and step_id == "collect_evidence"
                or current_step == "critical_evaluation"
                and step_id == "evaluate"
            ):
                current_index = i
                break

        # Return next step if available
        if current_index >= 0 and current_index + 1 < len(steps):
            next_step = steps[current_index + 1]
            return {
                "step_name": next_step["step_id"],
                "template_name": next_step["template_name"],
                "instructions": f"Execute {next_step['step_name']} step",
            }

        return None

    def get_total_steps(self, flow_type: str) -> int:
        """Get total number of steps in a flow type"""
        if flow_type not in self.flow_definitions:
            return 0
        return len(self.flow_definitions[flow_type]["steps"])
        
    def reset_flow(self, flow_id: str) -> bool:
        """Reset a flow to its initial state"""
        flow = self.get_flow(flow_id)
        if not flow:
            logger.warning(f"Flow not found when trying to reset: {flow_id}")
            return False
            
        # Use state machine to reset the flow
        try:
            return self.state_machine.reset_flow(flow)
        except Exception as e:
            logger.error(f"Error resetting flow {flow_id}: {e}")
            return False
            
    def get_flow_state_history(self, flow_id: str) -> List[Dict[str, Any]]:
        """Get state transition history for a flow"""
        flow = self.get_flow(flow_id)
        if not flow:
            logger.warning(f"Flow not found when trying to get history: {flow_id}")
            return []
            
        return self.state_machine.get_state_history(flow_id)
        
    def get_valid_transitions(self, flow_id: str) -> List[str]:
        """Get valid transitions for a flow's current state"""
        flow = self.get_flow(flow_id)
        if not flow:
            logger.warning(f"Flow not found when trying to get valid transitions: {flow_id}")
            return []
            
        from .flow_state_machine import FlowEvent
        transitions = self.state_machine.get_valid_transitions(flow)
        return [event.value for event in transitions.keys()]
        
    def restore_flow(self, flow_id: str, session_id: str) -> Optional[str]:
        """
        Restore a flow from database
        
        Args:
            flow_id: Flow identifier
            session_id: Session identifier
            
        Returns:
            Flow ID if successful, None otherwise
        """
        if not self.db:
            logger.warning("Cannot restore flow without database")
            return None
            
        try:
            # Restore flow state from database
            flow = self.state_machine.restore_flow_state(flow_id, session_id)
            if not flow:
                logger.warning(f"Failed to restore flow {flow_id}")
                return None
                
            # Add to active flows
            self.active_flows[flow_id] = flow
            logger.info(f"Restored flow {flow_id}")
            return flow_id
            
        except Exception as e:
            logger.error(f"Error restoring flow {flow_id}: {e}")
            return None
