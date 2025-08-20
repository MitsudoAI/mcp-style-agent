"""
Configuration validation system with comprehensive checks
"""

import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from pydantic import BaseModel, Field, ValidationError, validator

from .exceptions import ConfigurationError

logger = logging.getLogger(__name__)


class AgentConfigSchema(BaseModel):
    """Schema for agent configuration"""

    agent_type: Optional[str] = None
    enabled: bool = True
    max_retries: int = Field(ge=0, le=10, default=3)
    timeout_seconds: int = Field(ge=1, le=3600, default=300)
    temperature: float = Field(ge=0.0, le=2.0, default=0.7)
    quality_threshold: float = Field(ge=0.0, le=1.0, default=0.8)

    class Config:
        extra = "allow"


class FlowStepSchema(BaseModel):
    """Schema for flow step configuration"""

    agent: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: Optional[str] = None
    config: Dict[str, Any] = Field(default_factory=dict)
    parallel: bool = False
    for_each: Optional[str] = None
    repeat_until: Optional[str] = None
    conditions: Optional[Dict[str, str]] = None
    timeout_seconds: Optional[int] = Field(ge=1, le=3600, default=None)

    @validator("timeout_seconds")
    def validate_timeout(cls, v):
        if v is not None and v <= 0:
            raise ValueError("timeout_seconds must be positive")
        return v

    @validator("for_each")
    def validate_for_each(cls, v):
        if v is not None and not re.match(
            r"^[a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*$", v
        ):
            raise ValueError('for_each must be in format "agent.property"')
        return v

    class Config:
        extra = "allow"


class FlowSchema(BaseModel):
    """Schema for flow configuration"""

    description: str = Field(min_length=1)
    version: str = Field(default="1.0")
    estimated_duration: Optional[int] = Field(ge=1, default=None)
    steps: List[FlowStepSchema] = Field(min_items=1)
    error_handling: Optional[Dict[str, Any]] = None
    global_config: Optional[Dict[str, Any]] = None

    @validator("steps")
    def validate_steps(cls, v):
        if not v:
            raise ValueError("Flow must have at least one step")

        # Check for duplicate step names
        step_names = [step.name for step in v]
        if len(step_names) != len(set(step_names)):
            raise ValueError("Flow steps must have unique names")

        return v

    class Config:
        extra = "allow"


class SystemConfigSchema(BaseModel):
    """Schema for system configuration"""

    system: Dict[str, Any] = Field(default_factory=dict)
    agents: Dict[str, Any] = Field(default_factory=dict)
    search: Dict[str, Any] = Field(default_factory=dict)
    database: Dict[str, Any] = Field(default_factory=dict)
    cache: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        extra = "allow"


