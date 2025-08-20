"""
Flow configuration management with YAML support
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

from ..models.thinking_models import FlowStep, ThinkingFlow
from .config_manager import ConfigManager
from .exceptions import FlowConfigurationError
from .yaml_flow_parser import YAMLFlowParser

logger = logging.getLogger(__name__)


class FlowConfigManager:
    """
    Manager for thinking flow configurations
    """

    def __init__(self, config_manager: Optional[ConfigManager] = None):
        self.config_manager = config_manager
        self.flows: Dict[str, ThinkingFlow] = {}
        self._lock = asyncio.Lock()
        self.yaml_parser = YAMLFlowParser()

        # Register for config reload notifications if config_manager is provided
        if self.config_manager:
            self.config_manager.add_reload_callback(self._on_config_reload)

    async def initialize(self) -> None:
        """Initialize flow configuration manager"""
        await self._load_all_flows()

    async def _load_all_flows(self) -> None:
        """Load all flow configurations"""
        if not self.config_manager:
            logger.warning("No config manager available, skipping flow loading")
            return

        # Load flows from config manager
        flows_config = self.config_manager.get_config("flows", {})

        # Parse flows from config
        for flow_name, flow_data in flows_config.items():
            if flow_name.startswith("_"):  # Skip metadata fields
                continue

            try:
                await self._load_flow(flow_name, flow_data)
            except Exception as e:
                logger.error(f"Failed to load flow '{flow_name}': {e}")

        # Load flows from YAML files in config directory
        if self.config_manager and hasattr(self.config_manager, "config_dir"):
            config_dir = Path(self.config_manager.config_dir)
            flows_dir = config_dir / "flows"

            if flows_dir.exists() and flows_dir.is_dir():
                for file_path in flows_dir.glob("*.yaml"):
                    try:
                        await self._load_flow_file(file_path)
                    except Exception as e:
                        logger.error(f"Failed to load flow file '{file_path}': {e}")

    async def _load_flow_file(self, file_path: Path) -> None:
        """Load flows from a YAML file"""
        try:
            parsed_flows = self.yaml_parser.parse_file(file_path)

            for flow_name, flow in parsed_flows.items():
                self.flows[flow_name] = flow
                logger.info(f"Loaded flow configuration from file: {flow_name}")

        except Exception as e:
            logger.error(f"Failed to load flows from file {file_path}: {e}")
            raise

    async def _load_flow(self, flow_name: str, flow_data: Dict[str, Any]) -> None:
        """Load a single flow configuration"""
        try:
            # Use YAML parser to parse the flow
            flow_dict = {flow_name: flow_data}
            parsed_flows = self.yaml_parser.parse_yaml(flow_dict)

            if flow_name in parsed_flows:
                self.flows[flow_name] = parsed_flows[flow_name]
                logger.info(f"Loaded flow configuration: {flow_name}")
            else:
                raise FlowConfigurationError(f"Failed to parse flow '{flow_name}'")

        except Exception as e:
            raise FlowConfigurationError(f"Failed to parse flow '{flow_name}': {e}")

    def _on_config_reload(self, config_name: str, config_data: Dict[str, Any]) -> None:
        """Handle configuration reload events"""
        if config_name == "flows":
            asyncio.create_task(self._reload_flows())

    async def _reload_flows(self) -> None:
        """Reload all flow configurations"""
        async with self._lock:
            old_flows = self.flows.copy()
            self.flows.clear()

            try:
                await self._load_all_flows()
                logger.info("Successfully reloaded all flow configurations")
            except Exception as e:
                # Restore old flows on error
                self.flows = old_flows
                logger.error(
                    f"Failed to reload flows, restored previous configuration: {e}"
                )

    def get_flow(self, flow_name: str) -> Optional[ThinkingFlow]:
        """
        Get a flow configuration by name

        Args:
            flow_name: Name of the flow

        Returns:
            ThinkingFlow: Flow configuration or None if not found
        """
        return self.flows.get(flow_name)

    def get_all_flows(self) -> Dict[str, ThinkingFlow]:
        """Get all loaded flow configurations"""
        return self.flows.copy()

    def get_flow_names(self) -> List[str]:
        """Get list of available flow names"""
        return list(self.flows.keys())

    def validate_flow(self, flow_name: str) -> bool:
        """
        Validate a flow configuration

        Args:
            flow_name: Name of flow to validate

        Returns:
            bool: True if valid

        Raises:
            FlowConfigurationError: If validation fails
        """
        flow = self.get_flow(flow_name)
        if not flow:
            raise FlowConfigurationError(f"Flow '{flow_name}' not found")

        # Validate flow structure
        if not flow.steps:
            raise FlowConfigurationError(f"Flow '{flow_name}' has no steps")

        # Validate each step
        for step in flow.steps:
            self._validate_flow_step(step, flow_name)

        # Validate step dependencies
        self._validate_step_dependencies(flow)

        return True

    def _validate_flow_step(self, step: FlowStep, flow_name: str) -> None:
        """Validate a single flow step"""
        # Check required fields
        if not step.agent_type:
            raise FlowConfigurationError(
                f"Step '{step.step_id}' in flow '{flow_name}' missing agent_type"
            )

        # Validate conditional logic
        if step.repeat_until and step.for_each:
            raise FlowConfigurationError(
                f"Step '{step.step_id}' cannot have both repeat_until and for_each"
            )

        # Validate timeout
        if step.timeout_seconds and step.timeout_seconds <= 0:
            raise FlowConfigurationError(
                f"Step '{step.step_id}' timeout must be positive"
            )

    def _validate_step_dependencies(self, flow: ThinkingFlow) -> None:
        """Validate step dependencies and references"""
        # Use the YAML parser's dependency validation
        try:
            self.yaml_parser._validate_dependencies(flow)
        except FlowConfigurationError as e:
            raise e

    async def create_flow_from_template(
        self, flow_name: str, template_name: str, parameters: Dict[str, Any]
    ) -> ThinkingFlow:
        """
        Create a flow from a template with parameters

        Args:
            flow_name: Name for the new flow
            template_name: Name of the template flow
            parameters: Parameters to substitute in template

        Returns:
            ThinkingFlow: Created flow

        Raises:
            FlowConfigurationError: If template not found or creation fails
        """
        template_flow = self.get_flow(template_name)
        if not template_flow:
            raise FlowConfigurationError(f"Template flow '{template_name}' not found")

        try:
            # Create a copy of the template
            flow_dict = template_flow.model_dump()

            # Substitute parameters
            flow_dict = self._substitute_parameters(flow_dict, parameters)

            # Update name
            flow_dict["name"] = flow_name

            # Create new flow
            new_flow = ThinkingFlow(**flow_dict)

            # Store the new flow
            async with self._lock:
                self.flows[flow_name] = new_flow

            logger.info(f"Created flow '{flow_name}' from template '{template_name}'")
            return new_flow

        except Exception as e:
            raise FlowConfigurationError(f"Failed to create flow from template: {e}")

    def _substitute_parameters(self, data: Any, parameters: Dict[str, Any]) -> Any:
        """Recursively substitute parameters in data structure"""
        if isinstance(data, dict):
            return {
                key: self._substitute_parameters(value, parameters)
                for key, value in data.items()
            }
        elif isinstance(data, list):
            return [self._substitute_parameters(item, parameters) for item in data]
        elif isinstance(data, str):
            # Simple parameter substitution
            for param_name, param_value in parameters.items():
                placeholder = f"${{{param_name}}}"
                if placeholder in data:
                    data = data.replace(placeholder, str(param_value))
            return data
        else:
            return data

    def evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """
        Evaluate a condition expression using the YAML parser

        Args:
            condition: Condition expression (e.g., "score >= 0.8")
            context: Evaluation context with variables

        Returns:
            bool: Result of condition evaluation
        """
        return self.yaml_parser.evaluate_condition(condition, context)

    def resolve_references(self, expression: str, context: Dict[str, Any]) -> Any:
        """
        Resolve variable references in an expression using the YAML parser

        Args:
            expression: Expression with variable references
            context: Context with variable values

        Returns:
            Any: Resolved value
        """
        return self.yaml_parser.resolve_references(expression, context)

    async def save_flow(self, flow_name: str) -> None:
        """
        Save a flow configuration to file

        Args:
            flow_name: Name of flow to save

        Raises:
            FlowConfigurationError: If flow not found or save fails
        """
        if not self.config_manager:
            raise FlowConfigurationError("No config manager available for saving flows")

        flow = self.get_flow(flow_name)
        if not flow:
            raise FlowConfigurationError(f"Flow '{flow_name}' not found")

        try:
            # Get current flows config
            flows_config = self.config_manager.get_config("flows", {})

            # Update with this flow
            flows_config[flow_name] = flow.model_dump(exclude={"name"})

            # Save to config manager
            self.config_manager.set_config("flows", flows_config)
            await self.config_manager.save_config("flows", "yaml")

            logger.info(f"Saved flow configuration: {flow_name}")

        except Exception as e:
            raise FlowConfigurationError(f"Failed to save flow '{flow_name}': {e}")

    def get_default_flow_config(self) -> Dict[str, Any]:
        """Get default flow configuration template"""
        return {
            "comprehensive_analysis": {
                "description": "Comprehensive deep thinking analysis flow",
                "version": "1.0",
                "steps": [
                    {
                        "agent": "decomposer",
                        "name": "Problem Decomposition",
                        "config": {
                            "complexity_level": "adaptive",
                            "max_sub_questions": 5,
                        },
                    },
                    {
                        "agent": "evidence_seeker",
                        "name": "Evidence Collection",
                        "parallel": True,
                        "for_each": "decomposer.sub_questions",
                        "config": {"source_diversity": True, "min_sources": 5},
                    },
                    {
                        "agent": "debate_orchestrator",
                        "name": "Multi-perspective Debate",
                        "config": {
                            "positions": ["pro", "con", "neutral"],
                            "max_rounds": 3,
                            "sparse_communication": True,
                        },
                    },
                    {
                        "agent": "critic",
                        "name": "Critical Evaluation",
                        "repeat_until": "overall_score >= 0.8",
                        "config": {"standards": "paul_elder_full"},
                    },
                    {
                        "agent": "bias_buster",
                        "name": "Bias Detection",
                        "config": {"comprehensive_check": True},
                    },
                    {
                        "agent": "innovator",
                        "name": "Innovation Generation",
                        "conditions": {"critic.overall_score": ">=0.8"},
                        "config": {"methods": ["SCAMPER", "TRIZ"]},
                    },
                    {
                        "agent": "reflector",
                        "name": "Metacognitive Reflection",
                        "config": {"reflection_depth": "deep"},
                    },
                ],
                "error_handling": {
                    "retry_strategy": "exponential_backoff",
                    "fallback_agents": ["simplified_critic", "basic_reflector"],
                    "max_retries": 3,
                },
                "global_config": {
                    "enable_caching": True,
                    "parallel_execution": True,
                    "quality_gates": True,
                },
            }
        }


# Global flow configuration manager
flow_config_manager = FlowConfigManager(None)  # Will be initialized with config_manager
