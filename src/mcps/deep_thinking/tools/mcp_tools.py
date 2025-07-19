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
        """
        try:
            # Get current session state
            session = self.session_manager.get_session(input_data.session_id)
            if not session:
                return self._handle_session_not_found(input_data.session_id)
            
            # Save previous step result
            self.session_manager.add_step_result(
                input_data.session_id,
                session.current_step,
                input_data.step_result
            )
            
            # Determine next step based on flow
            next_step_info = self.flow_manager.get_next_step(
                session.flow_type,
                session.current_step,
                input_data.step_result
            )
            
            if not next_step_info:
                # Flow completed
                return self._handle_flow_completion(input_data.session_id)
            
            # Update session state
            self.session_manager.update_session_step(
                input_data.session_id,
                next_step_info["step_name"]
            )
            
            # Get appropriate prompt template
            template_params = self._build_template_params(session, input_data.step_result)
            prompt_template = self.template_manager.get_template(
                next_step_info["template_name"],
                template_params
            )
            
            return MCPToolOutput(
                tool_name=MCPToolName.NEXT_STEP,
                session_id=input_data.session_id,
                step=next_step_info["step_name"],
                prompt_template=prompt_template,
                instructions=next_step_info["instructions"],
                context=session.context,
                next_action="继续执行思维流程或调用analyze_step进行质量检查",
                metadata={
                    "step_number": session.step_number + 1,
                    "flow_progress": f"{session.step_number + 1}/{self.flow_manager.get_total_steps(session.flow_type)}"
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