class ConfigValidator:
    """
    Comprehensive configuration validator
    """

    def __init__(self):
        self.schemas = {
            "system": SystemConfigSchema,
            "flows": Dict[str, FlowSchema],
            "agent": AgentConfigSchema,
            "flow_step": FlowStepSchema,
        }

        self.required_agent_types = {
            "decomposer",
            "evidence_seeker",
            "debate_orchestrator",
            "critic",
            "bias_buster",
            "innovator",
            "reflector",
        }

        self.valid_log_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}

    def validate_system_config(
        self, config_data: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Validate system configuration

        Args:
            config_data: System configuration data

        Returns:
            Tuple[bool, List[str]]: (is_valid, error_messages)
        """
        errors = []

        try:
            # Validate using Pydantic schema
            SystemConfigSchema(**config_data)
        except ValidationError as e:
            for error in e.errors():
                field = ".".join(str(loc) for loc in error["loc"])
                errors.append(f"System config {field}: {error['msg']}")

        # Additional custom validations
        system_config = config_data.get("system", {})

        # Validate log level
        log_level = system_config.get("log_level", "INFO")
        if log_level not in self.valid_log_levels:
            errors.append(
                f"Invalid log_level: {log_level}. Must be one of {self.valid_log_levels}"
            )

        # Validate numeric ranges
        max_concurrent = system_config.get("max_concurrent_agents", 10)
        if (
            not isinstance(max_concurrent, int)
            or max_concurrent < 1
            or max_concurrent > 100
        ):
            errors.append("max_concurrent_agents must be between 1 and 100")

        timeout = system_config.get("default_timeout", 300)
        if not isinstance(timeout, int) or timeout < 1 or timeout > 3600:
            errors.append("default_timeout must be between 1 and 3600 seconds")

        # Validate agent configurations
        agents_config = config_data.get("agents", {})
        agent_errors = self._validate_agents_config(agents_config)
        errors.extend(agent_errors)

        # Validate database configuration
        db_config = config_data.get("database", {})
        db_errors = self._validate_database_config(db_config)
        errors.extend(db_errors)

        return len(errors) == 0, errors

    def validate_flows_config(
        self, config_data: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Validate flows configuration

        Args:
            config_data: Flows configuration data

        Returns:
            Tuple[bool, List[str]]: (is_valid, error_messages)
        """
        errors = []

        if not isinstance(config_data, dict):
            errors.append("Flows configuration must be a dictionary")
            return False, errors

        if not config_data:
            errors.append("Flows configuration cannot be empty")
            return False, errors

        # Validate each flow
        for flow_name, flow_config in config_data.items():
            if flow_name.startswith("_"):  # Skip metadata fields
                continue

            flow_errors = self._validate_single_flow(flow_name, flow_config)
            errors.extend(flow_errors)

        return len(errors) == 0, errors

    def _validate_single_flow(
        self, flow_name: str, flow_config: Dict[str, Any]
    ) -> List[str]:
        """
        Validate a single flow configuration

        Args:
            flow_name: Name of the flow
            flow_config: Flow configuration data

        Returns:
            List[str]: List of error messages
        """
        errors = []

        try:
            # Validate using Pydantic schema
            FlowSchema(**flow_config)
        except ValidationError as e:
            for error in e.errors():
                field = ".".join(str(loc) for loc in error["loc"])
                errors.append(f"Flow '{flow_name}' {field}: {error['msg']}")

        # Additional custom validations
        steps = flow_config.get("steps", [])
        if not steps:
            errors.append(f"Flow '{flow_name}' must have at least one step")
            return errors

        # Validate step dependencies and references
        step_errors = self._validate_flow_steps(flow_name, steps)
        errors.extend(step_errors)

        # Validate error handling configuration
        error_handling = flow_config.get("error_handling", {})
        if error_handling:
            eh_errors = self._validate_error_handling(flow_name, error_handling)
            errors.extend(eh_errors)

        return errors

    def _validate_flow_steps(
        self, flow_name: str, steps: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Validate flow steps

        Args:
            flow_name: Name of the flow
            steps: List of step configurations

        Returns:
            List[str]: List of error messages
        """
        errors = []
        step_names = set()
        agent_outputs = {}  # Track what each agent produces

        for i, step in enumerate(steps):
            step_name = step.get("name", f"step_{i}")
            agent_type = step.get("agent")

            # Check for duplicate step names
            if step_name in step_names:
                errors.append(
                    f"Flow '{flow_name}' has duplicate step name: {step_name}"
                )
            step_names.add(step_name)

            # Validate agent type
            if not agent_type:
                errors.append(
                    f"Flow '{flow_name}' step '{step_name}' missing agent type"
                )
                continue

            if agent_type not in self.required_agent_types:
                errors.append(
                    f"Flow '{flow_name}' step '{step_name}' uses unknown agent: {agent_type}"
                )

            # Track agent outputs for dependency validation
            agent_outputs[agent_type] = step_name

            # Validate for_each references
            for_each = step.get("for_each")
            if for_each:
                ref_errors = self._validate_reference(
                    flow_name, step_name, for_each, agent_outputs
                )
                errors.extend(ref_errors)

            # Validate condition references
            conditions = step.get("conditions", {})
            for condition_key, condition_value in conditions.items():
                if "." in condition_key:  # Reference to another agent's output
                    ref_errors = self._validate_reference(
                        flow_name, step_name, condition_key, agent_outputs
                    )
                    errors.extend(ref_errors)

            # Validate repeat_until conditions
            repeat_until = step.get("repeat_until")
            if repeat_until:
                # Check if condition references valid variables
                if "." in repeat_until:
                    # Extract variable references
                    import re

                    refs = re.findall(
                        r"([a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*)",
                        repeat_until,
                    )
                    for ref in refs:
                        ref_errors = self._validate_reference(
                            flow_name, step_name, ref, agent_outputs
                        )
                        errors.extend(ref_errors)

            # Validate step configuration
            step_config = step.get("config", {})
            config_errors = self._validate_step_config(
                flow_name, step_name, agent_type, step_config
            )
            errors.extend(config_errors)

        return errors

    def _validate_reference(
        self,
        flow_name: str,
        step_name: str,
        reference: str,
        agent_outputs: Dict[str, str],
    ) -> List[str]:
        """
        Validate a reference to another agent's output

        Args:
            flow_name: Name of the flow
            step_name: Name of the current step
            reference: Reference string (e.g., "decomposer.sub_questions")
            agent_outputs: Dictionary of agent types to step names

        Returns:
            List[str]: List of error messages
        """
        errors = []

        if "." not in reference:
            errors.append(
                f"Flow '{flow_name}' step '{step_name}' invalid reference format: {reference}"
            )
            return errors

        agent_type, property_name = reference.split(".", 1)

        if agent_type not in agent_outputs:
            errors.append(
                f"Flow '{flow_name}' step '{step_name}' references undefined agent: {agent_type}"
            )

        # Validate property name format
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", property_name):
            errors.append(
                f"Flow '{flow_name}' step '{step_name}' invalid property name: {property_name}"
            )

        return errors

    def _validate_step_config(
        self, flow_name: str, step_name: str, agent_type: str, config: Dict[str, Any]
    ) -> List[str]:
        """
        Validate step-specific configuration

        Args:
            flow_name: Name of the flow
            step_name: Name of the step
            agent_type: Type of agent
            config: Step configuration

        Returns:
            List[str]: List of error messages
        """
        errors = []

        # Agent-specific validation
        if agent_type == "decomposer":
            max_questions = config.get("max_sub_questions")
            if max_questions is not None:
                if (
                    not isinstance(max_questions, int)
                    or max_questions < 1
                    or max_questions > 10
                ):
                    errors.append(
                        f"Flow '{flow_name}' step '{step_name}': max_sub_questions must be 1-10"
                    )

        elif agent_type == "evidence_seeker":
            min_sources = config.get("min_sources")
            if min_sources is not None:
                if (
                    not isinstance(min_sources, int)
                    or min_sources < 1
                    or min_sources > 20
                ):
                    errors.append(
                        f"Flow '{flow_name}' step '{step_name}': min_sources must be 1-20"
                    )

            credibility_threshold = config.get("credibility_threshold")
            if credibility_threshold is not None:
                if (
                    not isinstance(credibility_threshold, (int, float))
                    or not 0 <= credibility_threshold <= 1
                ):
                    errors.append(
                        f"Flow '{flow_name}' step '{step_name}': credibility_threshold must be 0-1"
                    )

        elif agent_type == "debate_orchestrator":
            positions = config.get("positions", [])
            if positions and not isinstance(positions, list):
                errors.append(
                    f"Flow '{flow_name}' step '{step_name}': positions must be a list"
                )
            elif positions and len(positions) < 2:
                errors.append(
                    f"Flow '{flow_name}' step '{step_name}': must have at least 2 debate positions"
                )

            max_rounds = config.get("max_rounds")
            if max_rounds is not None:
                if not isinstance(max_rounds, int) or max_rounds < 1 or max_rounds > 10:
                    errors.append(
                        f"Flow '{flow_name}' step '{step_name}': max_rounds must be 1-10"
                    )

        elif agent_type == "critic":
            standards = config.get("standards")
            valid_standards = {"paul_elder_basic", "paul_elder_full", "formal_logic"}
            if standards and standards not in valid_standards:
                errors.append(
                    f"Flow '{flow_name}' step '{step_name}': invalid standards '{standards}'"
                )

        return errors

    def _validate_agents_config(self, agents_config: Dict[str, Any]) -> List[str]:
        """
        Validate agents configuration

        Args:
            agents_config: Agents configuration data

        Returns:
            List[str]: List of error messages
        """
        errors = []

        # Validate default values
        default_temp = agents_config.get("default_temperature", 0.7)
        if not isinstance(default_temp, (int, float)) or not 0 <= default_temp <= 2:
            errors.append("default_temperature must be between 0 and 2")

        quality_threshold = agents_config.get("quality_threshold", 0.8)
        if (
            not isinstance(quality_threshold, (int, float))
            or not 0 <= quality_threshold <= 1
        ):
            errors.append("quality_threshold must be between 0 and 1")

        max_retries = agents_config.get("default_max_retries", 3)
        if not isinstance(max_retries, int) or max_retries < 0 or max_retries > 10:
            errors.append("default_max_retries must be between 0 and 10")

        # Validate agent-specific configurations
        for agent_type in self.required_agent_types:
            if agent_type in agents_config:
                agent_config = agents_config[agent_type]
                if not isinstance(agent_config, dict):
                    errors.append(
                        f"Agent '{agent_type}' configuration must be a dictionary"
                    )
                    continue

                # Validate agent-specific settings
                agent_errors = self._validate_agent_specific_config(
                    agent_type, agent_config
                )
                errors.extend(agent_errors)

        return errors

    def _validate_agent_specific_config(
        self, agent_type: str, config: Dict[str, Any]
    ) -> List[str]:
        """
        Validate agent-specific configuration

        Args:
            agent_type: Type of agent
            config: Agent configuration

        Returns:
            List[str]: List of error messages
        """
        errors = []

        if agent_type == "critic":
            standards = config.get("paul_elder_standards", [])
            if standards and not isinstance(standards, list):
                errors.append(
                    f"Agent '{agent_type}': paul_elder_standards must be a list"
                )

            valid_standards = {
                "accuracy",
                "precision",
                "relevance",
                "logic",
                "breadth",
                "depth",
                "significance",
                "fairness",
                "clarity",
            }

            if standards:
                for standard in standards:
                    if standard not in valid_standards:
                        errors.append(
                            f"Agent '{agent_type}': invalid Paul-Elder standard '{standard}'"
                        )

        elif agent_type == "bias_buster":
            bias_types = config.get("bias_types", [])
            if bias_types and not isinstance(bias_types, list):
                errors.append(f"Agent '{agent_type}': bias_types must be a list")

            valid_bias_types = {
                "confirmation_bias",
                "anchoring",
                "availability_heuristic",
                "representativeness",
                "overconfidence",
                "hindsight_bias",
            }

            if bias_types:
                for bias_type in bias_types:
                    if bias_type not in valid_bias_types:
                        errors.append(
                            f"Agent '{agent_type}': invalid bias type '{bias_type}'"
                        )

        elif agent_type == "innovator":
            methods = config.get("methods", [])
            if methods and not isinstance(methods, list):
                errors.append(f"Agent '{agent_type}': methods must be a list")

            valid_methods = {
                "SCAMPER",
                "TRIZ",
                "lateral_thinking",
                "analogical_reasoning",
            }

            if methods:
                for method in methods:
                    if method not in valid_methods:
                        errors.append(
                            f"Agent '{agent_type}': invalid innovation method '{method}'"
                        )

        return errors

    def _validate_database_config(self, db_config: Dict[str, Any]) -> List[str]:
        """
        Validate database configuration

        Args:
            db_config: Database configuration

        Returns:
            List[str]: List of error messages
        """
        errors = []

        db_path = db_config.get("path")
        if db_path and not isinstance(db_path, str):
            errors.append("Database path must be a string")

        backup_interval = db_config.get("backup_interval")
        if backup_interval is not None:
            if not isinstance(backup_interval, int) or backup_interval < 60:
                errors.append("backup_interval must be at least 60 seconds")

        return errors

    def _validate_error_handling(
        self, flow_name: str, error_config: Dict[str, Any]
    ) -> List[str]:
        """
        Validate error handling configuration

        Args:
            flow_name: Name of the flow
            error_config: Error handling configuration

        Returns:
            List[str]: List of error messages
        """
        errors = []

        retry_strategy = error_config.get("retry_strategy")
        valid_strategies = {
            "exponential_backoff",
            "linear_backoff",
            "fixed_delay",
            "none",
        }

        if retry_strategy and retry_strategy not in valid_strategies:
            errors.append(
                f"Flow '{flow_name}': invalid retry_strategy '{retry_strategy}'"
            )

        max_retries = error_config.get("max_retries")
        if max_retries is not None:
            if not isinstance(max_retries, int) or max_retries < 0 or max_retries > 10:
                errors.append(
                    f"Flow '{flow_name}': max_retries must be between 0 and 10"
                )

        fallback_agents = error_config.get("fallback_agents", [])
        if fallback_agents and not isinstance(fallback_agents, list):
            errors.append(f"Flow '{flow_name}': fallback_agents must be a list")

        return errors

    def validate_config(
        self, config_name: str, config_data: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Validate configuration data

        Args:
            config_name: Name of the configuration
            config_data: Configuration data to validate

        Returns:
            Tuple[bool, List[str]]: (is_valid, error_messages)
        """
        if config_name == "system":
            return self.validate_system_config(config_data)
        elif config_name == "flows":
            return self.validate_flows_config(config_data)
        else:
            logger.warning(f"No validation rules defined for config: {config_name}")
            return True, []

    def get_validation_summary(
        self, config_name: str, config_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get comprehensive validation summary

        Args:
            config_name: Name of the configuration
            config_data: Configuration data to validate

        Returns:
            Dict[str, Any]: Validation summary
        """
        is_valid, errors = self.validate_config(config_name, config_data)

        summary = {
            "config_name": config_name,
            "is_valid": is_valid,
            "error_count": len(errors),
            "errors": errors,
            "validation_timestamp": self._get_timestamp(),
        }

        if config_name == "flows":
            summary["flow_count"] = len(
                [k for k in config_data.keys() if not k.startswith("_")]
            )
            summary["flows"] = list(config_data.keys())

        return summary

    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime

        return datetime.now().isoformat()


# Global validator instance
config_validator = ConfigValidator()
