"""
Core exception classes for the Deep Thinking Engine
"""


class DeepThinkingError(Exception):
    """Base exception for all deep thinking engine errors"""

    def __init__(self, message: str, error_code: str = None, details: dict = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}

    def to_dict(self) -> dict:
        """Convert exception to dictionary for serialization"""
        return {
            "error_type": self.__class__.__name__,
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
        }


class ConfigurationError(DeepThinkingError):
    """Raised when there are configuration-related errors"""

    pass


class FlowConfigurationError(ConfigurationError):
    """Raised when there are flow configuration errors"""

    pass


class AgentExecutionError(DeepThinkingError):
    """Raised when agent execution fails"""

    def __init__(
        self, message: str, agent_type: str = None, session_id: str = None, **kwargs
    ):
        super().__init__(message, **kwargs)
        self.agent_type = agent_type
        self.session_id = session_id
        if agent_type:
            self.details["agent_type"] = agent_type
        if session_id:
            self.details["session_id"] = session_id


class AgentTimeoutError(AgentExecutionError):
    """Raised when agent execution times out"""

    def __init__(self, message: str, timeout_seconds: int = None, **kwargs):
        super().__init__(message, **kwargs)
        self.timeout_seconds = timeout_seconds
        if timeout_seconds:
            self.details["timeout_seconds"] = timeout_seconds


class AgentValidationError(AgentExecutionError):
    """Raised when agent input validation fails"""

    def __init__(self, message: str, validation_errors: list = None, **kwargs):
        super().__init__(message, **kwargs)
        self.validation_errors = validation_errors or []
        if validation_errors:
            self.details["validation_errors"] = validation_errors


