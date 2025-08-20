"""
Flow Executor for Deep Thinking Engine

This module implements the flow execution engine that orchestrates the execution of thinking flows.
It handles step scheduling, template selection, parameter replacement, execution monitoring, and error handling.
"""

import json
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from ..config.exceptions import FlowExecutionError
from ..data.database import ThinkingDatabase
from ..flows.flow_manager import FlowManager, ThinkingFlow
from ..models.thinking_models import FlowStep
from ..templates.template_manager import TemplateManager

logger = logging.getLogger(__name__)


class FlowExecutor:
    """
    Flow execution engine for orchestrating thinking flows

    This class is responsible for executing thinking flows and their steps.
    It handles step scheduling, template selection, parameter replacement,
    execution monitoring, and error handling.

    Key features:
    - Execute individual steps or entire flows
    - Select appropriate templates based on context
    - Replace template parameters with context values
    - Monitor execution progress and performance
    - Handle errors and provide recovery options
    """

    def __init__(
        self,
        flow_manager: FlowManager,
        template_manager: TemplateManager,
        db: Optional[ThinkingDatabase] = None,
    ):
        """
        Initialize the flow executor

        Args:
            flow_manager: Flow manager for accessing flows and steps
            template_manager: Template manager for accessing templates
            db: Optional database for execution logging
        """
        self.flow_manager = flow_manager
        self.template_manager = template_manager
        self.db = db
        self.execution_stats = {}  # Track execution statistics
        logger.info("FlowExecutor initialized")

    def execute_step(
        self, flow_id: str, step_id: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a single step in a flow

        This method handles the execution of a single step in a flow. It retrieves the flow and step,
        checks dependencies, selects the appropriate template, replaces parameters, and executes the step.

        Args:
            flow_id: ID of the flow containing the step
            step_id: ID of the step to execute
            context: Optional additional context for template parameter replacement

        Returns:
            Dict containing execution results

        Raises:
            FlowExecutionError: If step execution fails
        """
        start_time = time.time()
        execution_id = f"{flow_id}_{step_id}_{int(start_time * 1000)}"
        context = context or {}

        try:
            # Get flow
            flow = self.flow_manager.get_flow(flow_id)
            if not flow:
                raise FlowExecutionError(f"Flow not found: {flow_id}")

            # Get step
            if step_id not in flow.steps:
                raise FlowExecutionError(f"Step not found: {step_id} in flow {flow_id}")

            step = flow.steps[step_id]

            # Check dependencies
            if hasattr(flow, "_check_dependencies") and not flow._check_dependencies(
                step
            ):
                raise FlowExecutionError(
                    f"Dependencies not satisfied for step {step_id} in flow {flow_id}"
                )

            # Mark step as in progress
            step.start()

            # Merge context
            merged_context = {**flow.context, **context}

            # Select template
            template_name, template_params = self._select_template(
                flow, step, merged_context
            )

            try:
                # Get template content
                template_content = self.template_manager.get_template(
                    template_name, template_params
                )
            except Exception as e:
                raise FlowExecutionError(
                    f"Error executing step {step_id} in flow {flow_id}: {e}"
                )

            # Log execution
            logger.info(
                f"Executing step {step_id} in flow {flow_id} with template {template_name}"
            )

            # Record execution in database if available
            if self.db:
                self._log_execution_start(flow, step, template_name, template_params)

            # Update execution stats
            self._update_execution_stats(flow_id, step_id, start_time)

            # Return execution result
            return {
                "execution_id": execution_id,
                "flow_id": flow_id,
                "step_id": step_id,
                "template_name": template_name,
                "template_content": template_content,
                "context": merged_context,
                "status": "completed",
                "execution_time_ms": int((time.time() - start_time) * 1000),
            }

        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            error_message = str(e)

            logger.error(
                f"Error executing step {step_id} in flow {flow_id}: {error_message}"
            )

            # Update execution stats for failure
            self._update_execution_stats(flow_id, step_id, start_time, success=False)

            # Log failure in database if available
            if self.db:
                self._log_execution_failure(
                    flow_id, step_id, error_message, execution_time_ms
                )

            # Raise exception with details
            if isinstance(e, FlowExecutionError):
                raise
            raise FlowExecutionError(
                f"Error executing step {step_id} in flow {flow_id}: {error_message}"
            )

    def execute_flow(
        self,
        flow_id: str,
        continue_on_error: bool = False,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute an entire flow

        This method executes all steps in a flow in sequence. It handles step dependencies,
        execution monitoring, and error handling, including for_each iterations.

        Args:
            flow_id: ID of the flow to execute
            continue_on_error: Whether to continue execution if a step fails
            context: Optional additional context for template parameter replacement

        Returns:
            Dict containing execution results

        Raises:
            FlowExecutionError: If flow execution fails and continue_on_error is False
        """
        start_time = time.time()
        context = context or {}
        steps_executed = 0
        steps_succeeded = 0
        steps_failed = 0
        failed_steps = []

        # Store step outputs for reference by later steps
        step_outputs = {}

        try:
            # Execute steps in sequence
            while True:
                # Get next step
                step = self.flow_manager.get_next_step_in_flow(flow_id)
                if not step:
                    break  # No more steps to execute

                # Check if this step has for_each configuration
                step_config = getattr(step, "config", {}) or {}
                for_each = getattr(step, "for_each", None) or step_config.get(
                    "for_each"
                )

                if for_each:
                    # Handle for_each iteration
                    iteration_results = self._execute_step_with_for_each(
                        flow_id,
                        step,
                        for_each,
                        context,
                        step_outputs,
                        continue_on_error,
                    )
                    steps_executed += iteration_results["steps_executed"]
                    steps_succeeded += iteration_results["steps_succeeded"]
                    steps_failed += iteration_results["steps_failed"]
                    failed_steps.extend(iteration_results["failed_steps"])

                    # Store iteration results in step_outputs
                    step_outputs[step.step_id] = iteration_results["results"]

                    # Mark step as completed and advance flow
                    if iteration_results["steps_succeeded"] > 0:
                        try:
                            # Mark step as completed
                            step.complete(str(iteration_results["results"]))

                            # Use flow manager to properly complete the step
                            flow = self.flow_manager.get_flow(flow_id)
                            if flow:
                                flow.advance_step()

                            logger.info(
                                f"Completed for_each step {step.step_id} with {iteration_results['steps_succeeded']} successful iterations"
                            )

                        except Exception as e:
                            logger.warning(
                                f"Error marking for_each step {step.step_id} as completed: {e}"
                            )

                else:
                    # Execute single step normally
                    steps_executed += 1

                    try:
                        # Execute step
                        step_result = self.execute_step(flow_id, step.step_id, context)
                        steps_succeeded += 1

                        # Store step output for later reference
                        if "template_content" in step_result:
                            step_outputs[step.step_id] = step_result["template_content"]

                        # Update context with step result
                        if "context" in step_result:
                            context.update(step_result["context"])

                        # Mark step as completed and advance flow
                        try:
                            # Mark step as completed
                            step.complete(step_result.get("template_content", ""))

                            # Use flow manager to properly complete the step
                            flow = self.flow_manager.get_flow(flow_id)
                            if flow:
                                flow.advance_step()

                            logger.info(f"Completed step {step.step_id}")

                        except Exception as e:
                            logger.warning(
                                f"Error marking step {step.step_id} as completed: {e}"
                            )

                    except Exception as e:
                        steps_failed += 1
                        failed_steps.append({"step_id": step.step_id, "error": str(e)})

                        logger.error(
                            f"Error executing step {step.step_id} in flow {flow_id}: {e}"
                        )

                        # Mark step as failed
                        try:
                            step.fail(str(e))
                        except Exception as completion_error:
                            logger.warning(
                                f"Error marking step {step.step_id} as failed: {completion_error}"
                            )

                        if not continue_on_error:
                            raise

                # Add step outputs to context for next steps
                context["step_outputs"] = step_outputs

            # Calculate execution time
            execution_time_ms = int((time.time() - start_time) * 1000)

            # Determine flow status
            status = "completed"

            # Log execution completion
            logger.info(
                f"Flow {flow_id} execution completed in {execution_time_ms}ms: "
                f"{steps_succeeded}/{steps_executed} steps succeeded"
            )

            # Return execution result
            return {
                "flow_id": flow_id,
                "status": status,
                "execution_time_ms": execution_time_ms,
                "steps_executed": steps_executed,
                "steps_succeeded": steps_succeeded,
                "steps_failed": steps_failed,
                "failed_steps": failed_steps,
                "step_outputs": step_outputs,
            }

        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            error_message = str(e)

            logger.error(f"Error executing flow {flow_id}: {error_message}")

            # Return execution result with failure
            return {
                "flow_id": flow_id,
                "status": "failed",
                "error": error_message,
                "execution_time_ms": execution_time_ms,
                "steps_executed": steps_executed,
                "steps_succeeded": steps_succeeded,
                "steps_failed": steps_failed,
                "failed_steps": failed_steps,
            }

    def _execute_step_with_for_each(
        self,
        flow_id: str,
        step,
        for_each: str,
        context: Dict[str, Any],
        step_outputs: Dict[str, Any],
        continue_on_error: bool = False,
    ) -> Dict[str, Any]:
        """
        Execute a step with for_each iteration

        Args:
            flow_id: ID of the flow
            step: Step to execute
            for_each: Reference to data to iterate over (e.g. "decomposer.sub_questions")
            context: Execution context
            step_outputs: Previous step outputs
            continue_on_error: Whether to continue on error

        Returns:
            Dict containing iteration results
        """
        logger.info(f"Executing step {step.step_id} with for_each: {for_each}")

        # Parse the for_each reference (e.g. "decomposer.sub_questions")
        iteration_data = self._resolve_for_each_reference(
            for_each, step_outputs, context
        )
        if not iteration_data:
            logger.warning(f"No data found for for_each reference: {for_each}")
            return {
                "steps_executed": 0,
                "steps_succeeded": 0,
                "steps_failed": 0,
                "failed_steps": [],
                "results": [],
            }

        results = []
        steps_executed = 0
        steps_succeeded = 0
        steps_failed = 0
        failed_steps = []

        # Execute step for each item in the iteration data
        for i, item in enumerate(iteration_data):
            steps_executed += 1
            iteration_context = context.copy()

            # Add current iteration item to context
            if isinstance(item, dict):
                iteration_context.update(item)
                # Also add as current_item for template access
                iteration_context["current_item"] = item
                iteration_context["current_index"] = i
            else:
                iteration_context["current_item"] = item
                iteration_context["current_index"] = i

            try:
                # Execute step for this iteration
                step_result = self.execute_step(
                    flow_id, f"{step.step_id}_iter_{i}", iteration_context
                )
                steps_succeeded += 1

                # Store iteration result
                result_data = {
                    "iteration_index": i,
                    "iteration_item": item,
                    "result": step_result.get("template_content", ""),
                    "execution_id": step_result.get("execution_id"),
                }
                results.append(result_data)

                logger.info(f"Completed iteration {i} of step {step.step_id}")

            except Exception as e:
                steps_failed += 1
                error_info = {
                    "step_id": f"{step.step_id}_iter_{i}",
                    "iteration_index": i,
                    "iteration_item": item,
                    "error": str(e),
                }
                failed_steps.append(error_info)

                logger.error(f"Error in iteration {i} of step {step.step_id}: {e}")

                if not continue_on_error:
                    raise

        logger.info(
            f"Completed for_each execution of step {step.step_id}: "
            f"{steps_succeeded}/{steps_executed} iterations succeeded"
        )

        return {
            "steps_executed": steps_executed,
            "steps_succeeded": steps_succeeded,
            "steps_failed": steps_failed,
            "failed_steps": failed_steps,
            "results": results,
        }

    def _resolve_for_each_reference(
        self, for_each: str, step_outputs: Dict[str, Any], context: Dict[str, Any]
    ) -> List[Any]:
        """
        Resolve for_each reference to get iteration data

        Args:
            for_each: Reference string (e.g. "decomposer.sub_questions")
            step_outputs: Previous step outputs
            context: Execution context

        Returns:
            List of items to iterate over
        """
        try:
            # Parse reference format "step_name.property"
            if "." not in for_each:
                logger.warning(
                    f"Invalid for_each format: {for_each}. Expected 'step_name.property'"
                )
                return []

            step_name, property_name = for_each.split(".", 1)

            # Get the step output
            step_output = step_outputs.get(step_name)
            if not step_output:
                logger.warning(f"No output found for step: {step_name}")
                return []

            # Try to parse as JSON if it's a string
            if isinstance(step_output, str):
                try:
                    step_output = json.loads(step_output)
                except json.JSONDecodeError:
                    logger.warning(f"Could not parse step output as JSON: {step_name}")
                    return []

            # Navigate to the property
            if isinstance(step_output, dict) and property_name in step_output:
                data = step_output[property_name]
                if isinstance(data, list):
                    logger.info(
                        f"Found {len(data)} items for for_each iteration from {for_each}"
                    )
                    return data
                else:
                    logger.warning(
                        f"Property {property_name} is not a list: {type(data)}"
                    )
                    return []
            else:
                logger.warning(
                    f"Property {property_name} not found in step output for {step_name}"
                )
                return []

        except Exception as e:
            logger.error(f"Error resolving for_each reference {for_each}: {e}")
            return []

    def _select_template(
        self, flow: ThinkingFlow, step: FlowStep, context: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Select the appropriate template for a step

        This method selects the appropriate template based on step configuration,
        flow context, and complexity. It handles template overrides and complexity-specific templates.

        Args:
            flow: Flow containing the step
            step: Step to select template for
            context: Context for template parameter replacement

        Returns:
            Tuple of (template_name, template_parameters)
        """
        # Check for template override in step config
        if hasattr(step, "config") and step.config and "template" in step.config:
            template_name = step.config["template"]
            logger.debug(f"Using template override from step config: {template_name}")
        elif hasattr(step, "config") and step.config and "template_name" in step.config:
            # Use template name from step config
            base_template_name = step.config["template_name"]
            logger.debug(f"Using template name from step config: {base_template_name}")

            # Try complexity-specific template first, fallback to base template
            complexity = context.get("complexity", "medium").lower()
            complexity_template = f"{base_template_name}_{complexity}"

            # Try to get complexity-specific template, fallback to base template
            try:
                test_content = self.template_manager.get_template(
                    complexity_template, {}
                )
                if test_content:
                    template_name = complexity_template
                    logger.debug(f"Using complexity-specific template: {template_name}")
                else:
                    template_name = base_template_name
                    logger.debug(f"Falling back to base template: {template_name}")
            except:
                template_name = base_template_name
                logger.debug(f"Falling back to base template: {template_name}")
        else:
            # Fallback: derive template name from agent_type
            template_name = getattr(step, "agent_type", "default")
            logger.warning(
                f"No template name found for step {step.step_id}, using agent_type: {template_name}"
            )

        # Prepare template parameters
        template_params = {}

        # Add context parameters
        for key, value in context.items():
            if isinstance(value, (str, int, float, bool)) or value is None:
                template_params[key] = value

        # Add step-specific parameters
        if hasattr(step, "config") and step.config:
            for key, value in step.config.items():
                if key != "template" and (
                    isinstance(value, (str, int, float, bool)) or value is None
                ):
                    template_params[key] = value

        return template_name, template_params

    def _update_execution_stats(
        self, flow_id: str, step_id: str, start_time: float, success: bool = True
    ) -> None:
        """
        Update execution statistics

        This method updates execution statistics for monitoring and performance tracking.

        Args:
            flow_id: ID of the flow
            step_id: ID of the step
            start_time: Start time of execution
            success: Whether execution was successful
        """
        execution_time = time.time() - start_time

        # Initialize stats if needed
        if flow_id not in self.execution_stats:
            self.execution_stats[flow_id] = {
                "total_executions": 0,
                "successful_executions": 0,
                "failed_executions": 0,
                "total_execution_time": 0.0,
                "steps": {},
            }

        # Update flow stats
        self.execution_stats[flow_id]["total_executions"] += 1
        if success:
            self.execution_stats[flow_id]["successful_executions"] += 1
        else:
            self.execution_stats[flow_id]["failed_executions"] += 1
        self.execution_stats[flow_id]["total_execution_time"] += execution_time

        # Initialize step stats if needed
        if step_id not in self.execution_stats[flow_id]["steps"]:
            self.execution_stats[flow_id]["steps"][step_id] = {
                "total_executions": 0,
                "successful_executions": 0,
                "failed_executions": 0,
                "total_execution_time": 0.0,
                "average_execution_time": 0.0,
            }

        # Update step stats
        step_stats = self.execution_stats[flow_id]["steps"][step_id]
        step_stats["total_executions"] += 1
        if success:
            step_stats["successful_executions"] += 1
        else:
            step_stats["failed_executions"] += 1
        step_stats["total_execution_time"] += execution_time
        step_stats["average_execution_time"] = (
            step_stats["total_execution_time"] / step_stats["total_executions"]
        )

    def _log_execution_start(
        self,
        flow: ThinkingFlow,
        step: FlowStep,
        template_name: str,
        template_params: Dict[str, Any],
    ) -> None:
        """
        Log execution start in database

        Args:
            flow: Flow being executed
            step: Step being executed
            template_name: Name of template being used
            template_params: Parameters for template
        """
        if not self.db:
            return

        try:
            # Update session status
            self.db.update_session(
                flow.session_id, current_step=step.step_id, status=flow.status.value
            )

            # Log step execution
            self.db.add_session_step(
                session_id=flow.session_id,
                step_name=step.step_name,
                step_number=flow.current_step_index,
                step_type=step.step_type,
                template_used=template_name,
                input_data=template_params,
            )

        except Exception as e:
            logger.warning(f"Failed to log execution start: {e}")

    def _log_execution_failure(
        self, flow_id: str, step_id: str, error_message: str, execution_time_ms: int
    ) -> None:
        """
        Log execution failure in database

        Args:
            flow_id: ID of the flow
            step_id: ID of the step
            error_message: Error message
            execution_time_ms: Execution time in milliseconds
        """
        if not self.db:
            return

        try:
            # Get flow
            flow = self.flow_manager.get_flow(flow_id)
            if not flow:
                return

            # Update session status
            self.db.update_session(
                flow.session_id,
                status="error",
                context={
                    "last_error": {
                        "step_id": step_id,
                        "error_message": error_message,
                        "timestamp": datetime.now().isoformat(),
                    }
                },
            )

        except Exception as e:
            logger.warning(f"Failed to log execution failure: {e}")

    def get_execution_stats(self, flow_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get execution statistics

        This method returns execution statistics for monitoring and performance tracking.

        Args:
            flow_id: Optional ID of flow to get stats for

        Returns:
            Dict containing execution statistics
        """
        if flow_id:
            # Return stats for specific flow
            return self.execution_stats.get(
                flow_id,
                {
                    "total_executions": 0,
                    "successful_executions": 0,
                    "failed_executions": 0,
                    "total_execution_time": 0.0,
                    "steps": {},
                },
            )
        else:
            # Return overall stats
            total_executions = 0
            successful_executions = 0
            failed_executions = 0
            total_execution_time = 0.0

            for flow_stats in self.execution_stats.values():
                total_executions += flow_stats["total_executions"]
                successful_executions += flow_stats["successful_executions"]
                failed_executions += flow_stats["failed_executions"]
                total_execution_time += flow_stats["total_execution_time"]

            return {
                "total_flows": len(self.execution_stats),
                "total_executions": total_executions,
                "successful_executions": successful_executions,
                "failed_executions": failed_executions,
                "total_execution_time": total_execution_time,
                "average_execution_time": (
                    total_execution_time / total_executions
                    if total_executions > 0
                    else 0.0
                ),
            }

    def monitor_execution(self, flow_id: str) -> Dict[str, Any]:
        """
        Monitor execution of a flow

        This method returns the current execution status of a flow.

        Args:
            flow_id: ID of flow to monitor

        Returns:
            Dict containing execution status
        """
        # Get flow
        flow = self.flow_manager.get_flow(flow_id)
        if not flow:
            return {"status": "not_found", "flow_id": flow_id}

        # Get flow progress
        progress = (
            flow.get_progress()
            if hasattr(flow, "get_progress")
            else {
                "status": flow.status.value,
                "current_step_index": flow.current_step_index,
                "total_steps": len(flow.steps),
            }
        )

        # Get execution stats
        stats = self.get_execution_stats(flow_id)

        # Return monitoring information
        return {
            "flow_id": flow_id,
            "status": flow.status.value,
            "progress": progress,
            "stats": stats,
            "last_updated": datetime.now().isoformat(),
        }

    def handle_error(
        self, flow_id: str, step_id: str, error: Exception
    ) -> Dict[str, Any]:
        """
        Handle execution error

        This method handles errors that occur during flow execution.
        It provides recovery options and error diagnostics.

        Args:
            flow_id: ID of flow where error occurred
            step_id: ID of step where error occurred
            error: Exception that occurred

        Returns:
            Dict containing error handling information
        """
        error_message = str(error)
        error_type = type(error).__name__

        logger.error(
            f"Error in flow {flow_id}, step {step_id}: {error_type}: {error_message}"
        )

        # Get flow
        flow = self.flow_manager.get_flow(flow_id)
        if not flow:
            return {
                "flow_id": flow_id,
                "step_id": step_id,
                "error_type": error_type,
                "error_message": error_message,
                "recovery_options": ["restart_flow"],
                "diagnostics": {"flow_found": False},
            }

        # Get step
        step = flow.steps.get(step_id)
        if not step:
            return {
                "flow_id": flow_id,
                "step_id": step_id,
                "error_type": error_type,
                "error_message": error_message,
                "recovery_options": ["restart_flow"],
                "diagnostics": {"flow_found": True, "step_found": False},
            }

        # Determine recovery options
        recovery_options = []

        # Check if step can be retried
        if hasattr(step, "can_retry") and step.can_retry():
            recovery_options.append("retry_step")

        # Check if step can be skipped
        if (
            hasattr(step, "config")
            and step.config
            and step.config.get("optional", False)
        ):
            recovery_options.append("skip_step")

        # Always allow restarting flow
        recovery_options.append("restart_flow")

        # Return error handling information
        return {
            "flow_id": flow_id,
            "step_id": step_id,
            "error_type": error_type,
            "error_message": error_message,
            "recovery_options": recovery_options,
            "diagnostics": {
                "flow_found": True,
                "step_found": True,
                "flow_status": flow.status.value,
                "step_status": step.status,
                "retry_count": step.retry_count if hasattr(step, "retry_count") else 0,
            },
        }
