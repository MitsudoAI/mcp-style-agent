"""
Deep Thinking Engine - Agent Framework

This module contains the base agent classes and interfaces for the deep thinking engine.
"""

from .agent_registry import AgentRegistry
from .base_agent import AgentInterface, BaseAgent

__all__ = [
    "BaseAgent",
    "AgentInterface",
    "AgentRegistry",
]
