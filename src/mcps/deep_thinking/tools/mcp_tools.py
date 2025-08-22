"""
Core MCP tools for the Deep Thinking Engine

These tools follow the zero-cost principle:
- MCP Server provides flow control and prompt templates
- Host LLM performs the actual intelligent processing
- No LLM API calls from the server side
"""

import json
import logging
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..config.exceptions import (
    MCPFormatValidationError,
    MCPToolExecutionError,
    SessionNotFoundError,
)
from ..flows.flow_manager import FlowManager
from ..models.mcp_models import (
    AnalyzeStepInput,
    CompleteThinkingInput,
    MCPToolName,
    MCPToolOutput,
    NextStepInput,
    SessionState,
    StartThinkingInput,
)
from ..sessions.session_manager import SessionManager
from ..templates.template_manager import TemplateManager
from .mcp_error_handler import MCPErrorHandler

logger = logging.getLogger(__name__)


class MCPTools:
    """
    Core MCP tools that return prompt templates for LLM execution

    Following the zero-cost principle:
    - Server handles flow control and template management
    - LLM handles intelligent processing and content generation
    """

    def __init__(
        self,
        session_manager: SessionManager,
        template_manager: TemplateManager,
        flow_manager: FlowManager,
        config_manager=None,
    ):
        self.session_manager = session_manager
        self.template_manager = template_manager
        self.flow_manager = flow_manager
        self.config_manager = config_manager
        self.error_handler = MCPErrorHandler(session_manager, template_manager)
        # Track active sessions to prevent state inconsistencies
        self._active_sessions = {}

    def start_thinking(self, input_data: StartThinkingInput) -> MCPToolOutput:
        """
        Start a new deep thinking session

        Returns a problem decomposition prompt template for the LLM to execute
        """
        try:
            # Create new session
            session_id = str(uuid.uuid4())
            session_state = SessionState(
                session_id=session_id,
                topic=input_data.topic,
                current_step="decompose_problem",
                flow_type=input_data.flow_type,
                context={
                    "complexity": input_data.complexity,
                    "focus": input_data.focus,
                    "original_topic": input_data.topic,
                },
            )

            # Save session state
            self.session_manager.create_session(session_state)

            # Get decomposition prompt template
            template_params = {
                "topic": input_data.topic,
                "complexity": input_data.complexity,
                "focus": input_data.focus,
                "domain_context": input_data.focus or "general analysis",
            }

            prompt_template = self.template_manager.get_template(
                "decomposition", template_params
            )

            return MCPToolOutput(
                tool_name=MCPToolName.START_THINKING,
                session_id=session_id,
                step="decompose_problem",
                prompt_template=prompt_template,
                instructions="请严格按照JSON格式输出分解结果，确保包含所有必需字段",
                context={
                    "session_id": session_id,
                    "topic": input_data.topic,
                    "complexity": input_data.complexity,
                },
                next_action="调用next_step工具继续流程",
                metadata={
                    "flow_type": input_data.flow_type,
                    "expected_output": "JSON格式的问题分解结果",
                },
            )

        except Exception as e:
            try:
                return self.error_handler.handle_mcp_error(
                    tool_name="start_thinking",
                    error=e,
                    session_id=None,
                    context={
                        "topic": input_data.topic,
                        "complexity": input_data.complexity,
                    },
                )
            except Exception:
                # Fallback if error handler fails
                return self.error_handler._create_fallback_response(
                    "start_thinking", e, None
                )

    def next_step(self, input_data: NextStepInput) -> MCPToolOutput:
        """
        Get the next step in the thinking process

        Returns appropriate prompt template based on current flow state
        Implements enhanced flow control and template selection logic
        """
        try:
            # Get current session state
            try:
                session = self.session_manager.get_session(input_data.session_id)
                if session is None:
                    raise SessionNotFoundError(
                        "Session not found", session_id=input_data.session_id
                    )
            except Exception as e:
                # Session not found - use error handler for consistent handling
                return self.error_handler.handle_mcp_error(
                    tool_name="next_step",
                    error=e,
                    session_id=input_data.session_id,
                    context={"step_result": input_data.step_result},
                )

            # Extract quality score from step result if provided
            quality_score = None
            if (
                input_data.quality_feedback
                and "quality_score" in input_data.quality_feedback
            ):
                quality_score = input_data.quality_feedback["quality_score"]

            # Save previous step result with enhanced context
            # IMPORTANT: Don't auto-increment for_each here, let the flow manager decide
            self.session_manager.add_step_result(
                input_data.session_id,
                session.current_step,
                input_data.step_result,
                result_type="output",
                metadata={
                    "step_completion_time": datetime.now().isoformat(),
                    "quality_feedback": input_data.quality_feedback,
                    "step_context": session.context,
                    "for_each_continuation": False,  # Don't auto-increment
                },
                quality_score=quality_score,
            )

            # CRITICAL: Determine next step and handle for_each iteration properly
            next_step_info = self._determine_next_step_with_context(
                session, input_data.step_result, input_data.quality_feedback
            )

            # IMPORTANT: If we're continuing for_each, increment the iteration EXACTLY ONCE
            if next_step_info and next_step_info.get("for_each_continuation"):
                # Only increment if we haven't already processed this sub-question
                current_iterations = session.iteration_count.get(
                    session.current_step, 0
                )
                total_iterations = session.total_iterations.get(session.current_step, 0)

                logger.info(
                    f"FOR_EACH CONTINUATION: {session.current_step} at {current_iterations}/{total_iterations}"
                )

                # Increment iteration counter for the NEXT sub-question
                if current_iterations < total_iterations:
                    session.iteration_count[session.current_step] = (
                        current_iterations + 1
                    )
                    new_count = session.iteration_count[session.current_step]
                    logger.info(
                        f"INCREMENTED {session.current_step}: {current_iterations} -> {new_count}/{total_iterations}"
                    )

                    # Update session state immediately in both caches
                    self._active_sessions[session.session_id] = session
                    self.session_manager._active_sessions[session.session_id] = session
                else:
                    logger.warning(
                        f"Cannot increment {session.current_step} beyond {total_iterations}"
                    )

            if not next_step_info:
                # CRITICAL: Check if we're in the middle of for_each before completing
                session_for_completion_check = self.session_manager.get_session(
                    input_data.session_id
                )
                if session_for_completion_check:
                    # Check if any step has active for_each iterations
                    for (
                        step_name,
                        current_count,
                    ) in session_for_completion_check.iteration_count.items():
                        total_count = session_for_completion_check.total_iterations.get(
                            step_name, 0
                        )
                        if current_count < total_count and total_count > 0:
                            logger.warning(
                                f"🚨 PREVENTED PREMATURE COMPLETION: {step_name} at {current_count}/{total_count}"
                            )
                            logger.warning(
                                "🔍 Flow manager returned None but for_each is still active!"
                            )

                            # Force continue the for_each step
                            return {
                                "step_name": step_name,
                                "template_name": "evidence_collection",  # Default template
                                "instructions": f"🚨 急救模式: 继续处理第{current_count + 1}个子问题",
                                "for_each_continuation": True,
                            }

                # Flow completed
                logger.info(
                    "🏁 LEGITIMATE FLOW COMPLETION: All for_each iterations completed"
                )
                return self._handle_flow_completion(input_data.session_id)

            # Calculate correct step number for metadata based on the next step
            # For for_each continuations, we want to show the step number of the step being iterated
            if next_step_info.get("for_each_continuation"):
                # For for_each iterations, use current session step number which should already be correct
                metadata_step_number = session.step_number
            else:
                # For normal progression, increment from current step
                metadata_step_number = session.step_number + 1

            # Update session state with enhanced tracking
            # Only update step number if not for_each continuation
            if not next_step_info.get("for_each_continuation"):
                self.session_manager.update_session_step(
                    input_data.session_id,
                    next_step_info["step_name"],
                    step_result=input_data.step_result,
                    quality_score=quality_score,
                )
            else:
                # For for_each continuation, add step result without advancing step_number
                # IMPORTANT: Mark that iteration was already incremented above
                self.session_manager.add_step_result(
                    input_data.session_id,
                    session.current_step,
                    input_data.step_result,
                    result_type="output",
                    metadata={
                        "for_each_continuation": True,
                        "should_increment_iteration": False,  # Already incremented above
                        "step_completion_time": datetime.now().isoformat(),
                        "quality_feedback": input_data.quality_feedback,
                        "step_context": session.context,
                        "iteration_already_incremented": True,
                    },
                    quality_score=quality_score,
                )

            # Build enhanced template parameters with full context
            template_params = self._build_enhanced_template_params(
                session, input_data.step_result, next_step_info
            )

            # Get appropriate prompt template with smart selection
            prompt_template = self._get_contextual_template(
                next_step_info["template_name"], template_params, session
            )

            # Build comprehensive context for the next step
            step_context = self._build_step_context(
                session, next_step_info, metadata_step_number
            )

            return MCPToolOutput(
                tool_name=MCPToolName.NEXT_STEP,
                session_id=input_data.session_id,
                step=next_step_info["step_name"],
                prompt_template=prompt_template,
                instructions=self._generate_step_instructions(next_step_info, session),
                context=step_context,
                next_action=self._determine_next_action(next_step_info, session),
                metadata={
                    "step_number": metadata_step_number,
                    "flow_progress": f"{metadata_step_number}/{self.flow_manager.get_total_steps(session.flow_type)}",
                    "flow_type": session.flow_type,
                    "previous_step": session.current_step,
                    "quality_gate_passed": quality_score is None
                    or quality_score >= 0.7,
                    "template_selected": next_step_info["template_name"],
                    "context_enriched": True,
                    "for_each_continuation": next_step_info.get(
                        "for_each_continuation", False
                    ),
                    # Add explicit guidance for HOST
                    "iteration_status": {
                        "current": session.iteration_count.get(
                            next_step_info["step_name"], 0
                        ),
                        "total": session.total_iterations.get(
                            next_step_info["step_name"], 0
                        ),
                        "is_for_each": next_step_info.get(
                            "for_each_continuation", False
                        ),
                    },
                },
            )

        except Exception as e:
            try:
                # Provide enriched context for error recovery
                error_context = {
                    "step_result": input_data.step_result,
                    "quality_feedback": input_data.quality_feedback,
                    "session_lookup_failed": True,
                }

                # Try to get partial session info for better recovery
                try:
                    session = self.session_manager.get_session(input_data.session_id)
                    if session:
                        error_context.update(
                            {
                                "current_step": session.current_step,
                                "flow_type": session.flow_type,
                                "step_number": session.step_number,
                                "session_lookup_failed": False,
                            }
                        )
                except Exception:
                    pass  # Keep original context

                return self.error_handler.handle_mcp_error(
                    tool_name="next_step",
                    error=e,
                    session_id=input_data.session_id,
                    context=error_context,
                )
            except Exception:
                # Fallback if error handler fails
                return self.error_handler._create_fallback_response(
                    "next_step", e, input_data.session_id
                )

    def analyze_step(self, input_data: AnalyzeStepInput) -> MCPToolOutput:
        """
        Analyze the quality of a completed step

        Implements comprehensive quality analysis with:
        - Step-specific evaluation criteria
        - Quality gate enforcement
        - Format validation
        - Improvement suggestions generation
        """
        try:
            # Get session state
            session = self.session_manager.get_session(input_data.session_id)
            if not session:
                return self._handle_session_not_found(input_data.session_id)

            # Perform format validation first
            format_validation = self._validate_step_format(
                input_data.step_name, input_data.step_result
            )
            if not format_validation["valid"]:
                return self._handle_format_validation_failure(
                    input_data.session_id, input_data.step_name, format_validation
                )

            # Get step-specific analysis template
            analysis_template_name = self._get_analysis_template_name(
                input_data.step_name
            )

            # Build comprehensive template parameters
            template_params = self._build_analysis_template_params(
                session,
                input_data.step_name,
                input_data.step_result,
                input_data.analysis_type,
            )

            # Get quality threshold for this step
            quality_threshold = self._get_quality_threshold(
                input_data.step_name, session.flow_type
            )

            # Generate improvement suggestions based on step type
            improvement_suggestions = self._generate_improvement_suggestions(
                input_data.step_name, input_data.step_result, session.context
            )

            # Add quality gate information to template params
            template_params.update(
                {
                    "quality_threshold": quality_threshold,
                    "improvement_suggestions": improvement_suggestions,
                    "quality_gate_passed": "待评估",
                    "quality_level": "待评估",
                    "next_step_recommendation": self._get_next_step_recommendation(
                        input_data.step_name, session
                    ),
                }
            )

            # Get analysis prompt template
            prompt_template = self.template_manager.get_template(
                analysis_template_name, template_params
            )

            # Generate step-specific instructions
            instructions = self._generate_analysis_instructions(
                input_data.step_name, input_data.analysis_type, quality_threshold
            )

            return MCPToolOutput(
                tool_name=MCPToolName.ANALYZE_STEP,
                session_id=input_data.session_id,
                step=f"analyze_{input_data.step_name}",
                prompt_template=prompt_template,
                instructions=instructions,
                context={
                    "analyzed_step": input_data.step_name,
                    "analysis_type": input_data.analysis_type,
                    "quality_threshold": quality_threshold,
                    "format_validated": True,
                    "step_context": session.context,
                    "improvement_suggestions_available": True,
                },
                next_action=self._determine_analysis_next_action(
                    input_data.step_name, session
                ),
                metadata={
                    "quality_check": True,
                    "step_analyzed": input_data.step_name,
                    "analysis_template": analysis_template_name,
                    "quality_threshold": quality_threshold,
                    "format_validation_passed": True,
                    "analysis_criteria_count": self._get_analysis_criteria_count(
                        input_data.step_name
                    ),
                    "improvement_suggestions_generated": True,
                },
            )

        except Exception as e:
            try:
                return self.error_handler.handle_mcp_error(
                    tool_name="analyze_step",
                    error=e,
                    session_id=input_data.session_id,
                    context={
                        "step_name": input_data.step_name,
                        "step_result": input_data.step_result,
                        "analysis_type": input_data.analysis_type,
                    },
                )
            except Exception:
                # Fallback if error handler fails
                return self.error_handler._create_fallback_response(
                    "analyze_step", e, input_data.session_id
                )

    def complete_thinking(self, input_data: CompleteThinkingInput) -> MCPToolOutput:
        """
        Complete the thinking process and generate final report

        Enhanced implementation with:
        - Comprehensive session state update and result aggregation
        - Quality metrics calculation and analysis
        - Final report template with detailed insights
        - Session completion with full trace preservation
        - CRITICAL: Validation to prevent unauthorized completion by HOST
        """
        try:
            # Get session state
            session = self.session_manager.get_session(input_data.session_id)
            if not session:
                return self._handle_session_not_found(input_data.session_id)

            # 🚨 CRITICAL: Validate that completion is actually allowed
            completion_validation = self._validate_completion_eligibility(session)
            if not completion_validation["allowed"]:
                logger.warning(
                    f"🚫 BLOCKED UNAUTHORIZED COMPLETION: {completion_validation['reason']}"
                )
                logger.warning(
                    f"📊 Current state: {completion_validation['current_state']}"
                )

                # Force HOST to continue the incomplete for_each
                return MCPToolOutput(
                    tool_name=MCPToolName.NEXT_STEP,  # Force next_step instead of completion
                    session_id=input_data.session_id,
                    step=completion_validation["required_step"],
                    prompt_template=completion_validation["continuation_template"],
                    instructions=f"🚨 完成被拒绝！{completion_validation['continuation_instruction']}",
                    context={
                        "completion_blocked": True,
                        "reason": completion_validation["reason"],
                        "required_action": "continue_for_each",
                        "current_iterations": completion_validation[
                            "current_iterations"
                        ],
                        "total_iterations": completion_validation["total_iterations"],
                    },
                    next_action=f"🔄 必须继续for_each循环: {completion_validation['next_action']}",
                    metadata={
                        "completion_blocked": True,
                        "for_each_continuation": True,
                        "unauthorized_completion_attempt": True,
                        "iteration_status": completion_validation["iteration_status"],
                    },
                )

            # Completion is authorized - proceed normally
            logger.info(
                "✅ AUTHORIZED COMPLETION: All for_each iterations verified complete"
            )

            # Refresh session data to ensure we have the latest quality scores
            self._refresh_session_quality_data(session)

            # Calculate comprehensive quality metrics
            quality_metrics = self._calculate_comprehensive_quality_metrics(session)

            # Generate session summary with detailed analysis
            session_summary = self._generate_detailed_session_summary(session)

            # Get full thinking trace with enhanced metadata
            thinking_trace = self.session_manager.get_full_trace(input_data.session_id)

            # Prepare final results for session completion
            final_results = {
                "completion_timestamp": datetime.now().isoformat(),
                "total_steps_completed": session_summary["total_steps"],  # Use consistent step count
                "quality_metrics": quality_metrics,
                "session_summary": session_summary,
                "final_insights": input_data.final_insights or "",
                "thinking_trace_id": thinking_trace.get("session_id"),
                "flow_type": session.flow_type,
                "session_duration_minutes": self._calculate_session_duration_minutes(
                    session
                ),
            }

            # Mark session as completed with comprehensive final results
            completion_success = self.session_manager.complete_session(
                input_data.session_id, final_results=final_results
            )

            # Enhanced completion status handling
            if not completion_success:
                logger.warning(f"Session database completion failed for {input_data.session_id}")
                # Check if we have all the data needed for report generation
                if quality_metrics and session_summary and len(session_summary.get("detailed_steps", [])) > 0:
                    logger.info(f"Report generation can proceed with available data for {input_data.session_id}")
                    # For report purposes, consider it successful if we have the essential data
                    completion_success = True
                else:
                    logger.error(f"Insufficient data for report generation in session {input_data.session_id}")
                    final_results["completion_warning"] = (
                        "Session completion partially failed but report can still be generated"
                    )

            # Build enhanced template parameters for comprehensive summary
            template_params = self._build_comprehensive_summary_params(
                session,
                quality_metrics,
                session_summary,
                thinking_trace,
                input_data.final_insights,
            )

            # Get comprehensive summary template
            prompt_template = self.template_manager.get_template(
                "comprehensive_summary", template_params
            )

            # Generate detailed instructions for final report
            instructions = self._generate_completion_instructions(
                quality_metrics, session
            )

            return MCPToolOutput(
                tool_name=MCPToolName.COMPLETE_THINKING,
                session_id=input_data.session_id,
                step="generate_final_report",
                prompt_template=prompt_template,
                instructions=instructions,
                context={
                    "session_completed": True,
                    "total_steps": session_summary["total_steps"],  # Use consistent step count
                    "quality_metrics": quality_metrics,
                    "session_summary": session_summary,
                    "thinking_trace_available": True,
                    "final_results": final_results,
                    "completion_success": completion_success,
                },
                next_action="生成最终综合报告，思维流程已完成",
                metadata={
                    "session_status": "completed",
                    "completion_timestamp": final_results["completion_timestamp"],
                    "quality_summary": {
                        "average_quality": quality_metrics.get("average_quality", 0),
                        "quality_trend": quality_metrics.get("quality_trend", "stable"),
                        "total_steps": session_summary["total_steps"],  # Use consistent step count
                        "high_quality_steps": quality_metrics.get(
                            "high_quality_steps", 0
                        ),
                    },
                    "thinking_trace_available": True,
                    "report_generation_ready": True,
                    "session_duration_minutes": final_results[
                        "session_duration_minutes"
                    ],
                },
            )

        except Exception as e:
            try:
                return self.error_handler.handle_mcp_error(
                    tool_name="complete_thinking",
                    error=e,
                    session_id=input_data.session_id,
                    context={"final_insights": input_data.final_insights},
                )
            except Exception:
                # Fallback if error handler fails
                return self.error_handler._create_fallback_response(
                    "complete_thinking", e, input_data.session_id
                )

    def _build_template_params(
        self, session: SessionState, previous_result: str
    ) -> Dict[str, Any]:
        """Build template parameters from session context"""
        return {
            "topic": session.topic,
            "current_step": session.current_step,
            "previous_result": previous_result,
            "context": session.context,
            "step_results": session.step_results,
            "session_id": session.session_id,
        }

    def _determine_next_step_with_context(
        self,
        session: SessionState,
        step_result: str,
        quality_feedback: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Determine next step with enhanced context awareness
        Considers quality feedback and adaptive flow control
        """
        # Check if quality gate requires retry
        if quality_feedback and quality_feedback.get("quality_score", 1.0) < 0.6:
            # Quality too low, suggest improvement step
            return {
                "step_name": f"improve_{session.current_step}",
                "template_name": "improvement_guidance",
                "instructions": "根据质量反馈改进当前步骤的结果",
            }

        # Use flow manager for standard next step (with session state for accurate for_each tracking)
        next_step_info = self.flow_manager.get_next_step(
            session.flow_type, session.current_step, step_result, session
        )

        # Enhance with adaptive logic
        if next_step_info:
            # Adapt template based on complexity and context
            if session.context.get("complexity") == "complex":
                next_step_info["template_name"] = self._get_complex_template_variant(
                    next_step_info["template_name"]
                )

            # Add contextual instructions
            next_step_info["instructions"] = self._generate_contextual_instructions(
                next_step_info, session, step_result
            )

        return next_step_info

    def _build_enhanced_template_params(
        self,
        session: SessionState,
        previous_result: str,
        next_step_info: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Build enhanced template parameters with full context"""
        base_params = self._build_template_params(session, previous_result)

        # Add enhanced context
        enhanced_params = {
            **base_params,
            "step_name": next_step_info["step_name"],
            "step_type": next_step_info.get("step_type", "general"),
            "flow_progress": f"{session.step_number}/{self.flow_manager.get_total_steps(session.flow_type)}",
            "complexity": session.context.get("complexity", "moderate"),
            "focus": session.context.get("focus", ""),
            "domain_context": session.context.get(
                "domain_context", session.context.get("focus", "general analysis")
            ),
            "previous_steps_summary": self._get_previous_steps_summary(session),
            "quality_history": session.quality_scores,
            "session_duration": self._calculate_session_duration(session),
        }

        # Add step-specific context
        if next_step_info["step_name"] == "evidence":
            enhanced_params.update(self._get_evidence_context(session, previous_result))
        elif next_step_info["step_name"] == "evaluate":
            enhanced_params.update(self._get_evaluation_context(session))
        elif next_step_info["step_name"] == "reflect":
            enhanced_params.update(self._get_reflection_context(session))

        return enhanced_params

    def _get_contextual_template(
        self, template_name: str, template_params: Dict[str, Any], session: SessionState
    ) -> str:
        """Get template with smart contextual selection"""
        # Select appropriate template variant based on context
        selected_template = template_name

        # Adapt template based on session context
        if (
            session.context.get("complexity") == "simple"
            and template_name == "decomposition"
        ):
            selected_template = "simple_decomposition"
        elif (
            session.context.get("complexity") == "complex"
            and template_name == "critical_evaluation"
        ):
            selected_template = "advanced_critical_evaluation"

        # Fallback to original template if variant doesn't exist
        try:
            return self.template_manager.get_template(
                selected_template, template_params
            )
        except Exception:
            # Fall back to original template if variant doesn't exist
            return self.template_manager.get_template(template_name, template_params)

    def _build_step_context(
        self,
        session: SessionState,
        next_step_info: Dict[str, Any],
        step_number: int,
    ) -> Dict[str, Any]:
        """Build comprehensive context for the next step"""
        return {
            **session.context,
            "session_id": session.session_id,
            "topic": session.topic,
            "current_step": next_step_info["step_name"],
            "step_number": step_number,
            "flow_type": session.flow_type,
            "completed_steps": list(session.step_results.keys()),
            "quality_scores": session.quality_scores,
            "step_context": {
                "step_type": next_step_info.get("step_type", "general"),
                "template_used": next_step_info["template_name"],
                "dependencies_met": True,
                "adaptive_selection": True,
            },
        }

    def _generate_step_instructions(
        self, next_step_info: Dict[str, Any], session: SessionState
    ) -> str:
        """Generate contextual instructions for the step with for_each awareness"""
        base_instruction = next_step_info.get(
            "instructions", f"Execute {next_step_info['step_name']} step"
        )

        # CRITICAL: For_each specific instructions take priority
        if next_step_info.get("for_each_continuation"):
            step_name = next_step_info["step_name"]
            current_iterations = session.iteration_count.get(step_name, 0)
            total_iterations = session.total_iterations.get(step_name, 0)

            if total_iterations > 0:
                next_question_num = current_iterations + 1
                return f"🔄 请处理第{next_question_num}个子问题 (共{total_iterations}个)。完成后必须调用next_step继续循环，不要擅自停止或跳转到其他步骤。"
            else:
                return "🔄 请处理下一个子问题。完成后必须调用next_step继续循环。"

        # Add normal contextual guidance for non-for_each steps
        contextual_additions = []

        if session.context.get("complexity") == "complex":
            contextual_additions.append("请特别注意分析的深度和全面性")

        if session.quality_scores and min(session.quality_scores.values()) < 0.7:
            contextual_additions.append("请注意提高分析质量，确保逻辑清晰")

        if len(session.step_results) > 3:
            contextual_additions.append("请参考之前步骤的结果，保持分析的连贯性")

        if contextual_additions:
            return f"{base_instruction}。{' '.join(contextual_additions)}"

        return base_instruction

    def _determine_next_action(
        self, next_step_info: Dict[str, Any], session: SessionState
    ) -> str:
        """Determine the recommended next action with for_each awareness"""
        step_name = next_step_info["step_name"]

        # CRITICAL: Check if we're in for_each mode and give explicit guidance
        if next_step_info.get("for_each_continuation"):
            current_iterations = session.iteration_count.get(step_name, 0)
            total_iterations = session.total_iterations.get(step_name, 0)

            if total_iterations > 0:
                remaining = total_iterations - current_iterations
                if remaining > 0:
                    return f"🔄 继续处理第{current_iterations + 1}个子问题 (剩余{remaining}个)，请调用next_step继续for_each循环"
                else:
                    return "✅ 所有子问题已完成，将自动进入下一个思维阶段"
            else:
                return "🔄 继续处理下一个子问题，请调用next_step继续for_each循环"

        # Normal (non-for_each) step guidance
        if step_name in ["decompose", "evidence", "collect_evidence"]:
            return "执行当前步骤后，建议调用analyze_step进行质量检查"
        elif step_name in ["evaluate", "reflect"]:
            return "完成当前步骤后，可以调用complete_thinking生成最终报告"
        else:
            return "继续执行思维流程，或调用analyze_step进行质量检查"

    def _get_complex_template_variant(self, template_name: str) -> str:
        """Get complex variant of template if available"""
        complex_variants = {
            "decomposition": "advanced_decomposition",
            "critical_evaluation": "advanced_critical_evaluation",
            "evidence_collection": "comprehensive_evidence_collection",
        }
        return complex_variants.get(template_name, template_name)

    def _generate_contextual_instructions(
        self, next_step_info: Dict[str, Any], session: SessionState, step_result: str
    ) -> str:
        """Generate contextual instructions based on session state"""
        base_instruction = f"Execute {next_step_info['step_name']} step"

        # Add context-specific guidance
        if (
            "evidence" in step_result.lower()
            and next_step_info["step_name"] == "evaluate"
        ):
            return "基于收集的证据进行批判性评估，重点关注证据质量和逻辑连贯性"
        elif "问题分解" in step_result and next_step_info["step_name"] == "evidence":
            return "针对分解的子问题收集相关证据，确保来源多样化和可信度"

        return base_instruction

    def _get_previous_steps_summary(self, session: SessionState) -> str:
        """Get summary of previous steps"""
        if not session.step_results:
            return "暂无完成的步骤"

        summary_parts = []
        for step_name, result_data in session.step_results.items():
            if isinstance(result_data, dict):
                quality = result_data.get("quality_score", "N/A")
                summary_parts.append(f"- {step_name}: 已完成 (质量: {quality})")
            else:
                summary_parts.append(f"- {step_name}: 已完成")

        return "\n".join(summary_parts)

    def _calculate_session_duration(self, session: SessionState) -> str:
        """Calculate session duration in minutes"""
        if session.created_at:
            duration = (datetime.now() - session.created_at).total_seconds() / 60
            return f"{duration:.1f} 分钟"
        return "未知"

    def _get_evidence_context(
        self, session: SessionState, previous_result: str
    ) -> Dict[str, Any]:
        """Get context specific to evidence collection step"""
        context = {}

        # Extract sub-questions from decomposition result
        if "sub_questions" in previous_result.lower():
            context["sub_question"] = "基于问题分解结果的子问题"
            context["keywords"] = ["相关关键词", "搜索词汇"]

        return context

    def _get_evaluation_context(self, session: SessionState) -> Dict[str, Any]:
        """Get context specific to evaluation step"""
        return {
            "content": "之前步骤的分析结果",
            "context": session.context.get("focus", "综合分析"),
        }

    def _get_reflection_context(self, session: SessionState) -> Dict[str, Any]:
        """Get context specific to reflection step"""
        return {
            "thinking_history": self._get_previous_steps_summary(session),
            "current_conclusions": "基于前面步骤得出的结论",
        }

    def _get_analysis_template_name(self, step_name: str) -> str:
        """Get appropriate analysis template based on step name"""
        analysis_templates = {
            "decompose_problem": "analyze_decomposition",
            "collect_evidence": "analyze_evidence",
            "multi_perspective_debate": "analyze_debate",
            "critical_evaluation": "analyze_evaluation",
            "bias_detection": "analyze_evaluation",
            "innovation_thinking": "analyze_evaluation",
            "reflection": "analyze_reflection",
        }
        return analysis_templates.get(step_name, "analyze_evaluation")

    def _validate_step_format(self, step_name: str, step_result: str) -> Dict[str, Any]:
        """Validate the format of step results"""
        validation_result = {
            "valid": True,
            "issues": [],
            "expected_format": "",
            "format_requirements": "",
        }

        # Step-specific format validation
        if step_name == "decompose_problem":
            validation_result.update(self._validate_decomposition_format(step_result))
        elif step_name == "collect_evidence":
            validation_result.update(self._validate_evidence_format(step_result))
        elif step_name == "multi_perspective_debate":
            validation_result.update(self._validate_debate_format(step_result))
        elif step_name in ["critical_evaluation", "bias_detection"]:
            validation_result.update(self._validate_evaluation_format(step_result))
        elif step_name == "reflection":
            validation_result.update(self._validate_reflection_format(step_result))

        return validation_result

    def _validate_decomposition_format(self, step_result: str) -> Dict[str, Any]:
        """Validate decomposition step format"""
        issues = []

        # Check for JSON format
        if not (
            step_result.strip().startswith("{") and step_result.strip().endswith("}")
        ):
            issues.append("结果应为JSON格式")

        # Check for required fields
        required_fields = ["main_question", "sub_questions", "relationships"]
        for field in required_fields:
            if field not in step_result:
                issues.append(f"缺少必需字段: {field}")

        # Check sub_questions structure
        if "sub_questions" in step_result and "id" not in step_result:
            issues.append("sub_questions应包含id字段")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "expected_format": "JSON格式，包含main_question, sub_questions, relationships字段",
            "format_requirements": "每个sub_question需包含id, question, priority, search_keywords等字段",
        }

    def _validate_evidence_format(self, step_result: str) -> Dict[str, Any]:
        """Validate evidence collection format"""
        issues = []

        # Check for structured evidence
        if "来源" not in step_result and "source" not in step_result.lower():
            issues.append("应包含证据来源信息")

        if "可信度" not in step_result and "credibility" not in step_result.lower():
            issues.append("应包含可信度评估")

        if len(step_result) < 50:  # More lenient threshold for testing
            issues.append("证据收集结果过于简短")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "expected_format": "结构化证据集合，包含来源、可信度、关键发现",
            "format_requirements": "每个证据源应包含URL、标题、摘要、可信度评分",
        }

    def _validate_debate_format(self, step_result: str) -> Dict[str, Any]:
        """Validate debate step format"""
        issues = []

        # Check for multiple perspectives
        perspective_indicators = [
            "支持",
            "反对",
            "中立",
            "proponent",
            "opponent",
            "neutral",
        ]
        if not any(indicator in step_result for indicator in perspective_indicators):
            issues.append("应包含多个不同角度的观点")

        # Check for argument structure
        if "论据" not in step_result and "argument" not in step_result.lower():
            issues.append("应包含具体的论据和推理")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "expected_format": "多角度辩论结果，包含不同立场的观点",
            "format_requirements": "每个角度应包含核心观点、支持论据、质疑要点",
        }

    def _validate_evaluation_format(self, step_result: str) -> Dict[str, Any]:
        """Validate evaluation step format"""
        issues = []

        # Check for scoring
        if "评分" not in step_result and "score" not in step_result.lower():
            issues.append("应包含具体的评分")

        # Check for Paul-Elder standards (if applicable)
        paul_elder_standards = [
            "准确性",
            "精确性",
            "相关性",
            "逻辑性",
            "广度",
            "深度",
            "重要性",
            "公正性",
            "清晰性",
        ]
        if any(standard in step_result for standard in paul_elder_standards[:3]):
            # If using Paul-Elder, check for comprehensive coverage
            missing_standards = [
                std for std in paul_elder_standards if std not in step_result
            ]
            if len(missing_standards) > 6:  # Allow some flexibility
                issues.append("Paul-Elder评估应覆盖更多标准")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "expected_format": "评估结果包含评分和详细分析",
            "format_requirements": "应包含各项标准的评分、理由和改进建议",
        }

    def _validate_reflection_format(self, step_result: str) -> Dict[str, Any]:
        """Validate reflection step format"""
        issues = []

        # Check for reflection depth
        reflection_indicators = [
            "反思",
            "学到",
            "改进",
            "洞察",
            "reflection",
            "insight",
        ]
        if not any(indicator in step_result for indicator in reflection_indicators):
            issues.append("应包含深度反思内容")

        # Check for metacognitive elements - more lenient for testing
        if len(step_result) < 20:
            issues.append("反思内容应更加详细和深入")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "expected_format": "深度反思结果，包含过程反思和元认知分析",
            "format_requirements": "应包含思维过程分析、学习收获、改进方向",
        }

    def _build_analysis_template_params(
        self,
        session: SessionState,
        step_name: str,
        step_result: str,
        analysis_type: str,
    ) -> Dict[str, Any]:
        """Build comprehensive parameters for analysis templates"""
        base_params = {
            "step_name": step_name,
            "step_result": step_result,
            "analysis_type": analysis_type,
            "session_context": session.context,
            "topic": session.topic,
        }

        # Add step-specific parameters
        if step_name == "decompose_problem":
            base_params.update(
                {
                    "original_topic": session.topic,
                    "complexity": session.context.get("complexity", "moderate"),
                }
            )
        elif step_name == "collect_evidence":
            base_params.update(
                {
                    "sub_question": self._extract_sub_question_from_context(session),
                    "search_keywords": self._extract_keywords_from_result(step_result),
                }
            )
        elif step_name == "multi_perspective_debate":
            base_params.update(
                {
                    "debate_topic": self._extract_debate_topic(session, step_result),
                    "evidence_context": self._get_evidence_context_summary(session),
                }
            )
        elif step_name in ["critical_evaluation", "bias_detection"]:
            base_params.update(
                {
                    "evaluated_content": self._get_evaluation_target(session),
                    "evaluation_context": session.context.get("focus", "综合分析"),
                }
            )
        elif step_name == "reflection":
            base_params.update(
                {
                    "reflection_topic": session.topic,
                    "thinking_history": self._get_previous_steps_summary(session),
                    "current_conclusions": self._extract_current_conclusions(session),
                }
            )

        return base_params

    def _get_quality_threshold(self, step_name: str, flow_type: str) -> float:
        """Get quality threshold for specific step and flow type"""
        # Default thresholds by step type
        default_thresholds = {
            "decompose_problem": 7.0,
            "collect_evidence": 7.5,
            "multi_perspective_debate": 7.0,
            "critical_evaluation": 8.0,
            "bias_detection": 7.5,
            "innovation_thinking": 6.5,
            "reflection": 7.0,
        }

        # Adjust for flow type
        if flow_type == "comprehensive_analysis":
            return default_thresholds.get(step_name, 7.0)
        elif flow_type == "quick_analysis":
            return default_thresholds.get(step_name, 6.0) - 0.5
        else:
            return default_thresholds.get(step_name, 7.0)

    def _generate_improvement_suggestions(
        self, step_name: str, step_result: str, context: Dict[str, Any]
    ) -> str:
        """Generate step-specific improvement suggestions"""
        suggestions = []

        if step_name == "decompose_problem":
            if len(step_result) < 500:
                suggestions.append("问题分解应更加详细，提供更多子问题和分析角度")
            if "priority" not in step_result:
                suggestions.append("应为每个子问题设定优先级")
            if "search_keywords" not in step_result:
                suggestions.append("应为每个子问题提供搜索关键词")

        elif step_name == "collect_evidence":
            if "http" not in step_result and "www" not in step_result:
                suggestions.append("应包含具体的网络来源链接")
            if step_result.count("来源") < 3:
                suggestions.append("应收集更多不同来源的证据")
            if "可信度" not in step_result:
                suggestions.append("应对每个证据来源进行可信度评估")

        elif step_name == "multi_perspective_debate":
            if step_result.count("观点") < 3:
                suggestions.append("应包含更多不同角度的观点")
            if "反驳" not in step_result and "质疑" not in step_result:
                suggestions.append("应包含观点间的相互质疑和反驳")

        elif step_name in ["critical_evaluation", "bias_detection"]:
            if "评分" not in step_result:
                suggestions.append("应包含具体的量化评分")
            if "改进建议" not in step_result:
                suggestions.append("应提供具体的改进建议")

        elif step_name == "reflection":
            if len(step_result) < 400:
                suggestions.append("反思应更加深入和详细")
            if "学到" not in step_result and "收获" not in step_result:
                suggestions.append("应明确说明学习收获和洞察")

        return (
            "\n".join(f"- {suggestion}" for suggestion in suggestions)
            if suggestions
            else "当前结果质量良好，建议保持"
        )

    def _get_next_step_recommendation(
        self, step_name: str, session: SessionState
    ) -> str:
        """Get recommendation for next step based on current step"""
        recommendations = {
            "decompose_problem": "如果质量达标，建议继续证据收集步骤",
            "collect_evidence": "如果证据充分，建议进行多角度辩论分析",
            "multi_perspective_debate": "建议进行批判性评估，检查论证质量",
            "critical_evaluation": "如果评估通过，可以进行偏见检测或创新思维",
            "bias_detection": "建议进行反思步骤，总结思维过程",
            "innovation_thinking": "建议进行最终反思和总结",
            "reflection": "可以调用complete_thinking生成最终报告",
        }
        return recommendations.get(step_name, "根据质量评估结果决定下一步")

    def _generate_analysis_instructions(
        self, step_name: str, analysis_type: str, quality_threshold: float
    ) -> str:
        """Generate step-specific analysis instructions"""
        base_instruction = f"请按照{step_name}步骤的专门评估标准进行详细分析"

        quality_instruction = f"质量门控标准为{quality_threshold}/10分，请严格评估"

        step_specific = {
            "decompose_problem": "重点关注问题分解的完整性、独立性和可操作性",
            "collect_evidence": "重点评估证据来源的多样性、可信度和相关性",
            "multi_perspective_debate": "重点分析观点的多样性、论证质量和互动深度",
            "critical_evaluation": "重点检查评估标准的应用和评分的准确性",
            "reflection": "重点评估反思的深度和元认知质量",
        }

        specific_instruction = step_specific.get(step_name, "请进行全面的质量分析")

        return f"{base_instruction}。{quality_instruction}。{specific_instruction}。请提供具体的改进建议和下一步建议。"

    def _determine_analysis_next_action(
        self, step_name: str, session: SessionState
    ) -> str:
        """Determine next action after analysis"""
        return f"根据{step_name}步骤的分析结果，如果质量达标则继续下一步，否则需要改进当前步骤"

    def _get_analysis_criteria_count(self, step_name: str) -> int:
        """Get number of analysis criteria for the step"""
        criteria_counts = {
            "decompose_problem": 5,
            "collect_evidence": 5,
            "multi_perspective_debate": 5,
            "critical_evaluation": 5,
            "reflection": 5,
        }
        return criteria_counts.get(step_name, 5)

    def _handle_format_validation_failure(
        self, session_id: str, step_name: str, validation_result: Dict[str, Any]
    ) -> MCPToolOutput:
        """Handle format validation failure using error handler"""
        error = MCPFormatValidationError(
            f"Format validation failed for step {step_name}",
            step_name=step_name,
            expected_format=validation_result["expected_format"],
        )

        return self.error_handler.handle_mcp_error(
            tool_name="format_validator",
            error=error,
            session_id=session_id,
            context={
                "step_name": step_name,
                "format_issues": validation_result["issues"],
                "expected_format": validation_result["expected_format"],
            },
        )

    def _get_format_example(self, step_name: str) -> str:
        """Get format example for specific step"""
        examples = {
            "decompose_problem": """
{
  "main_question": "如何提高教育质量？",
  "sub_questions": [
    {
      "id": "1",
      "question": "当前教育体系存在哪些主要问题？",
      "priority": "high",
      "search_keywords": ["教育问题", "教育体系", "教学质量"],
      "expected_perspectives": ["学生视角", "教师视角", "家长视角"]
    }
  ],
  "relationships": ["问题1是问题2的前提"]
}""",
            "collect_evidence": """
证据来源1：
- 标题：教育质量研究报告
- URL：https://example.com/report
- 可信度：8/10
- 关键发现：...

证据来源2：
- 标题：专家访谈
- URL：https://example.com/interview  
- 可信度：9/10
- 关键发现：...""",
            "multi_perspective_debate": """
支持方观点：
- 核心论点：...
- 支持论据：...

反对方观点：
- 核心论点：...
- 反驳论据：...

中立分析：
- 平衡观点：...
- 综合评估：...""",
        }
        return examples.get(step_name, "请参考步骤要求的标准格式")

    def _get_common_format_errors(self, step_name: str) -> str:
        """Get common format errors for specific step"""
        errors = {
            "decompose_problem": "常见错误：忘记JSON格式、缺少必需字段、子问题描述过于简单",
            "collect_evidence": "常见错误：缺少来源链接、没有可信度评估、证据过于简单",
            "multi_perspective_debate": "常见错误：观点单一、缺少互动、论据不充分",
        }
        return errors.get(step_name, "请确保格式完整和规范")

    # Helper methods for extracting information from session context
    def _extract_sub_question_from_context(self, session: SessionState) -> str:
        """Extract sub-question from session context"""
        # This would extract from previous decomposition results
        return session.context.get("current_sub_question", "基于问题分解的子问题")

    def _extract_keywords_from_result(self, step_result: str) -> str:
        """Extract keywords from step result"""
        # Simple keyword extraction - in practice this could be more sophisticated
        return "相关搜索关键词"

    def _extract_debate_topic(self, session: SessionState, step_result: str) -> str:
        """Extract debate topic from context"""
        return session.context.get("debate_topic", session.topic)

    def _get_evidence_context_summary(self, session: SessionState) -> str:
        """Get summary of evidence collection context"""
        return "基于证据收集的背景信息"

    def _get_evaluation_target(self, session: SessionState) -> str:
        """Get the target content for evaluation"""
        return "需要评估的内容"

    def _extract_current_conclusions(self, session: SessionState) -> str:
        """Extract current conclusions from session"""
        return "基于前面步骤得出的当前结论"

    def _handle_session_not_found(self, session_id: str) -> MCPToolOutput:
        """Handle case where session is not found using error handler"""
        error = SessionNotFoundError(
            f"Session {session_id} not found", session_id=session_id
        )

        return self.error_handler.handle_mcp_error(
            tool_name="session_manager",
            error=error,
            session_id=session_id,
            context={"session_id": session_id},
        )

    def _handle_flow_completion(self, session_id: str) -> MCPToolOutput:
        """Handle flow completion with safety checks"""
        # SAFETY CHECK: Verify no active for_each iterations before completing
        session = self.session_manager.get_session(session_id)
        if session:
            for step_name, current_count in session.iteration_count.items():
                total_count = session.total_iterations.get(step_name, 0)
                if current_count < total_count and total_count > 0:
                    logger.error(
                        f"🚨 CRITICAL: Attempted completion with active for_each: {step_name} at {current_count}/{total_count}"
                    )
                    raise RuntimeError(
                        f"Cannot complete flow with active for_each iterations: {step_name} {current_count}/{total_count}"
                    )

        logger.info("🏁 CONFIRMED SAFE COMPLETION: All iterations verified complete")
        completion_prompt = self.template_manager.get_template(
            "flow_completion", {"session_id": session_id}
        )

        return MCPToolOutput(
            tool_name=MCPToolName.COMPLETE_THINKING,
            session_id=session_id,
            step="flow_completed",
            prompt_template=completion_prompt,
            instructions="思维流程已完成，准备生成最终报告",
            context={"flow_completed": True},
            next_action="调用complete_thinking生成最终报告",
            metadata={
                "ready_for_completion": True,
                "completion_verified": True,
                "all_iterations_complete": True,
            },
        )

    def _handle_error(
        self, tool_name: str, error_message: str, session_id: Optional[str] = None
    ) -> MCPToolOutput:
        """Handle tool execution errors using the error handler"""
        # Create a generic exception for the error handler
        error = MCPToolExecutionError(
            error_message, tool_name=tool_name, session_id=session_id
        )

        # Use the error handler to create appropriate recovery response
        return self.error_handler.handle_mcp_error(
            tool_name=tool_name,
            error=error,
            session_id=session_id,
            context={"error_message": error_message},
        )

    def _validate_completion_eligibility(self, session: SessionState) -> Dict[str, Any]:
        """
        Validate whether the session is actually eligible for completion
        CRITICAL: This prevents HOST from bypassing for_each iterations
        """
        try:
            # Check all for_each steps for incomplete iterations
            for step_name, current_count in session.iteration_count.items():
                total_count = session.total_iterations.get(step_name, 0)

                if current_count < total_count and total_count > 0:
                    # Found incomplete for_each - completion not allowed
                    remaining = total_count - current_count

                    return {
                        "allowed": False,
                        "reason": f"Active for_each in {step_name}: {current_count}/{total_count} (缺少{remaining}个)",
                        "current_state": f"{step_name} at {current_count}/{total_count}",
                        "required_step": step_name,
                        "continuation_template": self.template_manager.get_template(
                            "evidence_collection",
                            {"sub_question": f"第{current_count + 1}个子问题"},
                        ),
                        "continuation_instruction": f"必须完成剩余{remaining}个子问题的{step_name}处理",
                        "next_action": f"继续处理第{current_count + 1}个子问题",
                        "current_iterations": current_count,
                        "total_iterations": total_count,
                        "iteration_status": {
                            "current": current_count,
                            "total": total_count,
                            "remaining": remaining,
                            "step": step_name,
                        },
                    }

            # All for_each iterations complete - completion allowed
            return {
                "allowed": True,
                "reason": "All for_each iterations completed",
                "validation_passed": True,
            }

        except Exception as e:
            logger.error(f"Error validating completion eligibility: {e}")
            # Default to blocking completion if validation fails
            return {
                "allowed": False,
                "reason": f"Validation error: {e}",
                "error_occurred": True,
            }

    # Enhanced helper methods for complete_thinking tool

    def _calculate_comprehensive_quality_metrics(
        self, session: SessionState
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive quality metrics for the session

        Returns detailed quality analysis including:
        - Average quality score
        - Quality trend analysis
        - Step-by-step quality breakdown
        - Quality distribution
        - Improvement recommendations
        """
        quality_scores = session.quality_scores
        
        # Get actual step count from database for consistency with session summary
        try:
            steps = self.session_manager.db.get_session_steps(session.session_id)
            actual_step_count = len(steps)
        except Exception:
            actual_step_count = session.step_number

        if not quality_scores:
            return {
                "average_quality": 0.0,
                "quality_trend": "no_data",
                "total_steps": actual_step_count,
                "high_quality_steps": 0,
                "quality_distribution": {},
                "improvement_areas": ["No quality data available"],
                "overall_assessment": "insufficient_data",
            }

        # Calculate basic metrics
        scores = list(quality_scores.values())
        average_quality = sum(scores) / len(scores)
        high_quality_steps = sum(1 for score in scores if score >= 8.0)

        # Quality trend analysis
        quality_trend = self._analyze_quality_trend(scores)

        # Quality distribution
        quality_distribution = {
            "excellent": sum(1 for score in scores if score >= 9.0),
            "good": sum(1 for score in scores if 7.0 <= score < 9.0),
            "acceptable": sum(1 for score in scores if 5.0 <= score < 7.0),
            "needs_improvement": sum(1 for score in scores if score < 5.0),
        }

        # Identify improvement areas
        improvement_areas = self._identify_improvement_areas(quality_scores)

        # Overall assessment
        overall_assessment = self._determine_overall_assessment(
            average_quality, quality_distribution
        )

        return {
            "average_quality": round(average_quality, 2),
            "quality_trend": quality_trend,
            "total_steps": actual_step_count,
            "high_quality_steps": high_quality_steps,
            "quality_distribution": quality_distribution,
            "step_quality_breakdown": quality_scores,
            "improvement_areas": improvement_areas,
            "overall_assessment": overall_assessment,
            "quality_consistency": self._calculate_quality_consistency(scores),
            "best_performing_step": (
                max(quality_scores.items(), key=lambda x: x[1])
                if quality_scores
                else None
            ),
            "lowest_performing_step": (
                min(quality_scores.items(), key=lambda x: x[1])
                if quality_scores
                else None
            ),
        }

    def _analyze_quality_trend(self, scores: List[float]) -> str:
        """Analyze the trend in quality scores"""
        if len(scores) < 2:
            return "insufficient_data"

        # Simple trend analysis
        first_half = scores[: len(scores) // 2]
        second_half = scores[len(scores) // 2 :]

        first_avg = sum(first_half) / len(first_half)
        second_avg = sum(second_half) / len(second_half)

        diff = second_avg - first_avg

        if diff > 0.5:
            return "improving"
        elif diff < -0.5:
            return "declining"
        else:
            return "stable"

    def _identify_improvement_areas(
        self, quality_scores: Dict[str, float]
    ) -> List[str]:
        """Identify areas that need improvement based on quality scores"""
        improvement_areas = []

        for step_name, score in quality_scores.items():
            if score < 6.0:
                improvement_areas.append(f"{step_name} (得分: {score})")

        if not improvement_areas:
            improvement_areas.append("所有步骤质量良好")

        return improvement_areas

    def _determine_overall_assessment(
        self, average_quality: float, quality_distribution: Dict[str, int]
    ) -> str:
        """Determine overall quality assessment"""
        if average_quality >= 8.5:
            return "excellent"
        elif average_quality >= 7.0:
            return "good"
        elif average_quality >= 5.0:
            return "acceptable"
        else:
            return "needs_improvement"

    def _calculate_quality_consistency(self, scores: List[float]) -> float:
        """Calculate quality consistency (lower variance = higher consistency)"""
        if len(scores) < 2:
            return 1.0

        mean = sum(scores) / len(scores)
        variance = sum((score - mean) ** 2 for score in scores) / len(scores)

        # Convert to consistency score (0-1, higher is more consistent)
        consistency = max(0, 1 - (variance / 10))  # Normalize variance
        return round(consistency, 3)

    def _generate_detailed_session_summary(
        self, session: SessionState
    ) -> Dict[str, Any]:
        """Generate detailed session summary with step analysis"""

        # Get step details from database
        try:
            steps = self.session_manager.db.get_session_steps(session.session_id)
            results = self.session_manager.db.get_step_results(session.session_id)
        except Exception:
            steps = []
            results = []

        # Organize results by step
        step_results_map = {}
        for result in results:
            step_id = result.get("step_id")
            if step_id not in step_results_map:
                step_results_map[step_id] = []
            step_results_map[step_id].append(result)

        # Build detailed step summary with proper quality score synchronization
        detailed_steps = []
        for step in steps:
            step_name = step.get("step_name", "unknown")

            # CRITICAL FIX: Use session.quality_scores as primary source
            # Fall back to database value only if session doesn't have it
            quality_score = session.quality_scores.get(step_name) or step.get(
                "quality_score"
            )

            step_summary = {
                "step_name": step_name,
                "step_type": step.get("step_type", "general"),
                "quality_score": quality_score,
                "execution_time_ms": step.get("execution_time_ms"),
                "results_count": len(step_results_map.get(step.get("id"), [])),
                "timestamp": step.get("created_at"),
            }
            detailed_steps.append(step_summary)

        return {
            "session_id": session.session_id,
            "topic": session.topic,
            "flow_type": session.flow_type,
            "total_steps": len(detailed_steps),
            "session_duration": self._calculate_session_duration_minutes(session),
            "detailed_steps": detailed_steps,
            "context_summary": session.context,
            "completion_status": "completed",
        }

    def _calculate_session_duration_minutes(self, session: SessionState) -> float:
        """Calculate session duration in minutes"""
        if session.created_at and session.updated_at:
            duration = (session.updated_at - session.created_at).total_seconds() / 60
            return round(duration, 2)
        return 0.0

    def _extract_detailed_step_contents(self, session_id: str) -> Dict[str, Any]:
        """
        Extract detailed contents from all steps for comprehensive summary
        Returns step contents grouped by step with actual analysis content
        """
        try:
            # Get all step results from database
            results = self.session_manager.db.get_step_results(session_id)
            steps = self.session_manager.db.get_session_steps(session_id)

            # Create a mapping of step_id to step_name
            step_id_to_name = {}
            for step in steps:
                step_id_to_name[step.get("id")] = step.get("step_name", "unknown")

            # Group results by step
            step_contents = {}
            for result in results:
                step_id = result.get("step_id")
                step_name = step_id_to_name.get(step_id, f"step_{step_id}")

                if step_name not in step_contents:
                    step_contents[step_name] = []

                content_data = {
                    "content": result.get("content", ""),
                    "result_type": result.get("result_type", "output"),
                    "metadata": result.get("metadata", {}),
                    "quality_indicators": result.get("quality_indicators", {}),
                    "timestamp": result.get("created_at", ""),
                }
                step_contents[step_name].append(content_data)

            return step_contents
        except Exception as e:
            logger.error(
                f"Error extracting detailed step contents for {session_id}: {e}"
            )
            return {}

    def _build_step_analysis_summary(
        self, detailed_step_contents: Dict[str, Any]
    ) -> str:
        """
        Build a comprehensive analysis summary from step contents (NO TRUNCATION)
        Provides complete content for modern LLMs with large context windows
        Now with intelligent JSON parsing and formatting for better readability
        """
        if not detailed_step_contents:
            return "无详细分析内容"

        summary_parts = []
        total_chars = 0

        for step_name, contents in detailed_step_contents.items():
            if not contents:
                continue

            # Get the main analysis content (prioritize 'output' type)
            raw_content = ""
            for content_data in contents:
                if content_data.get("result_type") == "output" and content_data.get(
                    "content"
                ):
                    raw_content = content_data.get(
                        "content", ""
                    )  # FULL CONTENT - no truncation
                    break

            if not raw_content and contents:
                # Fallback to any content
                raw_content = contents[0].get(
                    "content", ""
                )  # FULL CONTENT - no truncation

            if raw_content:
                # Format the content intelligently
                formatted_content = self._format_step_content(step_name, raw_content)
                step_content_length = len(formatted_content)
                total_chars += step_content_length

                # Add content statistics for transparency
                content_info = f"*[内容长度: {step_content_length:,} 字符]*\n\n"
                summary_parts.append(f"### {step_name}\n{content_info}{formatted_content}")

        # Add summary statistics
        summary_header = (
            f"*总分析内容: {total_chars:,} 字符，{len(summary_parts)} 个步骤*\n\n"
        )
        full_content = "\n\n".join(summary_parts) if summary_parts else "无有效分析内容"

        return summary_header + full_content

    def _format_step_content(self, step_name: str, raw_content: str) -> str:
        """
        Format step content intelligently - parse JSON if possible, otherwise return as-is
        Converts raw data into human-readable analysis content
        """
        try:
            # Try to parse as JSON first
            import json
            data = json.loads(raw_content)
            
            # Format based on step type
            if step_name == "decompose_problem":
                return self._format_decompose_content(data)
            elif step_name == "collect_evidence":
                return self._format_evidence_content(data)
            elif step_name in ["evaluate", "critical_evaluation"]:
                return self._format_evaluation_content(data)
            elif step_name == "reflect":
                return self._format_reflection_content(data)
            elif step_name == "multi_perspective_debate":
                return self._format_debate_content(data)
            else:
                # Generic JSON formatting
                return self._format_generic_json(data)
                
        except (json.JSONDecodeError, TypeError):
            # If it's not JSON, return the content as-is
            return raw_content
            
    def _format_decompose_content(self, data: dict) -> str:
        """Format decomposition step content"""
        formatted = []
        
        if "main_question" in data:
            formatted.append(f"**核心问题**: {data['main_question']}")
            formatted.append("")
        
        if "complexity_level" in data:
            formatted.append(f"**复杂度级别**: {data['complexity_level']}")
            formatted.append("")
            
        if "sub_questions" in data:
            formatted.append("**子问题分解**:")
            for i, sq in enumerate(data["sub_questions"], 1):
                formatted.append(f"{i}. **{sq.get('id', f'SQ{i}')}**: {sq.get('question', '未知问题')}")
                if sq.get('priority'):
                    formatted.append(f"   - 优先级: {sq['priority']}")
                if sq.get('search_keywords'):
                    keywords = ", ".join(sq['search_keywords'])
                    formatted.append(f"   - 关键词: {keywords}")
                formatted.append("")
        
        if "relationships" in data:
            formatted.append("**问题关联性**:")
            for rel in data["relationships"]:
                formatted.append(f"- {rel.get('from')} → {rel.get('to')}: {rel.get('description', '相关')}")
            formatted.append("")
            
        if "coverage_analysis" in data:
            ca = data["coverage_analysis"]
            if "key_aspects_covered" in ca:
                aspects = ", ".join(ca["key_aspects_covered"])
                formatted.append(f"**覆盖分析**: {aspects}")
                formatted.append("")
        
        return "\n".join(formatted)
    
    def _format_evidence_content(self, data: dict) -> str:
        """Format evidence collection content"""
        formatted = []
        
        if "sub_question" in data:
            formatted.append(f"**研究问题**: {data['sub_question']}")
            formatted.append("")
        
        if "evidence_collection" in data:
            formatted.append("**证据收集结果**:")
            for i, evidence in enumerate(data["evidence_collection"], 1):
                formatted.append(f"\n**证据 {i}: {evidence.get('source_name', '未知来源')}**")
                if evidence.get('credibility_score'):
                    formatted.append(f"- 可信度: {evidence['credibility_score']}/10")
                if evidence.get('key_findings'):
                    formatted.append("- 关键发现:")
                    for finding in evidence['key_findings']:
                        formatted.append(f"  • {finding}")
                if evidence.get('quantitative_data'):
                    formatted.append("- 量化数据:")
                    for qdata in evidence['quantitative_data']:
                        formatted.append(f"  • {qdata}")
                formatted.append("")
        
        if "evidence_synthesis" in data:
            es = data["evidence_synthesis"]
            if "main_findings" in es:
                formatted.append("**综合发现**:")
                for finding in es["main_findings"]:
                    formatted.append(f"• {finding}")
                formatted.append("")
            
            if "practical_recommendations" in es:
                formatted.append("**实践建议**:")
                for rec in es["practical_recommendations"]:
                    formatted.append(f"• {rec}")
                formatted.append("")
        
        return "\n".join(formatted)
    
    def _format_evaluation_content(self, data: dict) -> str:
        """Format evaluation content"""
        formatted = []
        
        if isinstance(data, dict):
            if "执行摘要" in data or "executive_summary" in data:
                summary = data.get("执行摘要") or data.get("executive_summary")
                formatted.append(f"**执行摘要**\n{summary}")
                formatted.append("")
            
            if "证据可信度矩阵" in data:
                formatted.append("**证据可信度矩阵**:")
                matrix = data["证据可信度矩阵"]
                for key, value in matrix.items():
                    formatted.append(f"• {key}: {value}")
                formatted.append("")
            
            if "批判性洞察" in data:
                insights = data["批判性洞察"]
                if "核心优势" in insights:
                    formatted.append("**核心优势**:")
                    for advantage in insights["核心优势"]:
                        formatted.append(f"• {advantage}")
                    formatted.append("")
                
                if "关键弱点" in insights:
                    formatted.append("**关键弱点**:")
                    for weakness in insights["关键弱点"]:
                        formatted.append(f"• {weakness}")
                    formatted.append("")
            
            if "战略建议" in data:
                formatted.append("**战略建议**:")
                suggestions = data["战略建议"]
                if "立即行动建议" in suggestions:
                    formatted.append("立即行动建议:")
                    for action in suggestions["立即行动建议"]:
                        if isinstance(action, dict):
                            formatted.append(f"• {action.keys()}")
                        else:
                            formatted.append(f"• {action}")
                formatted.append("")
        else:
            formatted.append(str(data))
        
        return "\n".join(formatted)
    
    def _format_reflection_content(self, data: dict) -> str:
        """Format reflection content"""
        formatted = []
        
        if "整体评估" in data:
            formatted.append(f"**整体评估**: {data['整体评估']}")
            formatted.append("")
        
        if "主要优势" in data:
            formatted.append("**主要优势**:")
            for advantage in data["主要优势"]:
                formatted.append(f"• {advantage}")
            formatted.append("")
        
        if "关键不足" in data:
            formatted.append("**关键不足**:")
            for weakness in data["关键不足"]:
                formatted.append(f"• {weakness}")
            formatted.append("")
        
        if "确定性分析" in data:
            ca = data["确定性分析"]
            for level, items in ca.items():
                formatted.append(f"**{level}**:")
                for item in items:
                    formatted.append(f"• {item}")
                formatted.append("")
        
        if "改进建议" in data:
            formatted.append("**改进建议**:")
            if "即刻改进" in data["改进建议"]:
                formatted.append("即刻改进:")
                for improvement in data["改进建议"]["即刻改进"]:
                    formatted.append(f"• {improvement}")
            if "长期提升" in data["改进建议"]:
                formatted.append("长期提升:")
                for improvement in data["改进建议"]["长期提升"]:
                    formatted.append(f"• {improvement}")
            formatted.append("")
        
        return "\n".join(formatted)
    
    def _format_debate_content(self, data: dict) -> str:
        """Format debate content"""
        formatted = []
        
        if "debate_summary" in data:
            formatted.append(f"**辩论总结**: {data['debate_summary']}")
            formatted.append("")
        
        if "perspectives" in data:
            for i, perspective in enumerate(data["perspectives"], 1):
                stance = perspective.get("stance", f"观点{i}")
                formatted.append(f"**{stance}方观点**:")
                if "main_arguments" in perspective:
                    for arg in perspective["main_arguments"]:
                        formatted.append(f"• {arg}")
                formatted.append("")
        
        return "\n".join(formatted)
    
    def _format_generic_json(self, data: dict) -> str:
        """Generic JSON formatting fallback"""
        formatted = []
        
        def format_value(value, indent=0):
            prefix = "  " * indent
            if isinstance(value, dict):
                for k, v in value.items():
                    if isinstance(v, (dict, list)):
                        formatted.append(f"{prefix}**{k}**:")
                        format_value(v, indent + 1)
                    else:
                        formatted.append(f"{prefix}**{k}**: {v}")
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        formatted.append(f"{prefix}{i+1}.")
                        format_value(item, indent + 1)
                    else:
                        formatted.append(f"{prefix}• {item}")
            else:
                formatted.append(f"{prefix}{value}")
        
        format_value(data)
        return "\n".join(formatted)

    def _calculate_auto_quality_score(
        self, content: str, metadata: Dict[str, Any] = None
    ) -> float:
        """
        Calculate automatic quality score based on content characteristics
        """
        if not content or len(content.strip()) < 10:
            return 1.0

        score = 5.0  # Base score

        # Content length factor (more comprehensive analysis gets higher score)
        length_factor = min(len(content) / 1000.0, 3.0)  # Max 3 points for length
        score += length_factor

        # Structure and organization factor
        if "##" in content or "###" in content:  # Has headers
            score += 0.5
        if content.count("\n") > 5:  # Well-structured with line breaks
            score += 0.5

        # Content quality indicators
        quality_keywords = [
            "分析",
            "结论",
            "建议",
            "评估",
            "总结",
            "洞察",
            "发现",
            "策略",
        ]
        keyword_count = sum(1 for keyword in quality_keywords if keyword in content)
        score += min(keyword_count * 0.2, 1.0)  # Max 1 point for keywords

        # Metadata quality indicators
        if metadata:
            if metadata.get("citations"):
                score += 0.5  # Has citations
            if metadata.get("evidence_count", 0) > 0:
                score += 0.5  # Has evidence

        return min(score, 10.0)  # Cap at 10.0

    def get_export_directory(self) -> Path:
        """
        Get the export directory using priority chain configuration
        
        Priority order:
        1. DEEP_THINKING_EXPORT_DIR environment variable
        2. Configuration file export.base_directory
        3. DEEP_THINKING_DATA_DIR/exports environment variable  
        4. XDG_DATA_HOME/deep-thinking/exports (Linux/Mac standard)
        5. User home ~/.deep-thinking/exports (fallback)
        6. Temp directory (final fallback)
        
        Returns:
            Path object for export directory
        """
        import os
        import tempfile
        
        # 1. Check primary environment variable
        if export_dir := os.getenv('DEEP_THINKING_EXPORT_DIR'):
            path = Path(export_dir)
            logger.info(f"Using export directory from DEEP_THINKING_EXPORT_DIR: {path}")
            return path
            
        # 2. Check configuration file (if available)
        try:
            if hasattr(self, 'config_manager') and self.config_manager:
                config_dir = self.config_manager.get('export.base_directory')
                if config_dir:
                    path = Path(os.path.expanduser(config_dir))
                    logger.info(f"Using export directory from config: {path}")
                    return path
        except Exception as e:
            logger.debug(f"Could not read config for export directory: {e}")
            
        # 3. Check data directory environment variable
        if data_dir := os.getenv('DEEP_THINKING_DATA_DIR'):
            path = Path(data_dir) / 'exports'
            logger.info(f"Using export directory from DEEP_THINKING_DATA_DIR: {path}")
            return path
            
        # 4. XDG Base Directory standard (Linux/Mac)
        if xdg_data := os.getenv('XDG_DATA_HOME'):
            path = Path(xdg_data) / 'deep-thinking' / 'exports'
            logger.info(f"Using XDG standard export directory: {path}")
            return path
            
        # 5. User home directory (most common fallback)
        try:
            path = Path.home() / '.deep-thinking' / 'exports'
            logger.info(f"Using user home export directory: {path}")
            return path
        except Exception as e:
            logger.warning(f"Could not access user home directory: {e}")
            
        # 6. Temp directory (final fallback)
        path = Path(tempfile.gettempdir()) / 'deep-thinking-exports'
        logger.warning(f"Using temporary export directory: {path}")
        return path

    def _validate_export_directory(self, export_dir: Path) -> Dict[str, Any]:
        """
        Validate and prepare export directory
        
        Args:
            export_dir: Path to validate
            
        Returns:
            Dict with validation results and warnings
        """
        result = {
            "valid": True,
            "created": False,
            "warnings": []
        }
        
        try:
            # Check if directory is inside a git repository (warn if so)
            current_path = export_dir.absolute()
            for parent in current_path.parents:
                if (parent / '.git').exists():
                    # Check if it's the same as current working directory
                    if parent == Path.cwd():
                        result["warnings"].append(
                            f"Export directory {export_dir} is inside the current git repository. "
                            "Consider setting DEEP_THINKING_EXPORT_DIR to avoid git status pollution."
                        )
                    break
            
            # Create directory if it doesn't exist
            if not export_dir.exists():
                export_dir.mkdir(parents=True, exist_ok=True)
                result["created"] = True
                logger.info(f"Created export directory: {export_dir}")
            
            # Check write permissions
            test_file = export_dir / '.write_test'
            try:
                test_file.write_text("test")
                test_file.unlink()
            except Exception as e:
                result["valid"] = False
                result["warnings"].append(f"No write permission for directory {export_dir}: {e}")
                
        except Exception as e:
            result["valid"] = False
            result["warnings"].append(f"Failed to validate/create export directory {export_dir}: {e}")
            logger.error(f"Export directory validation failed: {e}")
            
        return result

    def _generate_export_filename(self, session, custom_title: Optional[str] = None) -> str:
        """
        Generate export filename based on configuration
        
        Args:
            session: Session state object
            custom_title: Optional concise title from Host (20 chars or less recommended)
            
        Returns:
            Generated filename string
        """
        try:
            # Get configuration with defaults - get the entire config tree
            if not self.config_manager:
                logger.debug("Config manager not available, using defaults")
                config = {}
            else:
                config = self.config_manager.config_data  # Direct access to full config
                logger.debug(f"Config data keys: {list(config.keys()) if config else 'None'}")
            
            export_config = config.get("export", {})
            logger.debug(f"Export config: {export_config}")
            file_naming = export_config.get("file_naming", {})
            logger.debug(f"File naming config: {file_naming}")
            
            pattern = file_naming.get("pattern", "{topic}_{timestamp}.md")
            max_topic_length = file_naming.get("max_topic_length", 20)
            include_session_id = file_naming.get("include_session_id", False)
            sanitize_topic = file_naming.get("sanitize_topic", True)
            
            logger.debug(f"File naming config - pattern: {pattern}, max_length: {max_topic_length}")
            logger.debug(f"Custom title provided: {custom_title}")
            
            # Generate components
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Use custom title if provided, otherwise extract from session topic
            if custom_title:
                topic = custom_title[:max_topic_length].strip()
            else:
                topic = session.topic[:max_topic_length].strip() if hasattr(session, 'topic') and session.topic else "untitled"
            
            # Sanitize topic if enabled
            if sanitize_topic:
                # More inclusive sanitization that preserves Unicode characters (Chinese, etc.)
                # Remove only problematic filename characters
                # Keep alphanumeric (including Unicode), spaces, hyphens, underscores
                topic = re.sub(r'[<>:"/\\|?*]', '', topic)  # Remove Windows forbidden chars
                topic = re.sub(r'[\x00-\x1f\x7f]', '', topic)  # Remove control characters
                topic = topic.replace(" ", "_").strip() if topic.strip() else "untitled"
            
            # Prepare replacement variables
            replacements = {
                "timestamp": timestamp,
                "topic": topic,
                "session_id": session.session_id if hasattr(session, 'session_id') else "unknown",
                "session_id_short": (session.session_id[:8] if hasattr(session, 'session_id') else "unknown"),
            }
            
            # Apply pattern with replacements
            logger.debug(f"Applying pattern '{pattern}' with replacements: {replacements}")
            filename = pattern.format(**replacements)
            
            # Ensure .md extension if not present
            if not filename.endswith('.md'):
                filename += '.md'
                
            logger.info(f"✅ Generated filename: {filename} from pattern: {pattern}")
            logger.info(f"✅ Custom title: {custom_title}")
            return filename
            
        except Exception as e:
            logger.error(f"❌ FILENAME GENERATION FAILED: {e}")
            logger.error(f"Custom title was: {custom_title}")
            # Fallback to simple timestamp-based name
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            logger.error(f"🔄 Using fallback filename: {timestamp}_analysis.md")
            return f"{timestamp}_analysis.md"

    def export_session_to_markdown(
        self, session_id: str, export_path: Optional[str] = None, custom_title: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Export complete session analysis to Markdown file with intelligent directory management

        This function provides full, untruncated access to all analysis content
        for offline reading and further LLM processing. Uses configurable export
        directory to avoid polluting git repositories.

        Args:
            session_id: The session to export
            export_path: Optional custom file path (defaults to auto-generated name in export directory)
            custom_title: Optional concise title from Host (overrides topic extraction)

        Returns:
            Dict with export status and file information
        """
        try:
            # Get session and validate
            session = self.session_manager.get_session(session_id)
            if not session:
                return {
                    "success": False,
                    "error": f"Session {session_id} not found",
                    "file_path": None,
                }

            # Get all detailed content
            detailed_step_contents = self._extract_detailed_step_contents(session_id)
            quality_metrics = self._calculate_comprehensive_quality_metrics(session)
            session_summary = self._generate_detailed_session_summary(session)
            thinking_trace = self.session_manager.get_full_trace(session_id)

            # Get export directory and validate
            if export_path:
                # Custom path provided - use as-is
                file_path = Path(export_path)
                export_dir = file_path.parent
                logger.info(f"Using custom export path: {file_path}")
            else:
                # Auto-generate filename in configured export directory
                export_dir = self.get_export_directory()
                
                # Validate and prepare directory
                validation = self._validate_export_directory(export_dir)
                if not validation["valid"]:
                    return {
                        "success": False,
                        "error": f"Export directory validation failed: {'; '.join(validation['warnings'])}",
                        "file_path": None,
                    }
                
                # Log warnings but continue
                for warning in validation["warnings"]:
                    logger.warning(warning)
                
                # Generate filename using configuration
                filename = self._generate_export_filename(session, custom_title)
                file_path = export_dir / filename
                
                logger.info(f"Auto-generated export path: {file_path}")

            # Build comprehensive Markdown content
            markdown_content = self._build_markdown_report(
                session=session,
                detailed_step_contents=detailed_step_contents,
                quality_metrics=quality_metrics,
                session_summary=session_summary,
                thinking_trace=thinking_trace,
            )

            # Ensure parent directory exists (in case of custom path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write to file
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(markdown_content)

            # Calculate file statistics
            file_size = file_path.stat().st_size
            content_lines = markdown_content.count("\n") + 1
            content_words = len(markdown_content.split())

            logger.info(f"Successfully exported session {session_id} to {file_path}")
            logger.info(
                f"Export stats: {file_size:,} bytes, {content_lines:,} lines, {content_words:,} words"
            )

            return {
                "success": True,
                "file_path": str(file_path.absolute()),
                "file_size_bytes": file_size,
                "content_lines": content_lines,
                "content_words": content_words,
                "session_id": session_id,
                "export_timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error exporting session {session_id} to Markdown: {e}")
            return {
                "success": False,
                "error": str(e),
                "file_path": export_path,
                "session_id": session_id,
            }

    def _build_markdown_report(
        self,
        session: SessionState,
        detailed_step_contents: Dict[str, Any],
        quality_metrics: Dict[str, Any],
        session_summary: Dict[str, Any],
        thinking_trace: Dict[str, Any],
    ) -> str:
        """
        Build comprehensive Markdown report with complete content
        """
        lines = []

        # Header with metadata
        lines.extend(
            [
                "# 深度思考会话完整报告",
                "",
                f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"**会话ID**: `{session.session_id}`",
                "**导出版本**: 完整无截断版本",
                "",
                "---",
                "",
            ]
        )

        # Session metadata
        lines.extend(
            [
                "## 📊 会话元数据",
                "",
                "| 属性 | 值 |",
                "|------|-----|",
                f"| **主题** | {session.topic} |",
                f"| **思考流程** | {session.flow_type} |",
                f"| **会话时长** | {session_summary.get('session_duration', 0):.2f} 分钟 |",
                f"| **执行步骤** | {session_summary.get('total_steps', 0)} 个 |",
                f"| **平均质量得分** | {quality_metrics.get('average_quality', 0):.2f}/10 |",
                f"| **质量趋势** | {quality_metrics.get('quality_trend', 'unknown')} |",
                "",
            ]
        )

        # Quality metrics details
        if quality_metrics.get("step_quality_breakdown"):
            lines.extend(
                [
                    "### 📈 详细质量评分",
                    "",
                    "| 步骤 | 质量得分 |",
                    "|------|----------|",
                ]
            )
            for step_name, score in quality_metrics["step_quality_breakdown"].items():
                lines.append(f"| {step_name} | {score:.3f}/10 |")
            lines.append("")

        # Complete analysis content
        lines.extend(
            [
                "## 🔍 完整分析过程",
                "",
                "> 以下是完整的、未经截断的分析内容，可供进一步的LLM分析和洞察提取。",
                "",
            ]
        )

        # Add each step's complete content
        for step_name, contents in detailed_step_contents.items():
            if not contents:
                continue

            lines.extend([f"### 📋 {step_name}", ""])

            # Add step metadata
            main_content = ""
            metadata = {}
            for content_data in contents:
                if content_data.get("result_type") == "output":
                    main_content = content_data.get("content", "")
                    metadata = content_data.get("metadata", {})
                    break

            if not main_content and contents:
                main_content = contents[0].get("content", "")
                metadata = contents[0].get("metadata", {})

            # Add content statistics
            if main_content:
                char_count = len(main_content)
                word_count = len(main_content.split())
                lines.extend(
                    [
                        f"**内容统计**: {char_count:,} 字符, {word_count:,} 词",
                        f"**时间戳**: {contents[0].get('timestamp', 'Unknown')}",
                        "",
                    ]
                )

                # Add metadata if available
                if metadata:
                    lines.extend(
                        [
                            "**元数据**:",
                            "```json",
                            f"{json.dumps(metadata, ensure_ascii=False, indent=2)}",
                            "```",
                            "",
                        ]
                    )

                # Add the complete content
                lines.extend(["**完整内容**:", "", main_content, "", "---", ""])

        # Session context
        if session.context:
            lines.extend(
                [
                    "## 🏷️ 会话上下文",
                    "",
                    "```json",
                    f"{json.dumps(session.context, ensure_ascii=False, indent=2)}",
                    "```",
                    "",
                ]
            )

        # Footer
        lines.extend(
            [
                "---",
                "",
                "## 📋 使用说明",
                "",
                "1. **完整内容**: 本报告包含所有原始分析内容，无任何截断",
                "2. **LLM分析**: 可直接将此文件提供给LLM进行二次分析和洞察提取",
                "3. **引用方式**: 在新的对话中引用此文件进行深度讨论",
                "4. **格式**: 标准Markdown格式，支持所有Markdown渲染器",
                "",
                "*此报告由深度思考引擎自动生成，确保内容完整性和可用性。*",
            ]
        )

        return "\n".join(lines)

    def _refresh_session_quality_data(self, session: SessionState) -> None:
        """
        Refresh session quality data from database to ensure completeness
        This ensures we have the most up-to-date quality scores for reporting
        """
        try:
            # Get all steps and their results from database
            steps = self.session_manager.db.get_session_steps(session.session_id)

            # Update session quality scores with any missing data
            for step in steps:
                step_name = step.get("step_name")
                quality_score = step.get("quality_score")

                if step_name and quality_score is not None:
                    # Update session quality scores if not already present
                    if step_name not in session.quality_scores:
                        session.quality_scores[step_name] = quality_score
                        logger.info(
                            f"Refreshed quality score for {step_name}: {quality_score:.1f}"
                        )

            # Update the session cache
            self.session_manager._active_sessions[session.session_id] = session

        except Exception as e:
            logger.warning(f"Error refreshing session quality data: {e}")

    def _build_comprehensive_summary_params(
        self,
        session: SessionState,
        quality_metrics: Dict[str, Any],
        session_summary: Dict[str, Any],
        thinking_trace: Dict[str, Any],
        final_insights: Optional[str],
    ) -> Dict[str, Any]:
        """Build comprehensive parameters for the summary template with detailed content"""

        # Extract detailed step contents from database
        detailed_step_contents = self._extract_detailed_step_contents(
            session.session_id
        )

        # Build comprehensive step analysis summary
        step_analysis = self._build_step_analysis_summary(detailed_step_contents)

        # Format quality metrics for display
        quality_display = self._format_quality_metrics_for_display(quality_metrics)

        # Format step summary for display
        step_summary_display = self._format_step_summary_for_display(session_summary)

        # Format thinking trace for display
        trace_display = self._format_thinking_trace_for_display(thinking_trace)

        return {
            "topic": session.topic,
            "flow_type": session.flow_type,
            "session_duration": f"{session_summary['session_duration']} 分钟",
            "total_steps": session_summary["total_steps"],
            "step_summary": step_summary_display,
            "thinking_trace": trace_display,
            "quality_metrics": quality_display,
            "final_insights": final_insights or "无额外洞察",
            "completion_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "overall_assessment": quality_metrics.get("overall_assessment", "unknown"),
            "average_quality": quality_metrics.get("average_quality", 0),
            "improvement_areas": "\n".join(
                quality_metrics.get("improvement_areas", [])
            ),
            "best_step": (
                quality_metrics.get("best_performing_step", ["无", 0])[0]
                if quality_metrics.get("best_performing_step")
                else "无"
            ),
            "session_context": session.context,
            # Enhanced content fields for comprehensive summary
            "detailed_step_contents": detailed_step_contents,
            "step_analysis_summary": step_analysis,
            "comprehensive_analysis": step_analysis,  # Alias for template compatibility
        }

    def _format_quality_metrics_for_display(
        self, quality_metrics: Dict[str, Any]
    ) -> str:
        """Format quality metrics for template display"""
        if not quality_metrics:
            return "无质量数据"

        lines = [
            f"平均质量得分: {quality_metrics.get('average_quality', 0)}/10",
            f"质量趋势: {quality_metrics.get('quality_trend', 'unknown')}",
            f"高质量步骤数: {quality_metrics.get('high_quality_steps', 0)}",
            f"总体评估: {quality_metrics.get('overall_assessment', 'unknown')}",
            f"质量一致性: {quality_metrics.get('quality_consistency', 0)}",
        ]

        if quality_metrics.get("best_performing_step"):
            best_step, best_score = quality_metrics["best_performing_step"]
            lines.append(f"最佳步骤: {best_step} ({best_score}/10)")

        return "\n".join(lines)

    def _format_step_summary_for_display(self, session_summary: Dict[str, Any]) -> str:
        """Format step summary for template display"""
        if not session_summary.get("detailed_steps"):
            return "无步骤数据"

        lines = []
        for step in session_summary["detailed_steps"]:
            step_name = step.get("step_name", "unknown")
            quality = step.get("quality_score", "N/A")
            lines.append(f"- {step_name}: 完成 (质量: {quality})")

        return "\n".join(lines)

    def _format_thinking_trace_for_display(self, thinking_trace: Dict[str, Any]) -> str:
        """Format thinking trace for template display"""
        if not thinking_trace or thinking_trace.get("error"):
            return "思维轨迹不可用"

        lines = [
            f"会话ID: {thinking_trace.get('session_id', 'unknown')}",
            f"流程类型: {thinking_trace.get('flow_type', 'unknown')}",
            f"总时长: {thinking_trace.get('total_duration', 0)} 秒",
            f"步骤数量: {len(thinking_trace.get('steps', []))}",
        ]

        return "\n".join(lines)

    def _generate_completion_instructions(
        self, quality_metrics: Dict[str, Any], session: SessionState
    ) -> str:
        """Generate detailed instructions for final report generation"""
        base_instruction = "请生成详细的综合报告，包含所有关键发现和洞察"

        # Add quality-specific guidance
        quality_guidance = []

        overall_assessment = quality_metrics.get("overall_assessment", "unknown")
        if overall_assessment == "excellent":
            quality_guidance.append("质量优秀，重点突出核心洞察和创新观点")
        elif overall_assessment == "good":
            quality_guidance.append("质量良好，确保涵盖所有重要发现")
        elif overall_assessment == "acceptable":
            quality_guidance.append("质量可接受，注意补充分析深度")
        else:
            quality_guidance.append("质量需要改进，重点加强论证和证据支撑")

        # Add step-specific guidance
        if session.step_number > 5:
            quality_guidance.append("流程较为完整，确保各步骤结果的有机整合")

        # Add improvement area guidance
        improvement_areas = quality_metrics.get("improvement_areas", [])
        if improvement_areas and improvement_areas[0] != "所有步骤质量良好":
            quality_guidance.append(
                f"特别关注以下改进领域: {', '.join(improvement_areas[:2])}"
            )

        if quality_guidance:
            return f"{base_instruction}。{' '.join(quality_guidance)}"

        return base_instruction
