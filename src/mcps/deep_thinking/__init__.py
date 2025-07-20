"""
Deep Thinking Engine - Core Module

A sophisticated MCP-based system for deep thinking and critical analysis,
combining multiple AI agents with scientific thinking methodologies.
"""

__version__ = "0.1.0"


# Lazy imports to avoid dependency issues
def get_mcp_tools():
    """Get MCP tools - lazy import to avoid dependency issues"""
    from .tools.mcp_tools import MCPTools

    return MCPTools


def get_session_manager():
    """Get session manager - lazy import"""
    from .sessions.session_manager import SessionManager

    return SessionManager


def get_template_manager():
    """Get template manager - lazy import"""
    from .templates.template_manager import TemplateManager

    return TemplateManager


def get_flow_manager():
    """Get flow manager - lazy import"""
    from .flows.flow_manager import FlowManager

    return FlowManager
