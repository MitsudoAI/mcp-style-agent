"""
Agent registry for managing agent lifecycle and discovery
"""

from typing import Dict, List, Optional, Type, Any
from datetime import datetime
import asyncio
import logging

from ..models.agent_models import (
    AgentType, AgentConfig, AgentMetadata, AgentRegistration, AgentStatus
)
from ..config.exceptions import AgentRegistrationError, AgentNotFoundError
from .base_agent import BaseAgent, AgentFactory


logger = logging.getLogger(__name__)


class AgentRegistry:
    """
    Central registry for managing agent lifecycle, discovery, and metadata
    """
    
    def __init__(self):
        self._registrations: Dict[AgentType, AgentRegistration] = {}
        self._active_agents: Dict[str, BaseAgent] = {}  # instance_id -> agent
        self._agent_instances: Dict[AgentType, List[str]] = {}  # agent_type -> [instance_ids]
        self._lock = asyncio.Lock()
    
    async def register_agent(
        self, 
        agent_type: AgentType,
        agent_class: Type[BaseAgent],
        metadata: AgentMetadata,
        default_config: Optional[AgentConfig] = None
    ) -> None:
        """
        Register an agent type with the registry
        
        Args:
            agent_type: Type of agent to register
            agent_class: Agent class implementation
            metadata: Agent metadata
            default_config: Default configuration for the agent
            
        Raises:
            AgentRegistrationError: If registration fails
        """
        async with self._lock:
            try:
                # Validate agent class
                if not issubclass(agent_class, BaseAgent):
                    raise AgentRegistrationError(
                        f"Agent class must inherit from BaseAgent"
                    )
                
                # Create default config if not provided
                if default_config is None:
                    # Create a temporary instance to get default config
                    temp_instance = agent_class()
                    default_config = temp_instance.get_default_config()
                
                # Validate metadata matches agent type
                if metadata.agent_type != agent_type:
                    raise AgentRegistrationError(
                        f"Metadata agent_type {metadata.agent_type} doesn't match {agent_type}"
                    )
                
                # Create registration
                registration = AgentRegistration(
                    agent_type=agent_type,
                    class_name=agent_class.__name__,
                    module_path=f"{agent_class.__module__}.{agent_class.__name__}",
                    metadata=metadata,
                    config=default_config,
                    is_active=True
                )
                
                # Register with factory
                AgentFactory.register_agent(agent_type, agent_class)
                
                # Store registration
                self._registrations[agent_type] = registration
                self._agent_instances[agent_type] = []
                
                logger.info(f"Successfully registered agent: {agent_type}")
                
            except Exception as e:
                raise AgentRegistrationError(f"Failed to register agent {agent_type}: {str(e)}")
    
    async def unregister_agent(self, agent_type: AgentType) -> None:
        """
        Unregister an agent type
        
        Args:
            agent_type: Type of agent to unregister
        """
        async with self._lock:
            if agent_type not in self._registrations:
                raise AgentNotFoundError(f"Agent type {agent_type} is not registered")
            
            # Deactivate all instances
            instance_ids = self._agent_instances.get(agent_type, [])
            for instance_id in instance_ids:
                if instance_id in self._active_agents:
                    del self._active_agents[instance_id]
            
            # Remove from registry
            del self._registrations[agent_type]
            del self._agent_instances[agent_type]
            
            logger.info(f"Unregistered agent: {agent_type}")
    
    async def create_agent_instance(
        self, 
        agent_type: AgentType, 
        config: Optional[AgentConfig] = None,
        instance_id: Optional[str] = None
    ) -> str:
        """
        Create a new agent instance
        
        Args:
            agent_type: Type of agent to create
            config: Optional custom configuration
            instance_id: Optional custom instance ID
            
        Returns:
            str: Instance ID of the created agent
            
        Raises:
            AgentNotFoundError: If agent type is not registered
        """
        async with self._lock:
            if agent_type not in self._registrations:
                raise AgentNotFoundError(f"Agent type {agent_type} is not registered")
            
            registration = self._registrations[agent_type]
            if not registration.is_active:
                raise AgentRegistrationError(f"Agent type {agent_type} is not active")
            
            # Use provided config or default
            agent_config = config or registration.config
            
            # Create agent instance
            agent = AgentFactory.create_agent(agent_type, agent_config)
            
            # Generate instance ID if not provided
            if instance_id is None:
                instance_id = f"{agent_type}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            
            # Store instance
            self._active_agents[instance_id] = agent
            self._agent_instances[agent_type].append(instance_id)
            
            logger.info(f"Created agent instance: {instance_id} ({agent_type})")
            return instance_id
    
    async def get_agent_instance(self, instance_id: str) -> BaseAgent:
        """
        Get an agent instance by ID
        
        Args:
            instance_id: Instance ID
            
        Returns:
            BaseAgent: Agent instance
            
        Raises:
            AgentNotFoundError: If instance is not found
        """
        if instance_id not in self._active_agents:
            raise AgentNotFoundError(f"Agent instance {instance_id} not found")
        
        return self._active_agents[instance_id]
    
    async def destroy_agent_instance(self, instance_id: str) -> None:
        """
        Destroy an agent instance
        
        Args:
            instance_id: Instance ID to destroy
        """
        async with self._lock:
            if instance_id not in self._active_agents:
                raise AgentNotFoundError(f"Agent instance {instance_id} not found")
            
            agent = self._active_agents[instance_id]
            agent_type = agent.agent_type
            
            # Remove from active agents
            del self._active_agents[instance_id]
            
            # Remove from type instances
            if agent_type in self._agent_instances:
                self._agent_instances[agent_type] = [
                    id for id in self._agent_instances[agent_type] if id != instance_id
                ]
            
            logger.info(f"Destroyed agent instance: {instance_id}")
    
    def get_registered_types(self) -> List[AgentType]:
        """
        Get list of registered agent types
        """
        return list(self._registrations.keys())
    
    def get_agent_metadata(self, agent_type: AgentType) -> AgentMetadata:
        """
        Get metadata for an agent type
        
        Args:
            agent_type: Agent type
            
        Returns:
            AgentMetadata: Agent metadata
            
        Raises:
            AgentNotFoundError: If agent type is not registered
        """
        if agent_type not in self._registrations:
            raise AgentNotFoundError(f"Agent type {agent_type} is not registered")
        
        return self._registrations[agent_type].metadata
    
    def get_agent_config(self, agent_type: AgentType) -> AgentConfig:
        """
        Get default configuration for an agent type
        
        Args:
            agent_type: Agent type
            
        Returns:
            AgentConfig: Default configuration
            
        Raises:
            AgentNotFoundError: If agent type is not registered
        """
        if agent_type not in self._registrations:
            raise AgentNotFoundError(f"Agent type {agent_type} is not registered")
        
        return self._registrations[agent_type].config
    
    def get_active_instances(self, agent_type: Optional[AgentType] = None) -> List[str]:
        """
        Get list of active agent instances
        
        Args:
            agent_type: Optional filter by agent type
            
        Returns:
            List[str]: List of instance IDs
        """
        if agent_type is None:
            return list(self._active_agents.keys())
        
        return self._agent_instances.get(agent_type, [])
    
    def get_registry_status(self) -> Dict[str, Any]:
        """
        Get overall registry status
        
        Returns:
            Dict[str, Any]: Registry status information
        """
        total_registered = len(self._registrations)
        active_types = len([r for r in self._registrations.values() if r.is_active])
        total_instances = len(self._active_agents)
        
        instances_by_type = {
            agent_type.value: len(instances) 
            for agent_type, instances in self._agent_instances.items()
        }
        
        return {
            'total_registered_types': total_registered,
            'active_types': active_types,
            'total_active_instances': total_instances,
            'instances_by_type': instances_by_type,
            'registered_types': [t.value for t in self._registrations.keys()],
            'registry_timestamp': datetime.now().isoformat()
        }
    
    async def activate_agent_type(self, agent_type: AgentType) -> None:
        """
        Activate an agent type
        
        Args:
            agent_type: Agent type to activate
        """
        async with self._lock:
            if agent_type not in self._registrations:
                raise AgentNotFoundError(f"Agent type {agent_type} is not registered")
            
            self._registrations[agent_type].is_active = True
            logger.info(f"Activated agent type: {agent_type}")
    
    async def deactivate_agent_type(self, agent_type: AgentType) -> None:
        """
        Deactivate an agent type (prevents new instances)
        
        Args:
            agent_type: Agent type to deactivate
        """
        async with self._lock:
            if agent_type not in self._registrations:
                raise AgentNotFoundError(f"Agent type {agent_type} is not registered")
            
            self._registrations[agent_type].is_active = False
            logger.info(f"Deactivated agent type: {agent_type}")
    
    def is_agent_registered(self, agent_type: AgentType) -> bool:
        """
        Check if an agent type is registered
        
        Args:
            agent_type: Agent type to check
            
        Returns:
            bool: True if registered, False otherwise
        """
        return agent_type in self._registrations
    
    def is_agent_active(self, agent_type: AgentType) -> bool:
        """
        Check if an agent type is active
        
        Args:
            agent_type: Agent type to check
            
        Returns:
            bool: True if active, False otherwise
        """
        if agent_type not in self._registrations:
            return False
        
        return self._registrations[agent_type].is_active


# Global registry instance
agent_registry = AgentRegistry()