class AgentConfigurationError(ConfigurationError):
    """Raised when there are agent configuration errors"""

    def __init__(self, message: str, agent_type: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.agent_type = agent_type
        if agent_type:
            self.details["agent_type"] = agent_type


class AgentRegistrationError(DeepThinkingError):
    """Raised when agent registration fails"""

    def __init__(self, message: str, agent_type: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.agent_type = agent_type
        if agent_type:
            self.details["agent_type"] = agent_type


class AgentNotFoundError(DeepThinkingError):
    """Raised when a requested agent is not found"""

    def __init__(
        self, message: str, agent_type: str = None, instance_id: str = None, **kwargs
    ):
        super().__init__(message, **kwargs)
        self.agent_type = agent_type
        self.instance_id = instance_id
        if agent_type:
            self.details["agent_type"] = agent_type
        if instance_id:
            self.details["instance_id"] = instance_id


class FlowExecutionError(DeepThinkingError):
    """Raised when flow execution fails"""

    def __init__(
        self, message: str, flow_name: str = None, step_id: str = None, **kwargs
    ):
        super().__init__(message, **kwargs)
        self.flow_name = flow_name
        self.step_id = step_id
        if flow_name:
            self.details["flow_name"] = flow_name
        if step_id:
            self.details["step_id"] = step_id


class FlowStateError(DeepThinkingError):
    """Raised when there are flow state-related errors"""

    def __init__(
        self,
        message: str,
        flow_id: str = None,
        current_state: str = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.flow_id = flow_id
        self.current_state = current_state
        if flow_id:
            self.details["flow_id"] = flow_id
        if current_state:
            self.details["current_state"] = current_state


class InvalidTransitionError(FlowStateError):
    """Raised when an invalid state transition is attempted"""

    def __init__(
        self,
        message: str,
        flow_id: str = None,
        current_state: str = None,
        event: str = None,
        **kwargs
    ):
        super().__init__(message, flow_id, current_state, **kwargs)
        self.event = event
        if event:
            self.details["event"] = event


class DataValidationError(DeepThinkingError):
    """Raised when data validation fails"""

    def __init__(
        self, message: str, field_name: str = None, expected_type: str = None, **kwargs
    ):
        super().__init__(message, **kwargs)
        self.field_name = field_name
        self.expected_type = expected_type
        if field_name:
            self.details["field_name"] = field_name
        if expected_type:
            self.details["expected_type"] = expected_type


class ResourceError(DeepThinkingError):
    """Raised when there are resource-related errors"""

    def __init__(
        self, message: str, resource_type: str = None, resource_id: str = None, **kwargs
    ):
        super().__init__(message, **kwargs)
        self.resource_type = resource_type
        self.resource_id = resource_id
        if resource_type:
            self.details["resource_type"] = resource_type
        if resource_id:
            self.details["resource_id"] = resource_id


class CacheError(DeepThinkingError):
    """Raised when there are cache-related errors"""

    pass


class SearchError(DeepThinkingError):
    """Raised when search operations fail"""

    def __init__(
        self, message: str, query: str = None, search_type: str = None, **kwargs
    ):
        super().__init__(message, **kwargs)
        self.query = query
        self.search_type = search_type
        if query:
            self.details["query"] = query
        if search_type:
            self.details["search_type"] = search_type


class EvaluationError(DeepThinkingError):
    """Raised when evaluation processes fail"""

    def __init__(
        self,
        message: str,
        evaluation_type: str = None,
        content_id: str = None,
        **kwargs,
    ):
        super().__init__(message, **kwargs)
        self.evaluation_type = evaluation_type
        self.content_id = content_id
        if evaluation_type:
            self.details["evaluation_type"] = evaluation_type
        if content_id:
            self.details["content_id"] = content_id


class BiasDetectionError(EvaluationError):
    """Raised when bias detection fails"""

    pass


class InnovationError(DeepThinkingError):
    """Raised when innovation processes fail"""

    def __init__(self, message: str, method: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.method = method
        if method:
            self.details["method"] = method


class ReflectionError(DeepThinkingError):
    """Raised when reflection processes fail"""

    def __init__(self, message: str, reflection_type: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.reflection_type = reflection_type
        if reflection_type:
            self.details["reflection_type"] = reflection_type


class SessionError(DeepThinkingError):
    """Base class for session-related errors"""

    def __init__(self, message: str, session_id: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.session_id = session_id
        if session_id:
            self.details["session_id"] = session_id


class SessionNotFoundError(SessionError):
    """Raised when a requested session is not found"""

    pass


class SessionStateError(SessionError):
    """Raised when there are session state-related errors"""

    def __init__(
        self,
        message: str,
        current_state: str = None,
        expected_state: str = None,
        **kwargs,
    ):
        super().__init__(message, **kwargs)
        self.current_state = current_state
        self.expected_state = expected_state
        if current_state:
            self.details["current_state"] = current_state
        if expected_state:
            self.details["expected_state"] = expected_state


class SessionTimeoutError(SessionError):
    """Raised when a session times out"""

    def __init__(self, message: str, timeout_seconds: int = None, **kwargs):
        super().__init__(message, **kwargs)
        self.timeout_seconds = timeout_seconds
        if timeout_seconds:
            self.details["timeout_seconds"] = timeout_seconds


class DatabaseError(DeepThinkingError):
    """Raised when database operations fail"""

    def __init__(
        self, message: str, operation: str = None, table: str = None, **kwargs
    ):
        super().__init__(message, **kwargs)
        self.operation = operation
        self.table = table
        if operation:
            self.details["operation"] = operation
        if table:
            self.details["table"] = table


class TemplateError(DeepThinkingError):
    """Raised when template operations fail"""

    def __init__(
        self, message: str, template_name: str = None, template_type: str = None, **kwargs
    ):
        super().__init__(message, **kwargs)
        self.template_name = template_name
        self.template_type = template_type
        if template_name:
            self.details["template_name"] = template_name
        if template_type:
            self.details["template_type"] = template_type


class MCPToolError(DeepThinkingError):
    """Base class for MCP tool-related errors"""

    def __init__(
        self, message: str, tool_name: str = None, session_id: str = None, **kwargs
    ):
        super().__init__(message, **kwargs)
        self.tool_name = tool_name
        self.session_id = session_id
        if tool_name:
            self.details["tool_name"] = tool_name
        if session_id:
            self.details["session_id"] = session_id


class MCPToolExecutionError(MCPToolError):
    """Raised when MCP tool execution fails"""

    def __init__(
        self,
        message: str,
        tool_name: str = None,
        session_id: str = None,
        step_name: str = None,
        **kwargs,
    ):
        super().__init__(message, tool_name, session_id, **kwargs)
        self.step_name = step_name
        if step_name:
            self.details["step_name"] = step_name


class MCPToolValidationError(MCPToolError):
    """Raised when MCP tool input validation fails"""

    def __init__(
        self,
        message: str,
        tool_name: str = None,
        validation_errors: list = None,
        **kwargs,
    ):
        super().__init__(message, tool_name, **kwargs)
        self.validation_errors = validation_errors or []
        if validation_errors:
            self.details["validation_errors"] = validation_errors


class MCPSessionRecoveryError(MCPToolError):
    """Raised when MCP session recovery fails"""

    def __init__(
        self,
        message: str,
        session_id: str = None,
        recovery_data: dict = None,
        **kwargs,
    ):
        super().__init__(message, session_id=session_id, **kwargs)
        self.recovery_data = recovery_data
        if recovery_data:
            self.details["recovery_data"] = recovery_data


class MCPFormatValidationError(MCPToolError):
    """Raised when MCP tool output format validation fails"""

    def __init__(
        self,
        message: str,
        step_name: str = None,
        expected_format: str = None,
        actual_format: str = None,
        **kwargs,
    ):
        super().__init__(message, **kwargs)
        self.step_name = step_name
        self.expected_format = expected_format
        self.actual_format = actual_format
        if step_name:
            self.details["step_name"] = step_name
        if expected_format:
            self.details["expected_format"] = expected_format
        if actual_format:
            self.details["actual_format"] = actual_format


class MCPQualityGateError(MCPToolError):
    """Raised when quality gate validation fails"""

    def __init__(
        self,
        message: str,
        step_name: str = None,
        quality_score: float = None,
        quality_threshold: float = None,
        **kwargs,
    ):
        super().__init__(message, **kwargs)
        self.step_name = step_name
        self.quality_score = quality_score
        self.quality_threshold = quality_threshold
        if step_name:
            self.details["step_name"] = step_name
        if quality_score is not None:
            self.details["quality_score"] = quality_score
        if quality_threshold is not None:
            self.details["quality_threshold"] = quality_threshold
