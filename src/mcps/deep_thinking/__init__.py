"""
Deep Thinking Engine - Core Module

A sophisticated MCP-based system for deep thinking and critical analysis,
combining multiple AI agents with scientific thinking methodologies.
"""

from .models import *
from .agents import BaseAgent, AgentInterface, AgentRegistry
from .config import ConfigManager, FlowConfigManager, config_manager, flow_config_manager

__version__ = "0.1.0"

__all__ = [
    # Core Models
    'AgentInput',
    'AgentOutput', 
    'AgentConfig',
    'AgentMetadata',
    'ThinkingSession',
    'ThinkingTrace',
    'QuestionDecomposition',
    'SubQuestion',
    'EvidenceSource',
    'EvidenceCollection',
    'SearchQuery',
    'ConflictingInformation',
    'PaulElderEvaluation',
    'BiasAnalysis',
    'DebateResults',
    'InnovationResults',
    'ReflectionGuidance',
    
    # Agent Framework
    'BaseAgent',
    'AgentInterface',
    'AgentRegistry',
    
    # Configuration Management
    'ConfigManager',
    'FlowConfigManager',
    'config_manager',
    'flow_config_manager',
]