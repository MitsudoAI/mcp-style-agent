"""
Deep Thinking Engine - Configuration Management

This module provides configuration management capabilities including YAML flow definitions,
hot reloading, and configuration validation.
"""

# Import only exceptions by default to avoid dependency issues
from .exceptions import *

__all__ = [
    # Exceptions
    'DeepThinkingError',
    'ConfigurationError',
    'FlowConfigurationError',
    'AgentExecutionError',
    'AgentTimeoutError',
    'AgentValidationError',
    'AgentConfigurationError',
    'AgentRegistrationError',
    'AgentNotFoundError',
]

# Lazy imports to avoid dependency issues
def get_config_manager():
    """Get config manager - lazy import to avoid dependency issues"""
    from .config_manager import ConfigManager, config_manager
    return ConfigManager, config_manager

def get_flow_config_manager():
    """Get flow config manager - lazy import"""
    from .flow_config import FlowConfigManager, flow_config_manager
    return FlowConfigManager, flow_config_manager