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
