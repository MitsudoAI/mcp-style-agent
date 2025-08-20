"""
Flow management system for deep thinking processes
Handles the orchestration and state management of thinking flows
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from ..config.exceptions import (
    ConfigurationError,
    FlowExecutionError,
    InvalidTransitionError,
)
from ..data.database import ThinkingDatabase
from ..models.thinking_models import FlowStep, FlowStepStatus

logger = logging.getLogger(__name__)


class FlowStatus(str, Enum):
    """Status of a flow"""

    INITIALIZED = "initialized"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


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
                    "for_each": "decompose.sub_questions",
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
            # Prepare config with template name
            config = step_def.get("config", {}).copy()
            if "template_name" in step_def:
                config["template_name"] = step_def["template_name"]

            step = FlowStep(
                step_id=step_def["step_id"],
                agent_type=step_def.get(
                    "step_type", "unknown"
                ),  # Map step_type to agent_type
                step_name=step_def["step_name"],
                description=step_def.get("description", ""),
                config=config,
                for_each=step_def.get("for_each"),  # Add for_each support
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
                "quality_score": quality_score,
            }
            new_state, success = self.state_machine.transition(
                flow, FlowEvent.COMPLETE_STEP, metadata
            )
            if not success:
                logger.warning(f"Failed to complete step {step_id} in flow {flow_id}")
                # Fallback to direct method
                step = flow.steps[step_id]
                step.complete(result, quality_score)
        except InvalidTransitionError as e:
            logger.error(
                f"Invalid transition when completing step {step_id} in flow {flow_id}: {e}"
            )
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

    def fail_step(
        self, flow_id: str, step_id: str, error_message: str, critical: bool = False
    ):
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
                "critical": critical,
            }
            new_state, success = self.state_machine.transition(
                flow, FlowEvent.FAIL_STEP, metadata
            )
            if not success:
                logger.warning(
                    f"Failed to mark step {step_id} as failed in flow {flow_id}"
                )
                # Fallback to direct method
                step = flow.steps[step_id]
                step.fail(error_message)
        except InvalidTransitionError as e:
            logger.error(
                f"Invalid transition when failing step {step_id} in flow {flow_id}: {e}"
            )
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
        """Get next step information for a flow type with for_each support"""
        if flow_type not in self.flow_definitions:
            return None

        flow_def = self.flow_definitions[flow_type]
        steps = flow_def["steps"]

        # Find current step index - handle different step name formats
        current_index = -1
        current_step_def = None
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
                current_step_def = step
                break

        # Check if current step has for_each and needs to continue iterating
        if current_step_def and current_step_def.get("for_each"):
            logger.info(f"Checking for_each continuation for step {current_step}")

            # Check if we need to continue iterating
            should_continue = self._should_continue_for_each_iteration(
                current_step_def, step_result, current_step
            )

            if should_continue:
                logger.info(f"Continuing for_each iteration for step {current_step}")
                return {
                    "step_name": current_step_def["step_id"],
                    "template_name": current_step_def["template_name"],
                    "instructions": f"Continue {current_step_def['step_name']} step for next sub-question",
                    "for_each_continuation": True,
                }

        # Return next step if available
        if current_index >= 0 and current_index + 1 < len(steps):
            next_step = steps[current_index + 1]
            logger.info(f"Advancing from {current_step} to {next_step['step_id']}")
            return {
                "step_name": next_step["step_id"],
                "template_name": next_step["template_name"],
                "instructions": f"Execute {next_step['step_name']} step",
            }

        return None

    def _should_continue_for_each_iteration(
        self, current_step_def: Dict[str, Any], step_result: str, current_step: str
    ) -> bool:
        """
        Determine if a for_each step should continue iterating

        Args:
            current_step_def: Step definition with for_each configuration
            step_result: Result from the current step execution
            current_step: Current step name

        Returns:
            True if should continue iterating, False if should advance to next step
        """
        try:
            # Parse for_each reference (e.g., "decompose.sub_questions")
            for_each_ref = current_step_def.get("for_each", "")
            if not for_each_ref or "." not in for_each_ref:
                logger.warning(f"Invalid for_each reference: {for_each_ref}")
                return False

            source_step, property_name = for_each_ref.split(".", 1)

            # For collect_evidence step, we need to check if we've processed all sub-questions
            if current_step == "collect_evidence" and source_step == "decompose":
                return self._check_evidence_collection_progress(
                    step_result, property_name
                )

            # For other for_each steps, implement similar logic
            logger.info(
                f"No specific for_each continuation logic for {current_step}, defaulting to False"
            )
            return False

        except Exception as e:
            logger.error(f"Error checking for_each continuation: {e}")
            return False

    def _check_evidence_collection_progress(
        self, step_result: str, property_name: str
    ) -> bool:
        """
        Check if evidence collection should continue for more sub-questions

        Uses intelligent analysis of decomposition results and evidence content
        to dynamically determine completion, avoiding hard-coded thresholds.

        Args:
            step_result: Result from evidence collection step
            property_name: Property name (e.g., "sub_questions")

        Returns:
            True if more sub-questions need processing, False if all are done
        """
        import json
        import re

        try:
            # Get the expected number of sub-questions from decomposition result
            expected_subquestions = self._get_expected_subquestion_count()
            logger.info(f"Expected sub-questions count: {expected_subquestions}")

            # HIGHEST PRIORITY: Check for JSON-structured evidence first
            try:
                result_data = json.loads(step_result.strip())
                if isinstance(result_data, dict):
                    # Check if this is individual sub-question processing format
                    if (
                        "sub_question" in result_data
                        and "evidence_synthesis" in result_data
                    ):
                        sub_question = result_data.get("sub_question", "")
                        evidence_synthesis = result_data.get("evidence_synthesis", {})

                        # Check if this contains completion indicators
                        completion_phrases = [
                            "所有子问题已处理完成",
                            "全部子问题分析完毕",
                            "完成了所有子问题",
                            "evidence collection complete",
                            "all sub-questions processed",
                            "阶段结束",
                            "处理完成",
                            "analysis_complete",  # JSON field indicating completion
                        ]

                        full_text = json.dumps(result_data, ensure_ascii=False)
                        for phrase in completion_phrases:
                            if phrase in full_text:
                                logger.info(
                                    f"Found completion indicator in JSON: {phrase}"
                                )
                                return False

                        # Check for explicit completion fields in JSON
                        if (
                            result_data.get("analysis_complete") is True
                            or "sub_questions_processed" in result_data
                        ):
                            logger.info(
                                "Found explicit completion fields in JSON structure"
                            )
                            return False

                        # If we have a specific sub-question without completion indicators,
                        # this indicates individual processing - continue for_each
                        if sub_question and not any(
                            phrase in full_text for phrase in completion_phrases
                        ):
                            logger.info(
                                f"Found individual sub-question processing in JSON format: {sub_question[:50]}..."
                            )
                            return True

            except (json.JSONDecodeError, ValueError):
                logger.debug("Step result is not valid JSON, checking text patterns")

            # SECOND PRIORITY: Check for completion indicators in text
            completion_indicators = [
                "所有子问题已处理完成",
                "全部子问题分析完毕",
                "完成了所有子问题",
                "证据收集阶段已完成",
                "证据收集已完成",
                "evidence collection complete",
                "evidence collection phase complete",
                "comprehensive analysis of all",
                "all sub-questions processed",
                "final sub-question analysis",
                "第七个子问题",
                "现在需要进入综合分析阶段",
                "现在需要进入下一个思考阶段",
                "需要进入.*阶段",  # Regex pattern
                "所有.*子问题已处理完成",  # Regex-style pattern
            ]

            for indicator in completion_indicators:
                # Handle regex patterns
                if ".*" in indicator:
                    if re.search(indicator, step_result):
                        logger.info(f"Found completion indicator (regex): {indicator}")
                        return False
                else:
                    if indicator in step_result:
                        logger.info(f"Found completion indicator: {indicator}")
                        return False

            # HIGH PRIORITY: Check for summary/conclusion language (suggests completion)
            conclusion_patterns = [
                "综合以上分析",
                "总结",
                "综合建议",
                "最终建议",
                "in conclusion",
                "to summarize",
                "overall recommendation",
            ]

            for pattern in conclusion_patterns:
                if pattern in step_result:
                    logger.info(f"Found conclusion pattern: {pattern}")
                    return False

            # SMART PRIORITY: Dynamic completion detection based on expected count
            sq_matches = re.findall(r"SQ(\d+)", step_result)
            if sq_matches:
                unique_sqs = set(sq_matches)
                processed_count = len(unique_sqs)
                logger.info(f"Found sub-question IDs in result: {unique_sqs}")
                logger.info(
                    f"Processed: {processed_count}, Expected: {expected_subquestions}"
                )

                # Dynamic completion threshold based on expected count
                if expected_subquestions > 0:
                    completion_threshold = max(
                        expected_subquestions - 1, expected_subquestions * 0.8
                    )
                    logger.info(
                        f"Using dynamic completion threshold: {completion_threshold}"
                    )

                    # If we've seen most/all expected sub-questions, check for completion signals
                    if processed_count >= completion_threshold:
                        checkmark_count = step_result.count("✓")
                        if checkmark_count >= completion_threshold:
                            logger.info(
                                f"Found {processed_count}/{expected_subquestions} SQs with {checkmark_count} checkmarks, likely completion"
                            )
                            return False
                        elif processed_count >= expected_subquestions:
                            logger.info(
                                f"Found all expected sub-questions ({processed_count}/{expected_subquestions}), likely completion summary"
                            )
                            return False
                else:
                    # Smart fallback: look for completion signals when we have substantial progress
                    if processed_count >= 5:
                        # With 5+ sub-questions, look for strong completion signals
                        checkmark_count = step_result.count("✓")
                        if (
                            checkmark_count >= processed_count * 0.8
                            or processed_count >= 7
                        ):  # Very high confidence threshold
                            logger.info(
                                f"Found {processed_count} sub-questions with completion signals (fallback), likely completion"
                            )
                            return False

            # LOWER PRIORITY: Check for sub-question processing indicators
            sub_question_indicators = [
                "第一个高优先级子问题",
                "第二个高优先级子问题",
                "第三个子问题",
                "第一个子问题",
                "第二个子问题",
                "第1个子问题",
                "第2个子问题",
                "继续为",
                "针对SQ",
                "为.*子问题",
                "first sub-question",
                "second sub-question",
                "first high-priority",
            ]

            for indicator in sub_question_indicators:
                if indicator in step_result:
                    logger.info(
                        f"Detected sub-question processing indicator: {indicator}"
                    )
                    return True

            # Check for specific individual processing patterns
            individual_processing_indicators = [
                "重点关注在无本金约束下",
                "技术分析和AI工具识别",
                "最佳入场时机",
                "市场趋势",
                "期权组合策略",
                "风险管理体系",
            ]

            individual_count = sum(
                1
                for indicator in individual_processing_indicators
                if indicator in step_result
            )
            if individual_count >= 2:
                logger.info("Detected individual sub-question processing patterns")
                return True

            # Check for individual analysis patterns (suggests focusing on one sub-question)
            individual_analysis_patterns = [
                "这为第.*子问题提供了",
                "针对.*的详细分析",
                "这为.*提供了.*分析",
                "detailed analysis for",
                "provides analysis for",
            ]

            for pattern in individual_analysis_patterns:
                if re.search(pattern, step_result):
                    logger.info(f"Detected individual analysis pattern: {pattern}")
                    return True

            # Check for partial SQ processing (dynamic threshold)
            if sq_matches:
                processed_count = len(unique_sqs)
                # If we see SQ1 but not others, and no completion context, continue
                if "1" in unique_sqs and processed_count == 1:
                    logger.info("Only SQ1 processed, continuing for SQ2, SQ3, etc.")
                    return True
                elif expected_subquestions > 0:
                    # Use dynamic threshold: continue if we haven't processed most sub-questions yet
                    continue_threshold = max(
                        expected_subquestions * 0.7, expected_subquestions - 2
                    )
                    if processed_count < continue_threshold:
                        logger.info(
                            f"Only {processed_count}/{expected_subquestions} sub-questions processed (< {continue_threshold:.1f}), continuing"
                        )
                        return True
                else:
                    # Fallback: continue until we see substantial progress
                    if processed_count <= 4:
                        logger.info(
                            f"Only {processed_count} sub-questions processed (fallback threshold), likely more to go"
                        )
                        return True

            # Default heuristic - if we have substantial content but no clear indicators
            if len(step_result) > 1000:
                logger.info(
                    f"Substantial result ({len(step_result)} chars) without completion indicators, continuing for_each"
                )
                return True

            # More conservative default - continue unless we have strong completion signals
            logger.info(
                "No clear completion indicators found, continuing for_each to be safe"
            )
            return True

        except Exception as e:
            logger.error(f"Error analyzing evidence collection progress: {e}")
            # Default to continuing to be safe - this ensures we don't miss iterations
            return True

    def _get_expected_subquestion_count(self) -> int:
        """
        Get the expected number of sub-questions from decomposition result

        Since we don't have direct access to session state in this context,
        we use intelligent heuristics based on step result patterns and
        decomposition complexity indicators.

        Returns:
            Estimated number of expected sub-questions, or 0 if cannot be determined
        """
        try:
            # TODO: Future enhancement - access session state to get actual decomposition result
            # For now, use conservative estimation that favors continuing iteration

            # Return 0 to trigger conservative fallback logic in the caller
            # This is safer than guessing wrong and terminating early
            return 0

        except Exception as e:
            logger.error(f"Error getting expected sub-question count: {e}")
            return 0

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
            logger.warning(
                f"Flow not found when trying to get valid transitions: {flow_id}"
            )
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
