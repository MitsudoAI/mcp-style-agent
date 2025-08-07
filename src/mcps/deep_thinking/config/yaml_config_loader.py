"""
YAML configuration file loader with validation and hot reload support
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml
from pydantic import BaseModel, ValidationError

from .exceptions import ConfigurationError

logger = logging.getLogger(__name__)


class ConfigSchema(BaseModel):
    """Base schema for configuration validation"""
    
    class Config:
        extra = "allow"  # Allow additional fields


class SystemConfigSchema(ConfigSchema):
    """Schema for system configuration"""
    
    system: Dict[str, Any] = {}
    agents: Dict[str, Any] = {}
    search: Dict[str, Any] = {}
    database: Dict[str, Any] = {}
    cache: Dict[str, Any] = {}


class FlowConfigSchema(ConfigSchema):
    """Schema for flow configuration"""
    
    # Flow configurations are dynamic, so we allow any structure
    pass


class YAMLConfigLoader:
    """
    YAML configuration file loader with validation and hot reload support
    """
    
    def __init__(self, config_dir: Optional[Union[str, Path]] = None):
        """
        Initialize YAML config loader
        
        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = Path(config_dir) if config_dir else Path("config")
        self.schemas = {
            "system": SystemConfigSchema,
            "flows": FlowConfigSchema,
        }
        self.default_configs = self._get_default_configs()
    
    def _get_default_configs(self) -> Dict[str, Dict[str, Any]]:
        """Get default configuration values"""
        return {
            "system": {
                "system": {
                    "log_level": "INFO",
                    "max_concurrent_agents": 10,
                    "default_timeout": 300,
                    "enable_caching": True,
                    "cache_ttl": 3600,
                    "debug_mode": False,
                },
                "agents": {
                    "default_temperature": 0.7,
                    "default_max_retries": 3,
                    "quality_threshold": 0.8,
                    "enable_parallel_execution": True,
                },
                "search": {
                    "max_results_per_query": 10,
                    "search_timeout": 30,
                    "enable_source_diversity": True,
                },
                "database": {
                    "path": "data/thinking_sessions.db",
                    "enable_encryption": True,
                    "backup_interval": 3600,
                },
                "cache": {
                    "evidence_ttl": 3600,
                    "evaluation_cache_size": 500,
                    "debate_cache_size": 100,
                },
            },
            "flows": {
                "comprehensive_analysis": {
                    "description": "Complete deep thinking analysis with all agents",
                    "version": "1.0",
                    "estimated_duration": 15,
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
                            "agent": "reflector",
                            "name": "Metacognitive Reflection",
                            "config": {
                                "reflection_depth": "deep",
                            },
                        },
                    ],
                    "global_config": {
                        "enable_caching": True,
                        "parallel_execution": True,
                        "quality_gates": True,
                    },
                }
            },
        }
    
    def load_config_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Load and parse a YAML configuration file
        
        Args:
            file_path: Path to the YAML file
            
        Returns:
            Dict[str, Any]: Parsed configuration data
            
        Raises:
            ConfigurationError: If file cannot be loaded or parsed
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise ConfigurationError(f"Configuration file not found: {file_path}")
        
        if not file_path.is_file():
            raise ConfigurationError(f"Path is not a file: {file_path}")
        
        if file_path.suffix not in [".yaml", ".yml"]:
            raise ConfigurationError(f"Unsupported file format: {file_path.suffix}")
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f)
            
            if config_data is None:
                config_data = {}
            
            if not isinstance(config_data, dict):
                raise ConfigurationError(
                    f"Configuration file must contain a YAML dictionary: {file_path}"
                )
            
            logger.info(f"Successfully loaded configuration file: {file_path}")
            return config_data
            
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Failed to parse YAML file {file_path}: {e}")
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration file {file_path}: {e}")
    
    def load_all_configs(self) -> Dict[str, Dict[str, Any]]:
        """
        Load all configuration files from the config directory
        
        Returns:
            Dict[str, Dict[str, Any]]: All loaded configurations
        """
        configs = {}
        
        if not self.config_dir.exists():
            logger.warning(f"Config directory does not exist: {self.config_dir}")
            return self.default_configs.copy()
        
        # Load main config files
        for config_name in ["system", "flows"]:
            config_file = self.config_dir / f"{config_name}.yaml"
            
            if config_file.exists():
                try:
                    config_data = self.load_config_file(config_file)
                    configs[config_name] = config_data
                except ConfigurationError as e:
                    logger.error(f"Failed to load {config_name} config: {e}")
                    # Use default config as fallback
                    configs[config_name] = self.default_configs.get(config_name, {})
            else:
                logger.info(f"Config file not found, using defaults: {config_file}")
                configs[config_name] = self.default_configs.get(config_name, {})
        
        # Load additional flow configs from flows directory
        flows_dir = self.config_dir / "flows"
        if flows_dir.exists() and flows_dir.is_dir():
            for flow_file in flows_dir.glob("*.yaml"):
                try:
                    flow_config = self.load_config_file(flow_file)
                    # Merge with main flows config
                    if "flows" not in configs:
                        configs["flows"] = {}
                    configs["flows"].update(flow_config)
                except ConfigurationError as e:
                    logger.error(f"Failed to load flow config {flow_file}: {e}")
        
        return configs
    
    def validate_config(self, config_name: str, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate configuration data against schema
        
        Args:
            config_name: Name of the configuration
            config_data: Configuration data to validate
            
        Returns:
            Dict[str, Any]: Validated configuration data
            
        Raises:
            ConfigurationError: If validation fails
        """
        if config_name not in self.schemas:
            logger.warning(f"No schema defined for config: {config_name}")
            return config_data
        
        schema_class = self.schemas[config_name]
        
        try:
            # Validate using Pydantic schema
            validated_config = schema_class(**config_data)
            return validated_config.model_dump()
            
        except ValidationError as e:
            error_details = []
            for error in e.errors():
                field = ".".join(str(loc) for loc in error["loc"])
                message = error["msg"]
                error_details.append(f"{field}: {message}")
            
            raise ConfigurationError(
                f"Configuration validation failed for '{config_name}': {'; '.join(error_details)}"
            )
    
    def merge_with_defaults(self, config_name: str, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge configuration data with default values
        
        Args:
            config_name: Name of the configuration
            config_data: Configuration data to merge
            
        Returns:
            Dict[str, Any]: Merged configuration data
        """
        default_config = self.default_configs.get(config_name, {})
        
        if not default_config:
            return config_data
        
        # Deep merge with defaults
        merged_config = self._deep_merge(default_config.copy(), config_data)
        return merged_config
    
    def _deep_merge(self, base_dict: Dict[str, Any], update_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively merge two dictionaries
        
        Args:
            base_dict: Base dictionary
            update_dict: Dictionary with updates
            
        Returns:
            Dict[str, Any]: Merged dictionary
        """
        for key, value in update_dict.items():
            if (
                key in base_dict
                and isinstance(base_dict[key], dict)
                and isinstance(value, dict)
            ):
                base_dict[key] = self._deep_merge(base_dict[key], value)
            else:
                base_dict[key] = value
        
        return base_dict
    
    def save_config_file(
        self, 
        config_name: str, 
        config_data: Dict[str, Any], 
        file_path: Optional[Union[str, Path]] = None
    ) -> Path:
        """
        Save configuration data to YAML file
        
        Args:
            config_name: Name of the configuration
            config_data: Configuration data to save
            file_path: Optional custom file path
            
        Returns:
            Path: Path to saved file
            
        Raises:
            ConfigurationError: If save fails
        """
        if file_path is None:
            file_path = self.config_dir / f"{config_name}.yaml"
        else:
            file_path = Path(file_path)
        
        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                yaml.dump(
                    config_data,
                    f,
                    default_flow_style=False,
                    allow_unicode=True,
                    sort_keys=False,
                    indent=2,
                )
            
            logger.info(f"Successfully saved configuration to: {file_path}")
            return file_path
            
        except Exception as e:
            raise ConfigurationError(f"Failed to save configuration file {file_path}: {e}")
    
    def get_config_files(self) -> List[Path]:
        """
        Get list of all configuration files
        
        Returns:
            List[Path]: List of configuration file paths
        """
        config_files = []
        
        if not self.config_dir.exists():
            return config_files
        
        # Main config files
        for config_name in ["system", "flows"]:
            config_file = self.config_dir / f"{config_name}.yaml"
            if config_file.exists():
                config_files.append(config_file)
        
        # Flow config files
        flows_dir = self.config_dir / "flows"
        if flows_dir.exists() and flows_dir.is_dir():
            config_files.extend(flows_dir.glob("*.yaml"))
        
        return config_files
    
    def create_default_configs(self) -> None:
        """
        Create default configuration files if they don't exist
        """
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        for config_name, config_data in self.default_configs.items():
            config_file = self.config_dir / f"{config_name}.yaml"
            
            if not config_file.exists():
                try:
                    self.save_config_file(config_name, config_data, config_file)
                    logger.info(f"Created default configuration file: {config_file}")
                except ConfigurationError as e:
                    logger.error(f"Failed to create default config {config_file}: {e}")
    
    def backup_config(self, config_name: str) -> Optional[Path]:
        """
        Create a backup of a configuration file
        
        Args:
            config_name: Name of the configuration to backup
            
        Returns:
            Optional[Path]: Path to backup file, None if backup failed
        """
        config_file = self.config_dir / f"{config_name}.yaml"
        
        if not config_file.exists():
            logger.warning(f"Cannot backup non-existent config: {config_file}")
            return None
        
        # Create backup with timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.config_dir / f"{config_name}.yaml.backup.{timestamp}"
        
        try:
            import shutil
            shutil.copy2(config_file, backup_file)
            logger.info(f"Created config backup: {backup_file}")
            return backup_file
            
        except Exception as e:
            logger.error(f"Failed to create config backup: {e}")
            return None