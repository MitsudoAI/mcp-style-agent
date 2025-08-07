"""
MCP Tool Error Handler for Deep Thinking Engine

Implements comprehensive error handling for MCP tools following the zero-cost principle:
- Captures and handles tool call exceptions
- Provides error recovery prompt templates
- Manages session recovery and state repair
- Maintains system stability without LLM API calls
"""

import logging
import traceback
from datetime import datetime
from typing import Any, Dict, Optional

from ..config.exceptions import (
    DeepThinkingError,
    SessionError,
    SessionNotFoundError,
    SessionStateError,
    TemplateError,
)
from ..models.mcp_models import MCPToolName, MCPToolOutput
from ..sessions.session_manager import SessionManager
from ..templates.template_manager import TemplateManager

logger = logging.getLogger(__name__)


class MCPErrorHandler:
    """
    Comprehensive error handler for MCP tools
    
    Provides error recovery mechanisms and prompt templates for various failure scenarios
    """

    def __init__(
        self,
        session_manager: SessionManager,
        template_manager: TemplateManager,
    ):
        self.session_manager = session_manager
        self.template_manager = template_manager
        self.error_recovery_templates = self._initialize_error_templates()

    def _initialize_error_templates(self) -> Dict[str, str]:
        """Initialize error recovery prompt templates"""
        return {
            "session_not_found": """
# 会话恢复

抱歉，之前的思考会话似乎中断了。让我们重新开始：

**会话ID**: {session_id}
**错误类型**: 会话未找到

## 恢复选项：

### 选项1: 重新开始完整流程
如果你想从头开始一个新的深度思考流程，请提供：
- 你想要分析的问题或主题
- 分析的复杂度（简单/中等/复杂）
- 特别关注的方面

### 选项2: 快速分析模式
如果你想进行快速分析，请直接描述你的问题，我将提供简化的分析框架。

### 选项3: 尝试恢复（如果你记得之前的进展）
如果你记得之前的分析内容，请提供：
- 原始问题
- 已完成的步骤
- 当前想要继续的步骤

请选择一个选项并提供相应信息，我将为你创建新的思考框架。
""",
            "invalid_step_result": """
# 格式修正指导

你的上一步结果格式需要调整。让我帮你修正：

**步骤**: {step_name}
**问题**: {format_issues}

## 正确格式要求：
{expected_format}

## 修正建议：
{improvement_suggestions}

## 请重新提供结果：
请按照上述格式要求重新整理你的分析结果。如果需要，我可以提供具体的示例格式。

**提示**: {format_hint}
""",
            "template_missing": """
# 模板缺失处理

系统遇到了模板缺失的问题，但我们可以继续：

**缺失模板**: {template_name}
**当前步骤**: {step_name}

## 通用分析框架：

### 分析目标
请针对当前步骤进行分析，重点关注：
1. **核心问题**: 明确要解决的关键问题
2. **分析方法**: 选择合适的分析方法和角度
3. **证据支撑**: 收集和评估相关证据
4. **逻辑推理**: 进行清晰的逻辑推理
5. **结论总结**: 得出明确的结论和建议

### 质量标准
确保你的分析：
- 逻辑清晰，结构完整
- 有充分的证据支撑
- 考虑了多个角度和观点
- 结论明确，建议可行

请按照这个框架进行分析。
""",
            "flow_interrupted": """
# 流程恢复

思考流程出现了中断，让我们评估情况并继续：

**会话ID**: {session_id}
**中断位置**: {current_step}
**已完成步骤**: {completed_steps}

## 恢复策略：

### 当前状态分析
- 已完成: {progress_summary}
- 当前质量水平: {quality_status}
- 下一步建议: {next_step_recommendation}

### 继续选项：

**选项A: 从中断点继续**
继续执行 {current_step} 步骤，基于已有的分析结果。

**选项B: 回到上一步**
如果当前步骤结果不满意，可以回到 {previous_step} 重新分析。

**选项C: 跳转到特定步骤**
如果你想专注于某个特定方面，可以直接跳转到相应步骤。

**选项D: 生成当前总结**
基于已完成的步骤生成阶段性总结报告。

请选择一个选项，我将提供相应的分析框架。
""",
            "quality_gate_failed": """
# 质量改进指导

当前步骤的质量评估未达到标准，让我们一起改进：

**步骤**: {step_name}
**质量得分**: {quality_score}/10
**质量阈值**: {quality_threshold}/10

## 主要问题：
{quality_issues}

## 改进建议：

### 1. 内容深度
{depth_suggestions}

### 2. 逻辑结构
{logic_suggestions}

### 3. 证据支撑
{evidence_suggestions}

### 4. 分析全面性
{breadth_suggestions}

## 重新分析框架：
请基于以上建议重新进行分析，特别注意：
- 增加分析深度和细节
- 完善逻辑推理过程
- 补充更多证据支撑
- 考虑更多角度和观点

**目标**: 将质量得分提升到 {quality_threshold} 分以上。
""",
            "session_timeout": """
# 会话超时恢复

你的思考会话已超时，但我们可以恢复：

**会话ID**: {session_id}
**超时时间**: {timeout_duration}
**最后活动**: {last_activity}

## 恢复选项：

### 快速恢复
如果你想继续之前的分析：
1. 简要描述你记得的分析内容
2. 说明你想要继续的步骤
3. 我将为你重建分析框架

### 重新开始
如果你想重新开始：
1. 提供你的分析主题
2. 选择分析复杂度
3. 我将创建新的思考流程

### 部分恢复
如果你只想恢复某个特定方面：
1. 说明你想要分析的具体问题
2. 我将提供针对性的分析框架

请选择恢复方式，我将立即为你提供相应的支持。
""",
        }

    def handle_mcp_error(
        self,
        tool_name: str,
        error: Exception,
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> MCPToolOutput:
        """
        Handle MCP tool errors and return appropriate recovery prompt
        
        Args:
            tool_name: Name of the tool that failed
            error: The exception that occurred
            session_id: Session ID if available
            context: Additional context information
            
        Returns:
            MCPToolOutput with error recovery prompt
        """
        try:
            # Log the error for debugging
            logger.error(
                f"MCP tool error in {tool_name}: {str(error)}",
                extra={
                    "tool_name": tool_name,
                    "session_id": session_id,
                    "error_type": type(error).__name__,
                    "context": context,
                    "traceback": traceback.format_exc(),
                }
            )

            # Determine error type and create appropriate response
            error_type = self._classify_error(error)
            recovery_response = self._create_recovery_response(
                error_type, tool_name, error, session_id, context
            )

            return recovery_response

        except Exception as handler_error:
            # Fallback error handling if the handler itself fails
            logger.critical(
                f"Error handler failed: {str(handler_error)}",
                extra={"original_error": str(error), "handler_error": str(handler_error)}
            )
            return self._create_fallback_response(tool_name, error, session_id)

    def _classify_error(self, error: Exception) -> str:
        """Classify error type for appropriate handling"""
        if isinstance(error, SessionNotFoundError):
            return "session_not_found"
        elif isinstance(error, SessionStateError):
            return "session_state_error"
        elif isinstance(error, TemplateError):
            return "template_missing"
        elif "timeout" in str(error).lower():
            return "session_timeout"
        elif isinstance(error, SessionError) and "timeout" in str(error).lower():
            return "session_timeout"
        elif "format" in str(error).lower() or "validation" in str(error).lower():
            return "invalid_step_result"
        elif "interrupted" in str(error).lower() or "flow" in str(error).lower():
            return "flow_interrupted"
        elif "quality" in str(error).lower():
            return "quality_gate_failed"
        else:
            return "generic_error"

    def _create_recovery_response(
        self,
        error_type: str,
        tool_name: str,
        error: Exception,
        session_id: Optional[str],
        context: Optional[Dict[str, Any]],
    ) -> MCPToolOutput:
        """Create appropriate recovery response based on error type"""
        
        if error_type == "session_not_found":
            return self._handle_session_not_found(session_id, context)
        elif error_type == "invalid_step_result":
            return self._handle_format_validation_failure(session_id, context)
        elif error_type == "template_missing":
            return self._handle_template_missing(tool_name, session_id, context)
        elif error_type == "flow_interrupted":
            return self._handle_flow_interruption(session_id, context)
        elif error_type == "quality_gate_failed":
            return self._handle_quality_gate_failure(session_id, context)
        elif error_type == "session_timeout":
            return self._handle_session_timeout(session_id, context)
        else:
            return self._handle_generic_error(tool_name, error, session_id, context)

    def _handle_session_not_found(
        self, session_id: Optional[str], context: Optional[Dict[str, Any]]
    ) -> MCPToolOutput:
        """Handle session not found error"""
        template_params = {
            "session_id": session_id or "未知",
            "error_timestamp": datetime.now().isoformat(),
        }

        prompt_template = self.error_recovery_templates["session_not_found"].format(
            **template_params
        )

        # Merge original context with error context
        error_context = {
            "error_type": "session_not_found",
            "recovery_mode": True,
            "original_session_id": session_id,
            "recovery_options": ["restart", "quick_analysis", "manual_recovery"],
        }
        
        # Include original context if provided
        if context:
            error_context.update({f"original_{k}": v for k, v in context.items()})

        return MCPToolOutput(
            tool_name=MCPToolName.START_THINKING,  # Redirect to start new session
            session_id=session_id or "recovery",
            step="session_recovery",
            prompt_template=prompt_template,
            instructions="会话已丢失，请选择恢复方式继续分析",
            context=error_context,
            next_action="选择恢复选项后，我将为你创建新的分析框架",
            metadata={
                "error_recovery": True,
                "error_type": "session_not_found",
                "recovery_timestamp": datetime.now().isoformat(),
                "requires_user_choice": True,
            },
        )

    def _handle_format_validation_failure(
        self, session_id: Optional[str], context: Optional[Dict[str, Any]]
    ) -> MCPToolOutput:
        """Handle format validation failure"""
        step_name = context.get("step_name", "unknown") if context else "unknown"
        format_issues = context.get("format_issues", ["格式不正确"]) if context else ["格式不正确"]
        expected_format = context.get("expected_format", "请参考文档格式要求") if context else "请参考文档格式要求"

        template_params = {
            "step_name": step_name,
            "format_issues": "\n".join(f"- {issue}" for issue in format_issues),
            "expected_format": expected_format,
            "improvement_suggestions": self._generate_format_improvement_suggestions(step_name),
            "format_hint": self._get_format_hint(step_name),
        }

        prompt_template = self.error_recovery_templates["invalid_step_result"].format(
            **template_params
        )

        return MCPToolOutput(
            tool_name=MCPToolName.NEXT_STEP,
            session_id=session_id or "recovery",
            step=f"fix_format_{step_name}",
            prompt_template=prompt_template,
            instructions="请按照正确格式重新整理你的分析结果",
            context={
                "error_type": "format_validation_failed",
                "step_name": step_name,
                "format_issues": format_issues,
                "expected_format": expected_format,
                "recovery_mode": True,
            },
            next_action="修正格式后，可以继续下一步分析",
            metadata={
                "error_recovery": True,
                "error_type": "format_validation_failed",
                "step_name": step_name,
                "format_correction_required": True,
            },
        )

    def _handle_template_missing(
        self, tool_name: str, session_id: Optional[str], context: Optional[Dict[str, Any]]
    ) -> MCPToolOutput:
        """Handle missing template error"""
        template_name = context.get("template_name", "unknown") if context else "unknown"
        step_name = context.get("step_name", "unknown") if context else "unknown"

        template_params = {
            "template_name": template_name,
            "step_name": step_name,
        }

        prompt_template = self.error_recovery_templates["template_missing"].format(
            **template_params
        )

        return MCPToolOutput(
            tool_name=MCPToolName.NEXT_STEP,
            session_id=session_id or "recovery",
            step=f"generic_{step_name}",
            prompt_template=prompt_template,
            instructions="使用通用分析框架继续分析",
            context={
                "error_type": "template_missing",
                "template_name": template_name,
                "step_name": step_name,
                "using_generic_template": True,
                "recovery_mode": True,
            },
            next_action="按照通用框架完成分析后，可以继续下一步",
            metadata={
                "error_recovery": True,
                "error_type": "template_missing",
                "fallback_template_used": True,
                "original_template": template_name,
            },
        )

    def _handle_flow_interruption(
        self, session_id: Optional[str], context: Optional[Dict[str, Any]]
    ) -> MCPToolOutput:
        """Handle flow interruption error"""
        current_step = context.get("current_step", "unknown") if context else "unknown"
        completed_steps = context.get("completed_steps", []) if context else []
        
        template_params = {
            "session_id": session_id or "unknown",
            "current_step": current_step,
            "completed_steps": ", ".join(completed_steps) if completed_steps else "无",
            "progress_summary": self._generate_progress_summary(completed_steps),
            "quality_status": context.get("quality_status", "未知") if context else "未知",
            "next_step_recommendation": self._get_next_step_recommendation(current_step),
            "previous_step": completed_steps[-1] if completed_steps else "无",
        }

        prompt_template = self.error_recovery_templates["flow_interrupted"].format(
            **template_params
        )

        return MCPToolOutput(
            tool_name=MCPToolName.NEXT_STEP,
            session_id=session_id or "recovery",
            step="flow_recovery",
            prompt_template=prompt_template,
            instructions="选择恢复策略继续思考流程",
            context={
                "error_type": "flow_interrupted",
                "current_step": current_step,
                "completed_steps": completed_steps,
                "recovery_options": ["continue", "retry", "jump", "summarize"],
                "recovery_mode": True,
            },
            next_action="选择恢复选项后，我将提供相应的分析框架",
            metadata={
                "error_recovery": True,
                "error_type": "flow_interrupted",
                "recovery_options_available": True,
                "flow_state_preserved": len(completed_steps) > 0,
            },
        )

    def _handle_quality_gate_failure(
        self, session_id: Optional[str], context: Optional[Dict[str, Any]]
    ) -> MCPToolOutput:
        """Handle quality gate failure"""
        step_name = context.get("step_name", "unknown") if context else "unknown"
        quality_score = context.get("quality_score", 0) if context else 0
        quality_threshold = context.get("quality_threshold", 7) if context else 7
        quality_issues = context.get("quality_issues", ["质量不达标"]) if context else ["质量不达标"]

        template_params = {
            "step_name": step_name,
            "quality_score": quality_score,
            "quality_threshold": quality_threshold,
            "quality_issues": "\n".join(f"- {issue}" for issue in quality_issues),
            "depth_suggestions": self._get_depth_improvement_suggestions(step_name),
            "logic_suggestions": self._get_logic_improvement_suggestions(step_name),
            "evidence_suggestions": self._get_evidence_improvement_suggestions(step_name),
            "breadth_suggestions": self._get_breadth_improvement_suggestions(step_name),
        }

        prompt_template = self.error_recovery_templates["quality_gate_failed"].format(
            **template_params
        )

        return MCPToolOutput(
            tool_name=MCPToolName.ANALYZE_STEP,
            session_id=session_id or "recovery",
            step=f"improve_{step_name}",
            prompt_template=prompt_template,
            instructions=f"根据质量反馈改进 {step_name} 步骤的分析结果",
            context={
                "error_type": "quality_gate_failed",
                "step_name": step_name,
                "quality_score": quality_score,
                "quality_threshold": quality_threshold,
                "improvement_required": True,
                "recovery_mode": True,
            },
            next_action="改进分析质量后，重新进行质量评估",
            metadata={
                "error_recovery": True,
                "error_type": "quality_gate_failed",
                "quality_improvement_required": True,
                "target_quality": quality_threshold,
            },
        )

    def _handle_session_timeout(
        self, session_id: Optional[str], context: Optional[Dict[str, Any]]
    ) -> MCPToolOutput:
        """Handle session timeout error"""
        timeout_duration = context.get("timeout_duration", "未知") if context else "未知"
        last_activity = context.get("last_activity", "未知") if context else "未知"

        template_params = {
            "session_id": session_id or "unknown",
            "timeout_duration": timeout_duration,
            "last_activity": last_activity,
        }

        prompt_template = self.error_recovery_templates["session_timeout"].format(
            **template_params
        )

        return MCPToolOutput(
            tool_name=MCPToolName.START_THINKING,
            session_id=session_id or "recovery",
            step="timeout_recovery",
            prompt_template=prompt_template,
            instructions="会话已超时，请选择恢复方式",
            context={
                "error_type": "session_timeout",
                "original_session_id": session_id,
                "timeout_duration": timeout_duration,
                "recovery_options": ["quick_recovery", "restart", "partial_recovery"],
                "recovery_mode": True,
            },
            next_action="选择恢复方式后，我将为你重建分析框架",
            metadata={
                "error_recovery": True,
                "error_type": "session_timeout",
                "timeout_recovery_available": True,
            },
        )

    def _handle_generic_error(
        self,
        tool_name: str,
        error: Exception,
        session_id: Optional[str],
        context: Optional[Dict[str, Any]],
    ) -> MCPToolOutput:
        """Handle generic errors"""
        error_message = str(error)
        error_type = type(error).__name__

        prompt_template = f"""
# 系统错误恢复

系统遇到了一个错误，但我们可以继续：

**工具**: {tool_name}
**错误类型**: {error_type}
**错误信息**: {error_message}
**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 恢复建议：

### 选项1: 重试操作
如果这是临时错误，我们可以重试刚才的操作。

### 选项2: 跳过当前步骤
如果当前步骤不是必需的，我们可以跳过并继续下一步。

### 选项3: 使用替代方法
我可以为你提供替代的分析方法来达到相同目标。

### 选项4: 重新开始
如果问题严重，我们可以重新开始整个分析流程。

请告诉我你希望如何处理这个错误，我将为你提供相应的支持。

**提示**: 大多数情况下，选择"重试操作"或"使用替代方法"可以解决问题。
"""

        # Merge original context with error context
        error_context = {
            "error_type": "generic_error",
            "original_tool": tool_name,
            "error_message": error_message,
            "error_class": error_type,
            "recovery_options": ["retry", "skip", "alternative", "restart"],
            "recovery_mode": True,
        }
        
        # Include original context if provided
        if context:
            error_context.update({f"original_{k}": v for k, v in context.items()})

        return MCPToolOutput(
            tool_name=MCPToolName.NEXT_STEP,
            session_id=session_id or "recovery",
            step="error_recovery",
            prompt_template=prompt_template,
            instructions="选择错误恢复方式继续分析",
            context=error_context,
            next_action="选择恢复方式后，我将提供相应的解决方案",
            metadata={
                "error_recovery": True,
                "error_type": "generic_error",
                "original_error": error_type,
                "fallback_recovery": True,
            },
        )

    def _create_fallback_response(
        self, tool_name: str, error: Exception, session_id: Optional[str]
    ) -> MCPToolOutput:
        """Create fallback response when error handler itself fails"""
        prompt_template = f"""
# 系统恢复模式

系统遇到了严重错误，现在进入恢复模式：

**状态**: 系统错误恢复
**工具**: {tool_name}
**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 基本恢复选项：

1. **重新开始**: 从头开始新的分析流程
2. **简化分析**: 使用基本分析框架
3. **手动指导**: 我将提供逐步指导

请选择一个选项，我将尽力为你提供支持。

**注意**: 系统正在恢复模式下运行，功能可能有限，但基本分析功能仍然可用。
"""

        return MCPToolOutput(
            tool_name=MCPToolName.START_THINKING,
            session_id=session_id or "emergency_recovery",
            step="emergency_recovery",
            prompt_template=prompt_template,
            instructions="系统恢复模式，请选择基本恢复选项",
            context={
                "error_type": "system_error",
                "recovery_mode": "emergency",
                "limited_functionality": True,
            },
            next_action="选择恢复选项，系统将提供基本支持",
            metadata={
                "error_recovery": True,
                "error_type": "system_error",
                "emergency_mode": True,
                "handler_failed": True,
            },
        )

    def recover_session_state(
        self, session_id: str, recovery_data: Dict[str, Any]
    ) -> bool:
        """
        Attempt to recover session state from provided data
        
        Args:
            session_id: Session ID to recover
            recovery_data: Data to use for recovery
            
        Returns:
            True if recovery successful, False otherwise
        """
        try:
            # Validate recovery data
            if not self._validate_recovery_data(recovery_data):
                logger.warning(f"Invalid recovery data for session {session_id}")
                return False

            # Attempt to recover session
            success = self.session_manager.recover_session(session_id, recovery_data)
            
            if success:
                logger.info(f"Successfully recovered session {session_id}")
            else:
                logger.warning(f"Failed to recover session {session_id}")
                
            return success

        except Exception as e:
            logger.error(f"Error during session recovery: {str(e)}")
            return False

    def _validate_recovery_data(self, recovery_data: Dict[str, Any]) -> bool:
        """Validate recovery data structure"""
        required_fields = ["topic", "current_step"]
        return all(field in recovery_data for field in required_fields)

    def _generate_format_improvement_suggestions(self, step_name: str) -> str:
        """Generate format improvement suggestions for specific steps"""
        suggestions = {
            "decompose_problem": "确保使用JSON格式，包含main_question、sub_questions和relationships字段",
            "collect_evidence": "包含证据来源、可信度评估和关键发现",
            "multi_perspective_debate": "分别列出支持方、反对方和中立方的观点",
            "critical_evaluation": "使用Paul-Elder九大标准进行评分",
            "bias_detection": "列出检测到的偏见类型和具体证据",
            "innovation_thinking": "使用SCAMPER方法的七个步骤",
            "reflection": "回答苏格拉底式提问的各个问题",
        }
        return suggestions.get(step_name, "请参考步骤要求的具体格式")

    def _get_format_hint(self, step_name: str) -> str:
        """Get format hint for specific steps"""
        hints = {
            "decompose_problem": "使用JSON格式，确保所有字段都有值",
            "collect_evidence": "结构化列出证据，包含来源链接",
            "multi_perspective_debate": "分角色清晰表达不同观点",
            "critical_evaluation": "提供具体评分和理由",
            "bias_detection": "引用具体句子作为偏见证据",
            "innovation_thinking": "逐步应用SCAMPER各个技法",
            "reflection": "深入回答每个反思问题",
        }
        return hints.get(step_name, "参考文档中的格式示例")

    def _generate_progress_summary(self, completed_steps: list) -> str:
        """Generate progress summary from completed steps"""
        if not completed_steps:
            return "尚未完成任何步骤"
        
        step_descriptions = {
            "decompose_problem": "问题分解",
            "collect_evidence": "证据收集",
            "multi_perspective_debate": "多角度辩论",
            "critical_evaluation": "批判性评估",
            "bias_detection": "偏见检测",
            "innovation_thinking": "创新思维",
            "reflection": "反思总结",
        }
        
        completed_descriptions = [
            step_descriptions.get(step, step) for step in completed_steps
        ]
        return f"已完成: {', '.join(completed_descriptions)}"

    def _get_next_step_recommendation(self, current_step: str) -> str:
        """Get next step recommendation based on current step"""
        recommendations = {
            "decompose_problem": "建议继续进行证据收集",
            "collect_evidence": "建议进行多角度辩论分析",
            "multi_perspective_debate": "建议进行批判性评估",
            "critical_evaluation": "建议进行偏见检测",
            "bias_detection": "建议进行创新思维",
            "innovation_thinking": "建议进行反思总结",
            "reflection": "建议生成最终报告",
        }
        return recommendations.get(current_step, "继续下一步分析")

    def _get_depth_improvement_suggestions(self, step_name: str) -> str:
        """Get depth improvement suggestions for specific steps"""
        suggestions = {
            "decompose_problem": "深入分析每个子问题的复杂性和相互关系",
            "collect_evidence": "寻找更多权威来源，增加证据的多样性",
            "multi_perspective_debate": "深入探讨每个观点的理论基础",
            "critical_evaluation": "详细分析每个评估维度的具体表现",
            "bias_detection": "深入分析偏见产生的心理机制",
            "innovation_thinking": "探索更多创新可能性和实施细节",
            "reflection": "深入思考认知过程和改进空间",
        }
        return suggestions.get(step_name, "增加分析的深度和细节")

    def _get_logic_improvement_suggestions(self, step_name: str) -> str:
        """Get logic improvement suggestions for specific steps"""
        return "确保推理过程清晰，避免逻辑跳跃，加强论证的连贯性"

    def _get_evidence_improvement_suggestions(self, step_name: str) -> str:
        """Get evidence improvement suggestions for specific steps"""
        return "补充更多可靠证据，确保证据与结论之间的逻辑关系"

    def _get_breadth_improvement_suggestions(self, step_name: str) -> str:
        """Get breadth improvement suggestions for specific steps"""
        return "考虑更多角度和观点，扩大分析的覆盖面"