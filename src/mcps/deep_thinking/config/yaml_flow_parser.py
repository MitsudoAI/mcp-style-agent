"""
YAML Flow Configuration Parser

This module provides functionality for parsing and validating YAML flow configurations.
It handles flow definitions, step dependencies, conditional logic, and loop control.
"""

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import yaml

from ..models.thinking_models import FlowStep, ThinkingFlow
from .exceptions import FlowConfigurationError

logger = logging.getLogger(__name__)


class YAMLFlowParser:
    """
    Parser for YAML flow configurations

    This class handles parsing, validation, and dependency management for flow configurations
    defined in YAML format.
    """

    def __init__(self):
        self.condition_pattern = re.compile(r"([a-zA-Z0-9_.]+)\s*([<>=!]+)\s*(.+)")
        self.reference_pattern = re.compile(r"([a-zA-Z0-9_]+)\.([a-zA-Z0-9_.]+)")

    def parse_file(self, file_path: Union[str, Path]) -> Dict[str, ThinkingFlow]:
        """
        Parse a YAML flow configuration file

        Args:
            file_path: Path to the YAML configuration file

        Returns:
            Dict[str, ThinkingFlow]: Dictionary of parsed flow configurations

        Raises:
            FlowConfigurationError: If parsing fails or configuration is invalid
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                raise FlowConfigurationError(
                    f"Flow configuration file not found: {file_path}"
                )

            with open(file_path, "r", encoding="utf-8") as f:
                yaml_content = yaml.safe_load(f)

            if not isinstance(yaml_content, dict):
                raise FlowConfigurationError(
                    f"Invalid YAML format in {file_path}, expected dictionary"
                )

            return self.parse_yaml(yaml_content)

        except yaml.YAMLError as e:
            raise FlowConfigurationError(f"Failed to parse YAML file {file_path}: {e}")
        except Exception as e:
            raise FlowConfigurationError(
                f"Error processing flow configuration file {file_path}: {e}"
            )

    def parse_yaml(self, yaml_content: Dict[str, Any]) -> Dict[str, ThinkingFlow]:
        """
        Parse YAML content into flow configurations

        Args:
            yaml_content: Dictionary containing YAML content

        Returns:
            Dict[str, ThinkingFlow]: Dictionary of parsed flow configurations

        Raises:
            FlowConfigurationError: If configuration is invalid
        """
        flows = {}

        # Skip metadata fields (keys starting with underscore)
        flow_keys = [k for k in yaml_content.keys() if not k.startswith("_")]

        for flow_name in flow_keys:
            flow_data = yaml_content[flow_name]
            flows[flow_name] = self._parse_flow(flow_name, flow_data)

        return flows

    def _parse_flow(self, flow_name: str, flow_data: Dict[str, Any]) -> ThinkingFlow:
        """
        Parse a single flow configuration

        Args:
            flow_name: Name of the flow
            flow_data: Flow configuration data

        Returns:
            ThinkingFlow: Parsed flow configuration

        Raises:
            FlowConfigurationError: If flow configuration is invalid
        """
        try:
            # Validate required fields
            if "steps" not in flow_data:
                raise FlowConfigurationError(
                    f"Flow '{flow_name}' missing required 'steps' field"
                )

            if not isinstance(flow_data["steps"], list):
                raise FlowConfigurationError(
                    f"Flow '{flow_name}' 'steps' must be a list"
                )

            # Parse steps
            steps = []
            step_ids = set()

            for i, step_data in enumerate(flow_data["steps"]):
                # Generate step ID if not provided
                step_id = (
                    step_data.get("name", f"{flow_name}_step_{i}")
                    .lower()
                    .replace(" ", "_")
                )

                # Ensure step ID uniqueness
                if step_id in step_ids:
                    step_id = f"{step_id}_{i}"
                step_ids.add(step_id)

                # Parse step
                step = self._parse_step(step_id, step_data)
                steps.append(step)

            # Create flow
            flow = ThinkingFlow(
                name=flow_name,
                description=flow_data.get("description"),
                version=flow_data.get("version", "1.0"),
                steps=steps,
                error_handling=flow_data.get("error_handling"),
                global_config=flow_data.get("global_config", {}),
                prerequisites=flow_data.get("prerequisites", []),
                expected_outputs=flow_data.get("expected_outputs", []),
                estimated_duration=flow_data.get("estimated_duration"),
            )

            # Validate dependencies
            self._validate_dependencies(flow)

            return flow

        except Exception as e:
            if isinstance(e, FlowConfigurationError):
                raise
            raise FlowConfigurationError(f"Failed to parse flow '{flow_name}': {e}")

    def _parse_step(self, step_id: str, step_data: Dict[str, Any]) -> FlowStep:
        """
        Parse a single flow step

        Args:
            step_id: ID for the step
            step_data: Step configuration data

        Returns:
            FlowStep: Parsed step configuration

        Raises:
            FlowConfigurationError: If step configuration is invalid
        """
        if "agent" not in step_data:
            raise FlowConfigurationError(
                f"Step '{step_id}' missing required 'agent' field"
            )

        # Extract dependencies from conditions and for_each
        dependencies = []

        # Check for_each dependencies
        for_each = step_data.get("for_each")
        if for_each:
            ref_match = self.reference_pattern.match(for_each)
            if ref_match:
                dependencies.append(ref_match.group(1))

        # Check condition dependencies
        conditions = step_data.get("conditions", {})
        if conditions:
            for condition_key in conditions:
                ref_match = self.reference_pattern.match(condition_key)
                if ref_match:
                    dependencies.append(ref_match.group(1))

        # Create step
        return FlowStep(
            step_id=step_id,
            agent_type=step_data["agent"],
            step_name=step_data.get("name", step_id),
            description=step_data.get("description"),
            config=step_data.get("config", {}),
            conditions=conditions,
            parallel=step_data.get("parallel", False),
            for_each=for_each,
            repeat_until=step_data.get("repeat_until"),
            timeout_seconds=step_data.get("timeout_seconds"),
            retry_config=step_data.get("retry_config"),
        )

    def _validate_dependencies(self, flow: ThinkingFlow) -> None:
        """
        Validate step dependencies and detect cycles

        Args:
            flow: Flow configuration to validate

        Raises:
            FlowConfigurationError: If dependencies are invalid or cycles are detected
        """
        # Build dependency graph
        dependency_graph = {}
        step_map = {step.step_id: step for step in flow.steps}

        for step in flow.steps:
            dependencies = set()

            # Check for_each dependencies
            if step.for_each:
                ref_match = self.reference_pattern.match(step.for_each)
                if ref_match:
                    dep_step_id = ref_match.group(1)
                    if dep_step_id not in step_map:
                        raise FlowConfigurationError(
                            f"Step '{step.step_id}' references unknown step '{dep_step_id}' in for_each"
                        )
                    dependencies.add(dep_step_id)

            # Check condition dependencies
            if step.conditions:
                for condition_key in step.conditions:
                    ref_match = self.reference_pattern.match(condition_key)
                    if ref_match:
                        dep_step_id = ref_match.group(1)
                        if dep_step_id not in step_map:
                            logger.warning(
                                f"Step '{step.step_id}' condition references unknown step '{dep_step_id}'"
                            )
                        else:
                            dependencies.add(dep_step_id)

            dependency_graph[step.step_id] = dependencies

        # Check for cycles
        visited = set()
        temp_visited = set()

        def has_cycle(node: str) -> bool:
            if node in temp_visited:
                return True
            if node in visited:
                return False

            temp_visited.add(node)

            for neighbor in dependency_graph.get(node, set()):
                if has_cycle(neighbor):
                    return True

            temp_visited.remove(node)
            visited.add(node)
            return False

        for step_id in dependency_graph:
            if step_id not in visited:
                if has_cycle(step_id):
                    raise FlowConfigurationError(
                        f"Cycle detected in flow '{flow.name}' dependencies"
                    )

    def evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """
        Evaluate a condition expression

        Args:
            condition: Condition expression (e.g., "score >= 0.8")
            context: Evaluation context with variables

        Returns:
            bool: Result of condition evaluation
        """
        match = self.condition_pattern.match(condition)
        if not match:
            logger.warning(f"Invalid condition format: {condition}")
            return False

        var_name, operator, value_str = match.groups()

        # Get variable value from context
        if "." in var_name:
            parts = var_name.split(".")
            current = context
            for part in parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    logger.warning(f"Variable not found in context: {var_name}")
                    return False
            var_value = current
        else:
            var_value = context.get(var_name)
            if var_value is None:
                logger.warning(f"Variable not found in context: {var_name}")
                return False

        # Convert value string to appropriate type
        try:
            if value_str.lower() == "true":
                value = True
            elif value_str.lower() == "false":
                value = False
            elif value_str.replace(".", "", 1).isdigit():
                value = float(value_str)
                if value.is_integer():
                    value = int(value)
            else:
                # Remove quotes if present
                value = value_str.strip("\"'")
        except Exception:
            value = value_str

        # Evaluate condition
        if operator == "==":
            return var_value == value
        elif operator == "!=":
            return var_value != value
        elif operator == ">":
            return var_value > value
        elif operator == ">=":
            return var_value >= value
        elif operator == "<":
            return var_value < value
        elif operator == "<=":
            return var_value <= value
        else:
            logger.warning(f"Unsupported operator: {operator}")
            return False

    def resolve_references(self, expression: str, context: Dict[str, Any]) -> Any:
        """
        Resolve variable references in an expression

        Args:
            expression: Expression with variable references
            context: Context with variable values

        Returns:
            Any: Resolved value
        """
        if not isinstance(expression, str):
            return expression

        # Check if it's a direct reference
        ref_match = self.reference_pattern.match(expression)
        if ref_match:
            step_id, field_path = ref_match.groups()

            if step_id not in context:
                logger.warning(f"Referenced step not found in context: {step_id}")
                return None

            step_context = context[step_id]

            # Navigate nested fields
            parts = field_path.split(".")
            current = step_context

            for part in parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                elif isinstance(current, list) and part.isdigit():
                    index = int(part)
                    if 0 <= index < len(current):
                        current = current[index]
                    else:
                        logger.warning(f"Index out of range: {part} in {field_path}")
                        return None
                else:
                    logger.warning(f"Field not found: {part} in {field_path}")
                    return None

            return current

        # If not a direct reference, look for embedded references
        def replace_ref(match):
            full_ref = match.group(0)
            step_id = match.group(1)
            field_path = match.group(2)

            if step_id not in context:
                logger.warning(f"Referenced step not found in context: {step_id}")
                return full_ref

            # Navigate nested fields
            current = context[step_id]
            parts = field_path.split(".")

            for part in parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                elif isinstance(current, list) and part.isdigit():
                    index = int(part)
                    if 0 <= index < len(current):
                        current = current[index]
                    else:
                        logger.warning(f"Index out of range: {part} in {field_path}")
                        return full_ref
                else:
                    logger.warning(f"Field not found: {part} in {field_path}")
                    return full_ref

            return str(current)

        # Replace all references in the expression
        return re.sub(r"(\w+)\.([a-zA-Z0-9_.]+)", replace_ref, expression)

    def get_step_dependencies(self, step: FlowStep) -> Set[str]:
        """
        Get all dependencies for a step

        Args:
            step: Flow step

        Returns:
            Set[str]: Set of step IDs this step depends on
        """
        dependencies = set()

        # Check for_each dependencies
        if step.for_each:
            ref_match = self.reference_pattern.match(step.for_each)
            if ref_match:
                dependencies.add(ref_match.group(1))

        # Check condition dependencies
        if step.conditions:
            for condition_key in step.conditions:
                ref_match = self.reference_pattern.match(condition_key)
                if ref_match:
                    dependencies.add(ref_match.group(1))

        return dependencies

    def topological_sort(self, flow: ThinkingFlow) -> List[str]:
        """
        Sort steps in topological order based on dependencies

        Args:
            flow: Flow configuration

        Returns:
            List[str]: List of step IDs in execution order

        Raises:
            FlowConfigurationError: If cycle is detected
        """
        # Build dependency graph
        graph = {}
        for step in flow.steps:
            graph[step.step_id] = self.get_step_dependencies(step)

        # Perform topological sort
        result = []
        visited = set()
        temp_visited = set()

        def visit(node: str) -> None:
            if node in temp_visited:
                raise FlowConfigurationError(
                    f"Cycle detected in flow '{flow.name}' dependencies"
                )
            if node in visited:
                return

            temp_visited.add(node)

            for neighbor in graph.get(node, set()):
                visit(neighbor)

            temp_visited.remove(node)
            visited.add(node)
            result.append(node)

        for step in flow.steps:
            if step.step_id not in visited:
                visit(step.step_id)

        return result


# Global instance
yaml_flow_parser = YAMLFlowParser()
