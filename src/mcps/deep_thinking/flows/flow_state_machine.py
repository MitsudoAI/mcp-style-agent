"""
Flow State Machine for Deep Thinking Engine
Implements a state machine for managing thinking flow states and transitions

This module provides a robust state machine implementation for managing the lifecycle
of thinking flows. It handles state transitions, validation, persistence, and recovery.
The state machine ensures that flows follow valid state transitions and maintains a
complete history of state changes for auditing and debugging purposes.
"""

import json
import logging
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from ..config.exceptions import FlowStateError, InvalidTransitionError
from ..data.database import ThinkingDatabase
from .flow_manager import FlowStatus, ThinkingFlow
from ..models.thinking_models import FlowStep, FlowStepStatus

logger = logging.getLogger(__name__)


class FlowEvent(str, Enum):
    """
    Events that can trigger state transitions in the flow state machine

    These events represent all possible triggers that can cause a flow to change state.
    Each event corresponds to a specific action or condition in the flow lifecycle.
    """

    # Core flow lifecycle events
    START = "start"  # Start a flow
    COMPLETE = "complete"  # Complete the entire flow
    PAUSE = "pause"  # Pause a running flow
    RESUME = "resume"  # Resume a paused flow
    RESET = "reset"  # Reset a flow to initial state
    CANCEL = "cancel"  # Cancel a flow
    TIMEOUT = "timeout"  # Flow timed out

    # Step-related events
    COMPLETE_STEP = "complete_step"  # Complete a specific step
    FAIL_STEP = "fail_step"  # Fail a specific step
    RETRY_STEP = "retry_step"  # Retry a failed step
    SKIP_STEP = "skip_step"  # Skip a step

    # Quality control events
    QUALITY_CHECK_PASS = "quality_check_pass"  # Quality check passed
    QUALITY_CHECK_FAIL = "quality_check_fail"  # Quality check failed

    # Special events
    MANUAL_OVERRIDE = "manual_override"  # Manual state override
    ERROR = "error"  # Unhandled error occurred
    RECOVER = "recover"  # Recover from error state


