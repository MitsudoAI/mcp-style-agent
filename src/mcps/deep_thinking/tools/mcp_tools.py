"""
Core MCP tools for the Deep Thinking Engine

These tools follow the zero-cost principle:
- MCP Server provides flow control and prompt templates
- Host LLM performs the actual intelligent processing
- No LLM API calls from the server side
"""

import uuid
from typing import Dict, Any, Optional
from datetime import datetime

from ..models.mcp_models import (
    MCPToolOutput, MCPToolName,
    StartThinkingInput, NextStepInput, AnalyzeStepInput, CompleteThinkingInput,
    SessionState
)
from ..sessions.session_manager import SessionManager
from ..templates.template_manager import TemplateManager
from ..flows.flow_manager import FlowManager
from ..config.exceptions import DeepThinkingError


class MCPTools:
    """
    Core MCP tools that return prompt templates for LLM execution
    
    Following the zero-cost principle:
    - Server handles flow control and template management
    - LLM handles intelligent processing and content generation
    """
    
    def __init__(self, 
                 session_manager: SessionManager,
                 template_manager: TemplateManager,
                 flow_manager: FlowManager):
        self.session_manager = session_manager
        self.template_manager = template_manager
        self.flow_manager = flow_manager
    
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
                    "original_topic": input_data.topic
                }
            )
            
            # Save session state
            self.session_manager.create_session(session_state)
            
            # Get decomposition prompt template
            template_params = {
                "topic": input_data.topic,
                "complexity": input_data.complexity,
                "focus": input_data.focus,
                "domain_context": input_data.focus or "general analysis"
            }
            
            prompt_template = self.template_manager.get_template(
                "decomposition", 
                template_params
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
                    "complexity": input_data.complexity
                },
                next_action="调用next_step工具继续流程",
                metadata={
                    "flow_type": input_data.flow_type,
                    "expected_output": "JSON格式的问题分解结果"
                }
            )
            
        except Exception as e:
            raise DeepThinkingError(f"Failed to start thinking session: {str(e)}")
    
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
            except Exception:
                # Session not found - return session recovery prompt
                recovery_prompt = self.template_manager.get_template(
                    "session_recovery",
                    {"session_id": input_data.session_id}
                )
                
                return MCPToolOutput(
                    tool_name=MCPToolName.NEXT_STEP,
                    session_id=input_data.session_id,
                    step="session_recovery",
                    prompt_template=recovery_prompt,
                    instructions="会话已丢失，请选择如何继续",
                    context={"error": "session_not_found"},
                    next_action="重新开始或尝试恢复会话",
                    metadata={"error_recovery": True}
                )
            
            # Extract quality score from step result if provided
            quality_score = None
            if input_data.quality_feedback and "quality_score" in input_data.quality_feedback:
                quality_score = input_data.quality_feedback["quality_score"]
            
            # Save previous step result with enhanced context
            self.session_manager.add_step_result(
                input_data.session_id,
                session.current_step,
                input_data.step_result,
                result_type="output",
                metadata={
                    "step_completion_time": datetime.now().isoformat(),
                    "quality_feedback": input_data.quality_feedback,
                    "step_context": session.context
                },
                quality_score=quality_score
            )
            
            # Determine next step based on flow and current state
            next_step_info = self._determine_next_step_with_context(
                session, 
                input_data.step_result,
                input_data.quality_feedback
            )
            
            if not next_step_info:
                # Flow completed
                return self._handle_flow_completion(input_data.session_id)
            
            # Update session state with enhanced tracking
            self.session_manager.update_session_step(
                input_data.session_id,
                next_step_info["step_name"],
                step_result=input_data.step_result,
                quality_score=quality_score
            )
            
            # Build enhanced template parameters with full context
            template_params = self._build_enhanced_template_params(
                session, 
                input_data.step_result,
                next_step_info
            )
            
            # Get appropriate prompt template with smart selection
            prompt_template = self._get_contextual_template(
                next_step_info["template_name"],
                template_params,
                session
            )
            
            # Build comprehensive context for the next step
            step_context = self._build_step_context(session, next_step_info)
            
            return MCPToolOutput(
                tool_name=MCPToolName.NEXT_STEP,
                session_id=input_data.session_id,
                step=next_step_info["step_name"],
                prompt_template=prompt_template,
                instructions=self._generate_step_instructions(next_step_info, session),
                context=step_context,
                next_action=self._determine_next_action(next_step_info, session),
                metadata={
                    "step_number": session.step_number + 1,
                    "flow_progress": f"{session.step_number + 1}/{self.flow_manager.get_total_steps(session.flow_type)}",
                    "flow_type": session.flow_type,
                    "previous_step": session.current_step,
                    "quality_gate_passed": quality_score is None or quality_score >= 0.7,
                    "template_selected": next_step_info["template_name"],
                    "context_enriched": True
                }
            )
            
        except Exception as e:
            return self._handle_error("next_step", str(e), input_data.session_id)
    
    def analyze_step(self, input_data: AnalyzeStepInput) -> MCPToolOutput:
        """
        Analyze the quality of a completed step
        
        Returns quality evaluation prompt template
        """
        try:
            # Get session state
            session = self.session_manager.get_session(input_data.session_id)
            if not session:
                return self._handle_session_not_found(input_data.session_id)
            
            # Get analysis template based on step type
            analysis_template_name = self._get_analysis_template_name(input_data.step_name)
            
            template_params = {
                "step_name": input_data.step_name,
                "step_result": input_data.step_result,
                "context": session.context,
                "analysis_type": input_data.analysis_type
            }
            
            prompt_template = self.template_manager.get_template(
                analysis_template_name,
                template_params
            )
            
            return MCPToolOutput(
                tool_name=MCPToolName.ANALYZE_STEP,
                session_id=input_data.session_id,
                step=f"analyze_{input_data.step_name}",
                prompt_template=prompt_template,
                instructions="请按照评估标准进行详细分析，并提供具体的改进建议",
                context={
                    "analyzed_step": input_data.step_name,
                    "analysis_type": input_data.analysis_type
                },
                next_action="根据分析结果决定是否需要重新执行步骤或继续下一步",
                metadata={
                    "quality_check": True,
                    "step_analyzed": input_data.step_name
                }
            )
            
        except Exception as e:
            return self._handle_error("analyze_step", str(e), input_data.session_id)
    
    def complete_thinking(self, input_data: CompleteThinkingInput) -> MCPToolOutput:
        """
        Complete the thinking process and generate final report
        
        Returns comprehensive summary prompt template
        """
        try:
            # Get session state
            session = self.session_manager.get_session(input_data.session_id)
            if not session:
                return self._handle_session_not_found(input_data.session_id)
            
            # Mark session as completed
            self.session_manager.complete_session(input_data.session_id)
            
            # Get summary template
            template_params = {
                "topic": session.topic,
                "step_summary": self.session_manager.get_step_summary(input_data.session_id),
                "thinking_trace": self.session_manager.get_full_trace(input_data.session_id),
                "quality_metrics": session.quality_scores,
                "final_insights": input_data.final_insights or ""
            }
            
            prompt_template = self.template_manager.get_template(
                "comprehensive_summary",
                template_params
            )
            
            return MCPToolOutput(
                tool_name=MCPToolName.COMPLETE_THINKING,
                session_id=input_data.session_id,
                step="generate_final_report",
                prompt_template=prompt_template,
                instructions="请生成详细的综合报告，包含所有关键发现和洞察",
                context={
                    "session_completed": True,
                    "total_steps": session.step_number
                },
                next_action="思维流程已完成，可以生成最终报告",
                metadata={
                    "session_status": "completed",
                    "thinking_trace_available": True,
                    "quality_metrics": session.quality_scores
                }
            )
            
        except Exception as e:
            return self._handle_error("complete_thinking", str(e), input_data.session_id)
    
    def _build_template_params(self, session: SessionState, previous_result: str) -> Dict[str, Any]:
        """Build template parameters from session context"""
        return {
            "topic": session.topic,
            "current_step": session.current_step,
            "previous_result": previous_result,
            "context": session.context,
            "step_results": session.step_results,
            "session_id": session.session_id
        }
    
    def _determine_next_step_with_context(self, session: SessionState, step_result: str, 
                                        quality_feedback: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
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
                "instructions": "根据质量反馈改进当前步骤的结果"
            }
        
        # Use flow manager for standard next step
        next_step_info = self.flow_manager.get_next_step(
            session.flow_type,
            session.current_step,
            step_result
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
    
    def _build_enhanced_template_params(self, session: SessionState, previous_result: str, 
                                      next_step_info: Dict[str, Any]) -> Dict[str, Any]:
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
            "domain_context": session.context.get("domain_context", session.context.get("focus", "general analysis")),
            "previous_steps_summary": self._get_previous_steps_summary(session),
            "quality_history": session.quality_scores,
            "session_duration": self._calculate_session_duration(session)
        }
        
        # Add step-specific context
        if next_step_info["step_name"] == "evidence":
            enhanced_params.update(self._get_evidence_context(session, previous_result))
        elif next_step_info["step_name"] == "evaluate":
            enhanced_params.update(self._get_evaluation_context(session))
        elif next_step_info["step_name"] == "reflect":
            enhanced_params.update(self._get_reflection_context(session))
        
        return enhanced_params
    
    def _get_contextual_template(self, template_name: str, template_params: Dict[str, Any], 
                               session: SessionState) -> str:
        """Get template with smart contextual selection"""
        # Select appropriate template variant based on context
        selected_template = template_name
        
        # Adapt template based on session context
        if session.context.get("complexity") == "simple" and template_name == "decomposition":
            selected_template = "simple_decomposition"
        elif session.context.get("complexity") == "complex" and template_name == "critical_evaluation":
            selected_template = "advanced_critical_evaluation"
        
        # Fallback to original template if variant doesn't exist
        try:
            return self.template_manager.get_template(selected_template, template_params)
        except:
            return self.template_manager.get_template(template_name, template_params)
    
    def _build_step_context(self, session: SessionState, next_step_info: Dict[str, Any]) -> Dict[str, Any]:
        """Build comprehensive context for the next step"""
        return {
            **session.context,
            "session_id": session.session_id,
            "topic": session.topic,
            "current_step": next_step_info["step_name"],
            "step_number": session.step_number + 1,
            "flow_type": session.flow_type,
            "completed_steps": list(session.step_results.keys()),
            "quality_scores": session.quality_scores,
            "step_context": {
                "step_type": next_step_info.get("step_type", "general"),
                "template_used": next_step_info["template_name"],
                "dependencies_met": True,
                "adaptive_selection": True
            }
        }
    
    def _generate_step_instructions(self, next_step_info: Dict[str, Any], session: SessionState) -> str:
        """Generate contextual instructions for the step"""
        base_instruction = next_step_info.get("instructions", f"Execute {next_step_info['step_name']} step")
        
        # Add contextual guidance
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
    
    def _determine_next_action(self, next_step_info: Dict[str, Any], session: SessionState) -> str:
        """Determine the recommended next action"""
        step_name = next_step_info["step_name"]
        
        if step_name in ["decompose", "evidence"]:
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
            "evidence_collection": "comprehensive_evidence_collection"
        }
        return complex_variants.get(template_name, template_name)
    
    def _generate_contextual_instructions(self, next_step_info: Dict[str, Any], 
                                        session: SessionState, step_result: str) -> str:
        """Generate contextual instructions based on session state"""
        base_instruction = f"Execute {next_step_info['step_name']} step"
        
        # Add context-specific guidance
        if "evidence" in step_result.lower() and next_step_info["step_name"] == "evaluate":
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
    
    def _get_evidence_context(self, session: SessionState, previous_result: str) -> Dict[str, Any]:
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
            "context": session.context.get("focus", "综合分析")
        }
    
    def _get_reflection_context(self, session: SessionState) -> Dict[str, Any]:
        """Get context specific to reflection step"""
        return {
            "thinking_history": self._get_previous_steps_summary(session),
            "current_conclusions": "基于前面步骤得出的结论"
        }
    
    def _get_analysis_template_name(self, step_name: str) -> str:
        """Get appropriate analysis template based on step name"""
        # Use existing templates for analysis since we don't have separate analysis templates
        analysis_templates = {
            "decompose_problem": "critical_evaluation",
            "collect_evidence": "critical_evaluation", 
            "multi_perspective_debate": "critical_evaluation",
            "critical_evaluation": "critical_evaluation",
            "bias_detection": "bias_detection",
            "innovation_thinking": "critical_evaluation",
            "reflection": "reflection"
        }
        return analysis_templates.get(step_name, "critical_evaluation")
    
    def _handle_session_not_found(self, session_id: str) -> MCPToolOutput:
        """Handle case where session is not found"""
        recovery_prompt = self.template_manager.get_template(
            "session_recovery",
            {"session_id": session_id}
        )
        
        return MCPToolOutput(
            tool_name=MCPToolName.NEXT_STEP,
            session_id=session_id,
            step="session_recovery",
            prompt_template=recovery_prompt,
            instructions="会话已丢失，请选择如何继续",
            context={"error": "session_not_found"},
            next_action="重新开始或尝试恢复会话",
            metadata={"error_recovery": True}
        )
    
    def _handle_flow_completion(self, session_id: str) -> MCPToolOutput:
        """Handle flow completion"""
        completion_prompt = self.template_manager.get_template(
            "flow_completion",
            {"session_id": session_id}
        )
        
        return MCPToolOutput(
            tool_name=MCPToolName.COMPLETE_THINKING,
            session_id=session_id,
            step="flow_completed",
            prompt_template=completion_prompt,
            instructions="思维流程已完成，准备生成最终报告",
            context={"flow_completed": True},
            next_action="调用complete_thinking生成最终报告",
            metadata={"ready_for_completion": True}
        )
    
    def _handle_error(self, tool_name: str, error_message: str, session_id: Optional[str] = None) -> MCPToolOutput:
        """Handle tool execution errors"""
        error_prompt = self.template_manager.get_template(
            "error_recovery",
            {
                "tool_name": tool_name,
                "error_message": error_message,
                "session_id": session_id
            }
        )
        
        return MCPToolOutput(
            tool_name=MCPToolName.NEXT_STEP,
            session_id=session_id,
            step="error_recovery",
            prompt_template=error_prompt,
            instructions="发生错误，请选择如何继续",
            context={
                "error": True,
                "error_message": error_message,
                "failed_tool": tool_name
            },
            next_action="选择错误恢复选项",
            metadata={
                "error_recovery": True,
                "original_tool": tool_name
            }
        )