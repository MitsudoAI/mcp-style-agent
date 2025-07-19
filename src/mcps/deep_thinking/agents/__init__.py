"""
Deep Thinking Engine - Agent Framework

This module contains the base agent classes and interfaces for the deep thinking engine.
"""

from .base_agent import BaseAgent, AgentInterface
from .agent_registry import AgentRegistry

__all__ = [
    'BaseAgent',
    'AgentInterface', 
    'AgentRegistry',
]