class FlowStateMachine:
    """
    State machine for managing thinking flow states and transitions

    This class implements a robust state machine that manages the lifecycle of thinking flows.
    It handles state transitions, validation, persistence, and recovery. The state machine
    ensures that flows follow valid state transitions and maintains a complete history of
    state changes for auditing and debugging purposes.

    Key features:
    - Validates state transitions based on a predefined transition map
    - Records complete state transition history
    - Persists flow state to database for recovery
    - Supports flow pause, resume, and reset operations
    - Provides detailed flow state summaries and diagnostics
    """

    def __init__(self, db: Optional[ThinkingDatabase] = None):
        """
        Initialize the flow state machine

        Args:
            db: Optional database for state persistence. If provided, the state machine
                will persist flow states to the database for recovery.
        """
        self.db = db
        self._valid_transitions = self._build_transition_map()
        self._state_history: Dict[str, List[Dict[str, Any]]] = {}
        self._paused_flows: Dict[str, datetime] = {}  # Track when flows were paused
        self._auto_recovery_enabled = (
            True  # Enable automatic recovery of interrupted flows
        )
        self._max_retry_attempts = (
            3  # Maximum number of retry attempts for failed steps
        )
        logger.info(
            "FlowStateMachine initialized with persistence: %s",
            "enabled" if db else "disabled",
        )

    def _build_transition_map(self) -> Dict[FlowStatus, Dict[FlowEvent, FlowStatus]]:
        """
        Build the state transition map

        This method defines all valid state transitions for the flow state machine.
        Each entry maps a current state to a dictionary of events and their target states.

        Returns:
            Dictionary mapping current states to valid transitions
        """
        transitions = {
            FlowStatus.INITIALIZED: {
                FlowEvent.START: FlowStatus.RUNNING,
                FlowEvent.CANCEL: FlowStatus.CANCELLED,
                FlowEvent.MANUAL_OVERRIDE: FlowStatus.INITIALIZED,  # Allow configuration changes
            },
            FlowStatus.RUNNING: {
                # Step-related events (stay in running state)
                FlowEvent.COMPLETE_STEP: FlowStatus.RUNNING,
                FlowEvent.FAIL_STEP: FlowStatus.RUNNING,
                FlowEvent.RETRY_STEP: FlowStatus.RUNNING,
                FlowEvent.SKIP_STEP: FlowStatus.RUNNING,
                # Flow lifecycle events
                FlowEvent.COMPLETE: FlowStatus.COMPLETED,
                FlowEvent.PAUSE: FlowStatus.PAUSED,
                FlowEvent.CANCEL: FlowStatus.CANCELLED,
                FlowEvent.TIMEOUT: FlowStatus.PAUSED,
                FlowEvent.ERROR: FlowStatus.FAILED,
                # Quality control events (stay in running state)
                FlowEvent.QUALITY_CHECK_FAIL: FlowStatus.RUNNING,
                FlowEvent.QUALITY_CHECK_PASS: FlowStatus.RUNNING,
                # Special events
                FlowEvent.MANUAL_OVERRIDE: FlowStatus.RUNNING,
            },
            FlowStatus.PAUSED: {
                FlowEvent.RESUME: FlowStatus.RUNNING,
                FlowEvent.CANCEL: FlowStatus.CANCELLED,
                FlowEvent.RESET: FlowStatus.INITIALIZED,
                FlowEvent.TIMEOUT: FlowStatus.FAILED,  # Long pause can lead to failure
                FlowEvent.MANUAL_OVERRIDE: FlowStatus.PAUSED,  # Allow configuration while paused
            },
            FlowStatus.COMPLETED: {
                FlowEvent.RESET: FlowStatus.INITIALIZED,
                FlowEvent.MANUAL_OVERRIDE: FlowStatus.COMPLETED,  # Allow metadata updates
            },
            FlowStatus.FAILED: {
                FlowEvent.RESET: FlowStatus.INITIALIZED,
                FlowEvent.RECOVER: FlowStatus.RUNNING,  # Allow recovery from failure
                FlowEvent.MANUAL_OVERRIDE: FlowStatus.FAILED,  # Allow diagnostics
            },
            FlowStatus.CANCELLED: {
                FlowEvent.RESET: FlowStatus.INITIALIZED,
                FlowEvent.MANUAL_OVERRIDE: FlowStatus.CANCELLED,  # Allow inspection
            },
        }
        return transitions

    def transition(
        self,
        flow: ThinkingFlow,
        event: FlowEvent,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Tuple[FlowStatus, bool]:
        """
        Transition a flow to a new state based on an event

        This method handles the core state transition logic. It validates the transition,
        updates the flow state, records the state change in history, performs any
        state-specific actions, and persists the state if a database is available.

        Args:
            flow: The flow to transition
            event: The event triggering the transition
            metadata: Optional metadata about the transition

        Returns:
            Tuple of (new_state, success)

        Raises:
            InvalidTransitionError: If the transition is not valid
            FlowStateError: If there's an error performing state actions
        """
        if not flow:
            raise ValueError("Cannot transition a null flow")

        current_state = flow.status
        metadata = metadata or {}

        # Add timestamp to metadata if not present
        if "timestamp" not in metadata:
            metadata["timestamp"] = datetime.now().isoformat()

        # Check if transition is valid
        if (
            current_state not in self._valid_transitions
            or event not in self._valid_transitions[current_state]
        ):
            # Handle special cases
            if (
                event == FlowEvent.MANUAL_OVERRIDE
                and metadata
                and "target_state" in metadata
            ):
                # Special case for manual override with explicit target state
                target_state = metadata["target_state"]
                if isinstance(target_state, str):
                    target_state = FlowStatus(target_state)
                logger.warning(
                    f"Manual override: Forcing flow {flow.flow_id} from {current_state} to {target_state}"
                )

                # Update flow status directly for manual override
                flow.status = target_state

                # Add metadata
                metadata["forced"] = True
                metadata["reason"] = metadata.get("reason", "Manual override")

                # Record the state change
                self._record_state_change(
                    flow.flow_id, current_state, target_state, event, metadata
                )

                # Persist if database is available
                if self.db:
                    self._persist_state(flow)

                # Return the target state and success
                return target_state, True
            elif event == FlowEvent.ERROR:
                # Special case for error events - always allow transition to FAILED
                logger.error(
                    f"Error in flow {flow.flow_id}: {metadata.get('error_message', 'Unknown error')}"
                )
                new_state = FlowStatus.FAILED
                metadata["error_time"] = datetime.now().isoformat()
            else:
                # Invalid transition
                error_msg = f"Invalid transition: {current_state} -> {event}"
                logger.error(f"{error_msg} for flow {flow.flow_id}")
                raise InvalidTransitionError(
                    error_msg,
                    flow_id=flow.flow_id,
                    current_state=current_state.value,
                    event=event.value,
                )
        else:
            # Get new state from transition map
            new_state = self._valid_transitions[current_state][event]

        try:
            # Record state change in history before actually changing state
            # This ensures we capture the intent even if the action fails
            self._record_state_change(
                flow.flow_id, current_state, new_state, event, metadata
            )

            # Update flow state
            previous_state = flow.status
            flow.status = new_state

            # Track pause time for timeout management
            if new_state == FlowStatus.PAUSED:
                self._paused_flows[flow.flow_id] = datetime.now()
            elif flow.flow_id in self._paused_flows and new_state != FlowStatus.PAUSED:
                self._paused_flows.pop(flow.flow_id, None)

            # Perform state-specific actions
            success = self._perform_state_actions(flow, event, new_state, metadata)

            # If actions failed but didn't raise an exception, log warning
            if not success:
                logger.warning(
                    f"State actions partially failed for flow {flow.flow_id} "
                    f"transition {current_state} -> {new_state} via {event}"
                )

            # Persist state if database is available
            if self.db:
                persist_success = self._persist_state(flow)
                if not persist_success:
                    logger.warning(f"Failed to persist state for flow {flow.flow_id}")

            logger.info(
                f"Flow {flow.flow_id} transitioned: {current_state} -> {new_state} via {event}"
            )

            return new_state, success

        except Exception as e:
            # Revert state change if an exception occurs during action execution
            logger.error(
                f"Error during state transition for flow {flow.flow_id}: {e}. "
                f"Reverting from {new_state} back to {current_state}"
            )
            flow.status = current_state

            # Record the failed transition attempt
            self._record_state_change(
                flow.flow_id,
                current_state,
                current_state,  # Reverted back to original state
                event,
                {**metadata, "error": str(e), "failed_transition": True},
            )

            # Re-raise as FlowStateError
            raise FlowStateError(
                f"Failed to transition flow {flow.flow_id} from {current_state} to {new_state}: {e}",
                flow_id=flow.flow_id,
                current_state=current_state.value,
            ) from e

    def _record_state_change(
        self,
        flow_id: str,
        from_state: FlowStatus,
        to_state: FlowStatus,
        event: FlowEvent,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Record a state change in the history

        This method maintains a complete history of all state transitions for auditing,
        debugging, and recovery purposes. Each state change is recorded with timestamp,
        from/to states, triggering event, and any associated metadata.

        Args:
            flow_id: Flow identifier
            from_state: Previous state
            to_state: New state
            event: Event that triggered the transition
            metadata: Optional metadata about the transition
        """
        if flow_id not in self._state_history:
            self._state_history[flow_id] = []

        # Create a copy of metadata to avoid modifying the original
        metadata_copy = dict(metadata or {})

        # Add standard fields
        state_change = {
            "timestamp": datetime.now().isoformat(),
            "from_state": from_state.value,
            "to_state": to_state.value,
            "event": event.value,
            "metadata": metadata_copy,
            "transition_id": f"{flow_id}_{len(self._state_history[flow_id])}",
        }

        # Add duration if this is completing a state
        if from_state != to_state:
            # Find the last transition to the from_state
            for prev_change in reversed(self._state_history[flow_id]):
                if prev_change["to_state"] == from_state.value:
                    try:
                        start_time = datetime.fromisoformat(prev_change["timestamp"])
                        end_time = datetime.fromisoformat(state_change["timestamp"])
                        duration_seconds = (end_time - start_time).total_seconds()
                        state_change["duration_seconds"] = duration_seconds
                        break
                    except (ValueError, KeyError):
                        # Skip if we can't calculate duration
                        pass

        # Add to history
        self._state_history[flow_id].append(state_change)

        # Log at appropriate level based on transition type
        if to_state in [FlowStatus.FAILED, FlowStatus.CANCELLED]:
            logger.warning(
                f"Flow {flow_id} state change: {from_state} -> {to_state} via {event}"
            )
        else:
            logger.info(
                f"Flow {flow_id} state change: {from_state} -> {to_state} via {event}"
            )

        # Limit history size to prevent memory issues in long-running flows
        max_history = 1000  # Configurable limit
        if len(self._state_history[flow_id]) > max_history:
            # Keep the first entry (initialization) and the most recent entries
            self._state_history[flow_id] = [
                self._state_history[flow_id][0]
            ] + self._state_history[flow_id][-max_history + 1 :]

    def _perform_state_actions(
        self,
        flow: ThinkingFlow,
        event: FlowEvent,
        new_state: FlowStatus,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Perform actions associated with a state transition

        This method executes the appropriate actions when a flow transitions to a new state.
        Different actions are performed based on the event type and the new state.

        Args:
            flow: The flow being transitioned
            event: The event that triggered the transition
            new_state: The new state
            metadata: Optional metadata about the transition

        Returns:
            True if actions were successful
        """
        try:
            metadata = metadata or {}

            # Handle flow state transitions
            if new_state == FlowStatus.RUNNING:
                if event == FlowEvent.START:
                    flow.start()
                    logger.info(f"Started flow {flow.flow_id}")
                elif event == FlowEvent.RESUME:
                    flow.resume()
                    # Calculate pause duration if we have pause time
                    if flow.flow_id in self._paused_flows:
                        pause_start = self._paused_flows[flow.flow_id]
                        pause_duration = (datetime.now() - pause_start).total_seconds()
                        logger.info(
                            f"Resumed flow {flow.flow_id} after {pause_duration:.1f}s pause"
                        )
                elif event == FlowEvent.RECOVER:
                    # Special handling for recovery from failure
                    error_step = metadata.get("error_step")
                    if error_step and error_step in flow.steps:
                        # Reset the failed step
                        step = flow.steps[error_step]
                        step.status = FlowStepStatus.PENDING
                        step.error_message = None
                        logger.info(
                            f"Recovered flow {flow.flow_id} by resetting step {error_step}"
                        )
                    else:
                        logger.info(f"Recovered flow {flow.flow_id} from failure state")

            elif new_state == FlowStatus.PAUSED:
                flow.pause()
                pause_reason = metadata.get("reason", "User requested")
                logger.info(f"Paused flow {flow.flow_id}: {pause_reason}")

            elif new_state == FlowStatus.COMPLETED:
                flow.complete()
                flow.end_time = datetime.now()

                # Calculate total duration
                if flow.start_time:
                    duration = (flow.end_time - flow.start_time).total_seconds()
                    logger.info(f"Completed flow {flow.flow_id} in {duration:.1f}s")
                else:
                    logger.info(f"Completed flow {flow.flow_id}")

            elif new_state == FlowStatus.FAILED:
                error_message = metadata.get("error_message", "Unknown error")
                flow.fail(error_message)
                flow.end_time = datetime.now()
                logger.error(f"Failed flow {flow.flow_id}: {error_message}")

            elif new_state == FlowStatus.CANCELLED:
                flow.status = FlowStatus.CANCELLED
                flow.end_time = datetime.now()
                cancel_reason = metadata.get("reason", "User cancelled")
                logger.info(f"Cancelled flow {flow.flow_id}: {cancel_reason}")

            # Handle step-specific events
            if event == FlowEvent.COMPLETE_STEP and metadata and "step_id" in metadata:
                step_id = metadata["step_id"]
                result = metadata.get("result", "")
                quality_score = metadata.get("quality_score")

                if step_id in flow.steps:
                    step = flow.steps[step_id]
                    step.complete(result, quality_score)
                    logger.info(
                        f"Completed step {step_id} in flow {flow.flow_id} "
                        f"with quality score {quality_score if quality_score is not None else 'N/A'}"
                    )

                    # Check if all steps are complete
                    all_complete = all(
                        step.status
                        in [FlowStepStatus.COMPLETED, FlowStepStatus.SKIPPED]
                        for step in flow.steps.values()
                    )

                    if all_complete:
                        # Auto-transition to completed state
                        logger.info(
                            f"All steps complete in flow {flow.flow_id}, auto-completing flow"
                        )
                        self.transition(
                            flow, FlowEvent.COMPLETE, {"auto_completed": True}
                        )
                else:
                    logger.warning(f"Step {step_id} not found in flow {flow.flow_id}")

            elif event == FlowEvent.FAIL_STEP and metadata and "step_id" in metadata:
                step_id = metadata["step_id"]
                error_message = metadata.get("error_message", "Step failed")

                if step_id in flow.steps:
                    step = flow.steps[step_id]
                    step.fail(error_message)
                    logger.warning(
                        f"Failed step {step_id} in flow {flow.flow_id}: {error_message}"
                    )

                    # If step can't be retried, check if flow should fail
                    if not step.can_retry() and metadata.get("critical", False):
                        logger.error(
                            f"Critical step {step_id} failed in flow {flow.flow_id} "
                            f"with no retries left, failing flow"
                        )
                        self.transition(
                            flow,
                            FlowEvent.ERROR,
                            {
                                "error_message": f"Critical step {step_id} failed: {error_message}",
                                "error_step": step_id,
                                "max_retries_exceeded": True,
                            },
                        )
                else:
                    logger.warning(f"Step {step_id} not found in flow {flow.flow_id}")

            elif event == FlowEvent.RETRY_STEP and metadata and "step_id" in metadata:
                step_id = metadata["step_id"]

                if step_id in flow.steps:
                    step = flow.steps[step_id]
                    if step.status == FlowStepStatus.FAILED and step.can_retry():
                        step.status = FlowStepStatus.PENDING
                        logger.info(
                            f"Retrying step {step_id} in flow {flow.flow_id} (attempt {step.retry_count + 1})"
                        )
                    else:
                        logger.warning(
                            f"Cannot retry step {step_id} in flow {flow.flow_id}: "
                            f"status={step.status}, retry_count={step.retry_count}"
                        )
                else:
                    logger.warning(f"Step {step_id} not found in flow {flow.flow_id}")

            elif event == FlowEvent.SKIP_STEP and metadata and "step_id" in metadata:
                step_id = metadata["step_id"]
                skip_reason = metadata.get("reason", "User requested")

                if step_id in flow.steps:
                    step = flow.steps[step_id]
                    step.status = FlowStepStatus.SKIPPED
                    logger.info(
                        f"Skipped step {step_id} in flow {flow.flow_id}: {skip_reason}"
                    )
                else:
                    logger.warning(f"Step {step_id} not found in flow {flow.flow_id}")

            return True

        except Exception as e:
            logger.error(
                f"Error performing state actions for flow {flow.flow_id}: {e}",
                exc_info=True,
            )
            return False

    def _persist_state(self, flow: ThinkingFlow) -> bool:
        """
        Persist flow state to database

        This method saves the current flow state to the database for recovery purposes.
        It stores the complete flow state, current step information, and state history.

        Args:
            flow: The flow to persist

        Returns:
            True if successful
        """
        if not self.db:
            return False

        try:
            # Convert flow state to JSON-serializable format
            flow_data = flow.to_dict()

            # Add additional metadata for recovery
            current_step = flow.get_current_step()
            context_data = {
                "flow_state": flow_data,
                "current_step": current_step.step_id if current_step else None,
                "step_number": flow.current_step_index,
                "last_updated": datetime.now().isoformat(),
                "persistence_version": "1.0",  # For future schema migrations
            }

            # Store in database - use both context and status for compatibility with tests
            self.db.update_session(
                flow.session_id, status=flow.status.value, context=context_data
            )

            # Store state history (limited to last 100 transitions to save space)
            if flow.flow_id in self._state_history:
                history = self._state_history[flow.flow_id]
                # Only store the most recent history entries
                recent_history = history[-100:] if len(history) > 100 else history

                self.db.update_session(
                    flow.session_id,
                    quality_metrics={
                        "flow_state_history": recent_history,
                        "last_transition": history[-1] if history else None,
                        "total_transitions": len(history),
                        "state_machine_stats": {
                            "current_state": flow.status.value,
                            "step_counts": {
                                status.value: len(
                                    [
                                        s
                                        for s in flow.steps.values()
                                        if s.status == status
                                    ]
                                )
                                for status in FlowStepStatus
                            },
                            "last_updated": datetime.now().isoformat(),
                        },
                    },
                )

            logger.debug(f"Persisted flow state for {flow.flow_id}")
            return True

        except Exception as e:
            logger.error(
                f"Error persisting flow state for {flow.flow_id}: {e}", exc_info=True
            )
            return False

    def restore_flow_state(
        self, flow_id: str, session_id: str
    ) -> Optional[ThinkingFlow]:
        """
        Restore flow state from database

        This method reconstructs a flow from its persisted state in the database.
        It restores the flow status, steps, and state history.

        Args:
            flow_id: Flow identifier
            session_id: Session identifier

        Returns:
            Restored flow or None if not found
        """
        if not self.db:
            logger.warning("Cannot restore flow state: no database connection")
            return None

        try:
            # Get session data from database
            session_data = self.db.get_session(session_id)
            if not session_data:
                logger.warning(f"Session {session_id} not found in database")
                return None

            if "context" not in session_data:
                logger.warning(f"Session {session_id} has no context data")
                return None

            context = session_data["context"]
            if "flow_state" not in context:
                logger.warning(f"Session {session_id} has no flow state data")
                return None

            flow_state = context["flow_state"]

            # Check persistence version for compatibility
            persistence_version = context.get("persistence_version", "0.1")
            logger.info(
                f"Restoring flow state version {persistence_version} for {flow_id}"
            )

            # Recreate flow object
            flow = ThinkingFlow(
                flow_id=flow_id,
                flow_name=flow_state.get("flow_name", "restored_flow"),
                session_id=session_id,
            )

            # Restore flow status
            try:
                flow.status = FlowStatus(flow_state.get("status", "initialized"))
            except ValueError:
                logger.warning(
                    f"Invalid flow status in database: {flow_state.get('status')}, using INITIALIZED"
                )
                flow.status = FlowStatus.INITIALIZED

            flow.current_step_index = flow_state.get("current_step_index", 0)
            flow.context = flow_state.get("context", {})

            # Restore timestamps
            if "start_time" in flow_state and flow_state["start_time"]:
                try:
                    flow.start_time = datetime.fromisoformat(flow_state["start_time"])
                except (ValueError, TypeError):
                    logger.warning(
                        f"Invalid start_time format in flow {flow_id}, ignoring"
                    )

            if "end_time" in flow_state and flow_state["end_time"]:
                try:
                    flow.end_time = datetime.fromisoformat(flow_state["end_time"])
                except (ValueError, TypeError):
                    logger.warning(
                        f"Invalid end_time format in flow {flow_id}, ignoring"
                    )

            # Restore steps
            steps_restored = 0
            for step_id, step_data in flow_state.get("steps", {}).items():
                try:
                    step = FlowStep(
                        step_id=step_id,
                        step_name=step_data.get("step_name", ""),
                        step_type=step_data.get("step_type", ""),
                        template_name=step_data.get("template_name", ""),
                        dependencies=step_data.get("dependencies", []),
                    )

                    # Restore step status
                    try:
                        step.status = FlowStepStatus(step_data.get("status", "pending"))
                    except ValueError:
                        logger.warning(
                            f"Invalid step status in database: {step_data.get('status')}, using PENDING"
                        )
                        step.status = FlowStepStatus.PENDING

                    step.result = step_data.get("result")
                    step.error_message = step_data.get("error_message")
                    step.quality_score = step_data.get("quality_score")
                    step.retry_count = step_data.get("retry_count", 0)

                    # Restore step timestamps
                    if "start_time" in step_data and step_data["start_time"]:
                        try:
                            step.start_time = datetime.fromisoformat(
                                step_data["start_time"]
                            )
                        except (ValueError, TypeError):
                            logger.warning(
                                f"Invalid start_time format in step {step_id}, ignoring"
                            )

                    if "end_time" in step_data and step_data["end_time"]:
                        try:
                            step.end_time = datetime.fromisoformat(
                                step_data["end_time"]
                            )
                        except (ValueError, TypeError):
                            logger.warning(
                                f"Invalid end_time format in step {step_id}, ignoring"
                            )

                    flow.add_step(step)
                    steps_restored += 1

                except Exception as step_error:
                    logger.error(
                        f"Error restoring step {step_id} in flow {flow_id}: {step_error}"
                    )

            # Restore step order
            flow.step_order = flow_state.get("step_order", [])

            # Restore state history
            if (
                "quality_metrics" in session_data
                and "flow_state_history" in session_data["quality_metrics"]
            ):
                try:
                    history = session_data["quality_metrics"]["flow_state_history"]
                    self._state_history[flow_id] = history
                    logger.info(
                        f"Restored {len(history)} state transitions for flow {flow_id}"
                    )
                except Exception as history_error:
                    logger.error(
                        f"Error restoring state history for flow {flow_id}: {history_error}"
                    )

            logger.info(
                f"Successfully restored flow {flow_id} with {steps_restored} steps"
            )

            # Check for interrupted flows that need recovery
            if self._auto_recovery_enabled and flow.status == FlowStatus.RUNNING:
                # This flow was running but got interrupted
                logger.warning(
                    f"Flow {flow_id} was in RUNNING state when persisted, "
                    f"marking for recovery"
                )
                flow.context["needs_recovery"] = True
                flow.context["recovery_timestamp"] = datetime.now().isoformat()

            return flow

        except Exception as e:
            logger.error(
                f"Error restoring flow state for {flow_id}: {e}", exc_info=True
            )
            return None

    def get_valid_transitions(self, flow: ThinkingFlow) -> Dict[FlowEvent, FlowStatus]:
        """
        Get valid transitions for a flow's current state

        This method returns all valid events and their target states for a flow's current state.
        It's useful for UI components that need to show available actions to users.

        Args:
            flow: The flow to check

        Returns:
            Dictionary of valid events and their target states
        """
        current_state = flow.status
        if current_state in self._valid_transitions:
            return self._valid_transitions[current_state]
        return {}

    def get_state_history(self, flow_id: str, limit: int = 0) -> List[Dict[str, Any]]:
        """
        Get state transition history for a flow

        This method returns the complete history of state transitions for a flow.
        It's useful for auditing, debugging, and visualization purposes.

        Args:
            flow_id: Flow identifier
            limit: Maximum number of history entries to return (0 for all)

        Returns:
            List of state transitions
        """
        history = self._state_history.get(flow_id, [])
        if limit > 0 and len(history) > limit:
            # Return the most recent entries if limited
            return history[-limit:]
        return history

    def can_transition(self, flow: ThinkingFlow, event: FlowEvent) -> bool:
        """
        Check if a transition is valid for a flow's current state

        This method checks if a specific event can be applied to a flow in its current state.
        It's useful for validating user actions before attempting a transition.

        Args:
            flow: The flow to check
            event: The event to check

        Returns:
            True if transition is valid
        """
        if not flow:
            return False

        current_state = flow.status
        return (
            current_state in self._valid_transitions
            and event in self._valid_transitions[current_state]
        )

    def reset_flow(self, flow: ThinkingFlow) -> bool:
        """
        Reset a flow to its initial state

        This method resets a flow to its initial state, clearing all progress and results.
        It's useful for restarting a flow from scratch after completion, failure, or cancellation.

        Args:
            flow: The flow to reset

        Returns:
            True if successful
        """
        if not flow:
            logger.warning("Cannot reset null flow")
            return False

        try:
            # Record original state for history
            original_state = flow.status

            # Reset flow status
            flow.status = FlowStatus.INITIALIZED
            flow.current_step_index = 0
            flow.start_time = None
            flow.end_time = None

            # Reset all steps
            for step in flow.steps.values():
                step.status = FlowStepStatus.PENDING
                step.start_time = None
                step.end_time = None
                step.result = None
                step.error_message = None
                step.quality_score = None
                step.retry_count = 0

            # Clear any recovery flags
            if "needs_recovery" in flow.context:
                del flow.context["needs_recovery"]
            if "recovery_timestamp" in flow.context:
                del flow.context["recovery_timestamp"]

            # Add reset metadata to context
            flow.context["last_reset"] = datetime.now().isoformat()
            flow.context["reset_from_state"] = original_state.value

            # Record reset in history
            self._record_state_change(
                flow.flow_id,
                original_state,
                FlowStatus.INITIALIZED,
                FlowEvent.RESET,
                {"reset_reason": "User requested reset"},
            )

            # Persist reset state
            if self.db:
                self._persist_state(flow)

            logger.info(
                f"Reset flow {flow.flow_id} from {original_state} to {FlowStatus.INITIALIZED}"
            )
            return True

        except Exception as e:
            logger.error(f"Error resetting flow {flow.flow_id}: {e}", exc_info=True)
            return False

    def pause_flow(self, flow: ThinkingFlow, reason: str = "User requested") -> bool:
        """
        Pause a running flow

        This method pauses a running flow, allowing it to be resumed later.
        It's useful for temporarily suspending a flow without cancelling it.

        Args:
            flow: The flow to pause
            reason: Reason for pausing the flow

        Returns:
            True if successful
        """
        if not flow:
            logger.warning("Cannot pause null flow")
            return False

        try:
            if flow.status != FlowStatus.RUNNING:
                logger.warning(
                    f"Cannot pause flow {flow.flow_id}: not in RUNNING state (current: {flow.status})"
                )
                return False

            # Transition to PAUSED state
            _, success = self.transition(flow, FlowEvent.PAUSE, {"reason": reason})
            return success

        except Exception as e:
            logger.error(f"Error pausing flow {flow.flow_id}: {e}")
            return False

    def resume_flow(self, flow: ThinkingFlow) -> bool:
        """
        Resume a paused flow

        This method resumes a previously paused flow.
        It's useful for continuing a flow after a temporary suspension.

        Args:
            flow: The flow to resume

        Returns:
            True if successful
        """
        if not flow:
            logger.warning("Cannot resume null flow")
            return False

        try:
            if flow.status != FlowStatus.PAUSED:
                logger.warning(
                    f"Cannot resume flow {flow.flow_id}: not in PAUSED state (current: {flow.status})"
                )
                return False

            # Transition to RUNNING state
            _, success = self.transition(flow, FlowEvent.RESUME)
            return success

        except Exception as e:
            logger.error(f"Error resuming flow {flow.flow_id}: {e}")
            return False

    def cancel_flow(self, flow: ThinkingFlow, reason: str = "User cancelled") -> bool:
        """
        Cancel a flow

        This method cancels a flow, terminating its execution.
        It's useful for abandoning a flow that is no longer needed.

        Args:
            flow: The flow to cancel
            reason: Reason for cancelling the flow

        Returns:
            True if successful
        """
        if not flow:
            logger.warning("Cannot cancel null flow")
            return False

        try:
            # Only allow cancellation from certain states
            if flow.status not in [
                FlowStatus.RUNNING,
                FlowStatus.PAUSED,
                FlowStatus.INITIALIZED,
            ]:
                logger.warning(
                    f"Cannot cancel flow {flow.flow_id}: invalid state {flow.status} "
                    f"(must be RUNNING, PAUSED, or INITIALIZED)"
                )
                return False

            # Transition to CANCELLED state
            _, success = self.transition(flow, FlowEvent.CANCEL, {"reason": reason})
            return success

        except Exception as e:
            logger.error(f"Error cancelling flow {flow.flow_id}: {e}")
            return False

    def check_for_timeouts(self, timeout_minutes: int = 60) -> List[str]:
        """
        Check for and handle timed out flows

        This method checks for flows that have been paused for too long and marks them as timed out.
        It's useful for automatically handling abandoned flows.

        Args:
            timeout_minutes: Number of minutes after which a paused flow is considered timed out

        Returns:
            List of flow IDs that were timed out
        """
        timed_out_flows = []
        now = datetime.now()
        timeout_threshold = timedelta(minutes=timeout_minutes)

        for flow_id, pause_time in list(self._paused_flows.items()):
            if now - pause_time > timeout_threshold:
                logger.warning(
                    f"Flow {flow_id} timed out after {timeout_minutes} minutes of inactivity"
                )

                # Get the flow from the flow manager (requires external handling)
                # For now, just remove from paused flows tracking
                self._paused_flows.pop(flow_id)
                timed_out_flows.append(flow_id)

        return timed_out_flows

    def get_flow_state_summary(self, flow: ThinkingFlow) -> Dict[str, Any]:
        """
        Get a summary of flow state

        This method generates a comprehensive summary of a flow's current state.
        It's useful for monitoring, reporting, and visualization purposes.

        Args:
            flow: The flow to summarize

        Returns:
            Dictionary with state summary
        """
        if not flow:
            return {"error": "Null flow provided"}

        try:
            # Count steps by status
            step_counts = {status.value: 0 for status in FlowStepStatus}
            for step in flow.steps.values():
                step_counts[step.status.value] += 1

            # Calculate quality metrics
            quality_scores = [
                step.quality_score
                for step in flow.steps.values()
                if step.quality_score is not None
            ]

            avg_quality = (
                sum(quality_scores) / len(quality_scores) if quality_scores else None
            )

            # Get current step info
            current_step = flow.get_current_step()
            current_step_info = None
            if current_step:
                current_step_info = {
                    "id": current_step.step_id,
                    "name": current_step.step_name,
                    "status": current_step.status.value,
                    "quality_score": current_step.quality_score,
                    "retry_count": current_step.retry_count,
                    "start_time": (
                        current_step.start_time.isoformat()
                        if current_step.start_time
                        else None
                    ),
                }

            # Calculate duration
            duration_seconds = None
            if flow.start_time:
                end_time = flow.end_time or datetime.now()
                duration_seconds = (end_time - flow.start_time).total_seconds()

            # Get next step info if available
            next_step = flow.get_next_step()
            next_step_info = None
            if next_step:
                next_step_info = {
                    "id": next_step.step_id,
                    "name": next_step.step_name,
                    "dependencies": next_step.dependencies,
                }

            # Get valid transitions
            valid_transitions = self.get_valid_transitions(flow)

            # Get state history stats
            history = self.get_state_history(flow.flow_id)
            history_stats = {
                "total_transitions": len(history),
                "last_transition": history[-1] if history else None,
                "state_counts": {},
            }

            # Count occurrences of each state in history
            for entry in history:
                to_state = entry["to_state"]
                history_stats["state_counts"][to_state] = (
                    history_stats["state_counts"].get(to_state, 0) + 1
                )

            return {
                "flow_id": flow.flow_id,
                "session_id": flow.session_id,
                "flow_name": flow.flow_name,
                "status": flow.status.value,
                "step_counts": step_counts,
                "total_steps": len(flow.steps),
                "completed_steps": step_counts[FlowStepStatus.COMPLETED.value],
                "failed_steps": step_counts[FlowStepStatus.FAILED.value],
                "skipped_steps": step_counts[FlowStepStatus.SKIPPED.value],
                "pending_steps": step_counts[FlowStepStatus.PENDING.value],
                "in_progress_steps": step_counts[FlowStepStatus.IN_PROGRESS.value],
                "current_step": current_step_info,
                "next_step": next_step_info,
                "current_step_index": flow.current_step_index,
                "progress_percentage": (
                    (
                        step_counts[FlowStepStatus.COMPLETED.value]
                        + step_counts[FlowStepStatus.SKIPPED.value]
                    )
                    / len(flow.steps)
                    * 100
                    if len(flow.steps) > 0
                    else 0
                ),
                "average_quality": avg_quality,
                "duration_seconds": duration_seconds,
                "start_time": flow.start_time.isoformat() if flow.start_time else None,
                "end_time": flow.end_time.isoformat() if flow.end_time else None,
                "valid_transitions": [
                    event.value for event in valid_transitions.keys()
                ],
                "state_history": history_stats,
                "needs_recovery": flow.context.get("needs_recovery", False),
                "last_updated": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(
                f"Error generating flow state summary for {flow.flow_id}: {e}",
                exc_info=True,
            )
            return {
                "error": f"Failed to generate summary: {str(e)}",
                "flow_id": flow.flow_id if flow else None,
                "status": flow.status.value if flow else None,
            }

    def get_step_state_summary(
        self, flow: ThinkingFlow, step_id: str
    ) -> Dict[str, Any]:
        """
        Get a summary of a specific step's state

        This method generates a comprehensive summary of a step's current state.
        It's useful for detailed step monitoring and debugging.

        Args:
            flow: The flow containing the step
            step_id: The ID of the step to summarize

        Returns:
            Dictionary with step state summary
        """
        if not flow:
            return {"error": "Null flow provided"}

        if step_id not in flow.steps:
            return {"error": f"Step {step_id} not found in flow {flow.flow_id}"}

        try:
            step = flow.steps[step_id]

            # Calculate duration if applicable
            duration_seconds = None
            if step.start_time:
                end_time = step.end_time or datetime.now()
                duration_seconds = (end_time - step.start_time).total_seconds()

            # Check dependencies
            dependencies_met = True
            dependency_status = {}
            for dep_id in step.dependencies:
                if dep_id in flow.steps:
                    dep_step = flow.steps[dep_id]
                    is_met = dep_step.status == FlowStepStatus.COMPLETED
                    dependencies_met = dependencies_met and is_met
                    dependency_status[dep_id] = {
                        "status": dep_step.status.value,
                        "is_met": is_met,
                    }
                else:
                    dependencies_met = False
                    dependency_status[dep_id] = {"status": "missing", "is_met": False}

            return {
                "step_id": step.step_id,
                "step_name": step.step_name,
                "step_type": step.step_type,
                "template_name": step.template_name,
                "status": step.status.value,
                "result": (
                    step.result[:100] + "..."
                    if step.result and len(step.result) > 100
                    else step.result
                ),
                "error_message": step.error_message,
                "quality_score": step.quality_score,
                "retry_count": step.retry_count,
                "max_retries": step.max_retries,
                "can_retry": step.can_retry(),
                "start_time": step.start_time.isoformat() if step.start_time else None,
                "end_time": step.end_time.isoformat() if step.end_time else None,
                "duration_seconds": duration_seconds,
                "dependencies": step.dependencies,
                "dependencies_met": dependencies_met,
                "dependency_status": dependency_status,
            }

        except Exception as e:
            logger.error(
                f"Error generating step state summary for {step_id} in flow {flow.flow_id}: {e}",
                exc_info=True,
            )
            return {
                "error": f"Failed to generate step summary: {str(e)}",
                "step_id": step_id,
                "flow_id": flow.flow_id if flow else None,
            }

    def get_flow_statistics(self) -> Dict[str, Any]:
        """
        Get overall statistics for all flows managed by this state machine

        This method generates aggregate statistics across all flows.
        It's useful for monitoring and reporting on the overall system state.

        Returns:
            Dictionary with flow statistics
        """
        try:
            # Count flows by status
            status_counts = {}
            for flow_id in self._state_history.keys():
                # Get the last state for each flow
                history = self._state_history[flow_id]
                if history:
                    last_state = history[-1]["to_state"]
                    status_counts[last_state] = status_counts.get(last_state, 0) + 1

            # Count paused flows
            paused_flows = len(self._paused_flows)

            # Calculate average transitions per flow
            avg_transitions = (
                sum(len(history) for history in self._state_history.values())
                / len(self._state_history)
                if self._state_history
                else 0
            )

            # Get total transition count
            total_transitions = sum(
                len(history) for history in self._state_history.values()
            )

            return {
                "total_flows_tracked": len(self._state_history),
                "flows_by_status": status_counts,
                "paused_flows": paused_flows,
                "total_transitions": total_transitions,
                "avg_transitions_per_flow": avg_transitions,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error generating flow statistics: {e}", exc_info=True)
            return {
                "error": f"Failed to generate statistics: {str(e)}",
                "timestamp": datetime.now().isoformat(),
            }

    def cleanup_history(self, max_age_days: int = 30) -> int:
        """
        Clean up old flow history to prevent memory bloat

        This method removes history for flows that haven't been updated in a while.
        It's useful for long-running systems to prevent memory leaks.

        Args:
            max_age_days: Maximum age of history entries to keep

        Returns:
            Number of flows whose history was cleaned up
        """
        if not self.db:
            logger.warning("Cannot clean up history without database - would lose data")
            return 0

        try:
            flows_cleaned = 0
            cutoff_date = datetime.now() - timedelta(days=max_age_days)

            for flow_id in list(self._state_history.keys()):
                history = self._state_history[flow_id]
                if not history:
                    continue

                # Check last update time
                try:
                    last_update = datetime.fromisoformat(history[-1]["timestamp"])
                    if last_update < cutoff_date:
                        # This flow hasn't been updated in a while
                        # Since we have a database, we can safely remove it from memory
                        del self._state_history[flow_id]
                        flows_cleaned += 1
                except (ValueError, KeyError, IndexError):
                    # Skip if we can't parse the timestamp
                    pass

            logger.info(
                f"Cleaned up history for {flows_cleaned} flows older than {max_age_days} days"
            )
            return flows_cleaned

        except Exception as e:
            logger.error(f"Error cleaning up flow history: {e}", exc_info=True)
            return 0

    def export_flow_history(self, flow_id: str, format: str = "json") -> Dict[str, Any]:
        """
        Export complete flow history in a structured format

        This method exports the complete history of a flow for external analysis.
        It's useful for debugging, auditing, and visualization purposes.

        Args:
            flow_id: The ID of the flow to export
            format: Export format (currently only 'json' is supported)

        Returns:
            Dictionary with complete flow history
        """
        if flow_id not in self._state_history:
            return {"error": f"Flow {flow_id} not found in history"}

        try:
            history = self._state_history[flow_id]

            # Calculate state durations
            state_durations = {}
            for i in range(1, len(history)):
                prev = history[i - 1]
                curr = history[i]

                try:
                    prev_time = datetime.fromisoformat(prev["timestamp"])
                    curr_time = datetime.fromisoformat(curr["timestamp"])
                    duration = (curr_time - prev_time).total_seconds()

                    state = prev["to_state"]
                    if state not in state_durations:
                        state_durations[state] = {
                            "total_seconds": 0,
                            "occurrences": 0,
                            "min_seconds": float("inf"),
                            "max_seconds": 0,
                        }

                    state_durations[state]["total_seconds"] += duration
                    state_durations[state]["occurrences"] += 1
                    state_durations[state]["min_seconds"] = min(
                        state_durations[state]["min_seconds"], duration
                    )
                    state_durations[state]["max_seconds"] = max(
                        state_durations[state]["max_seconds"], duration
                    )

                except (ValueError, KeyError):
                    # Skip if we can't parse the timestamps
                    pass

            # Calculate average durations
            for state, data in state_durations.items():
                if data["occurrences"] > 0:
                    data["avg_seconds"] = data["total_seconds"] / data["occurrences"]

                # Fix infinity in min_seconds if state only occurred once
                if data["min_seconds"] == float("inf"):
                    data["min_seconds"] = data["total_seconds"]

            return {
                "flow_id": flow_id,
                "history": history,
                "total_transitions": len(history),
                "state_durations": state_durations,
                "first_timestamp": history[0]["timestamp"] if history else None,
                "last_timestamp": history[-1]["timestamp"] if history else None,
                "export_format": format,
                "export_timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(
                f"Error exporting flow history for {flow_id}: {e}", exc_info=True
            )
            return {
                "error": f"Failed to export history: {str(e)}",
                "flow_id": flow_id,
            }
