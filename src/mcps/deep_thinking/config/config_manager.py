"""
Configuration management system with hot reload support
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

import yaml
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from ..models.agent_models import AgentConfig, AgentType
from .exceptions import ConfigurationError

logger = logging.getLogger(__name__)


class ConfigFileHandler(FileSystemEventHandler):
    """File system event handler for configuration file changes"""

    def __init__(self, config_manager: "ConfigManager"):
        self.config_manager = config_manager
        self.debounce_delay = 1.0  # seconds
        self.pending_reloads = set()

    def on_modified(self, event):
        if event.is_directory:
            return

        file_path = Path(event.src_path)
        if file_path.suffix in [".yaml", ".yml", ".json"]:
            # Debounce rapid file changes
            asyncio.create_task(self._debounced_reload(file_path))

    async def _debounced_reload(self, file_path: Path):
        """Debounced reload to handle rapid file changes"""
        file_key = str(file_path)

        if file_key in self.pending_reloads:
            return

        self.pending_reloads.add(file_key)
        await asyncio.sleep(self.debounce_delay)

        try:
            await self.config_manager._reload_config_file(file_path)
        except Exception as e:
            logger.error(f"Failed to reload config file {file_path}: {e}")
        finally:
            self.pending_reloads.discard(file_key)


class ConfigManager:
    """
    Central configuration manager with hot reload support
    """

    def __init__(self, config_dir: Optional[Union[str, Path]] = None):
        """
        Initialize configuration manager

        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = Path(config_dir) if config_dir else Path("config")
        self.config_data: Dict[str, Any] = {}
        self.config_files: Dict[str, Path] = {}
        self.reload_callbacks: List[Callable[[str, Dict[str, Any]], None]] = []
        self.file_observer: Optional[Observer] = None
        self.is_watching = False
        self._lock = asyncio.Lock()

        # Default configuration
        self.default_config = {
            "system": {
                "log_level": "INFO",
                "max_concurrent_agents": 10,
                "default_timeout": 300,
                "enable_caching": True,
                "cache_ttl": 3600,
            },
            "agents": {
                "default_temperature": 0.7,
                "default_max_retries": 3,
                "quality_threshold": 0.8,
            },
            "flows": {
                "default_flow": "comprehensive_analysis",
                "max_flow_steps": 50,
                "enable_parallel_execution": True,
            },
            "search": {
                "max_results_per_query": 10,
                "search_timeout": 30,
                "enable_source_diversity": True,
            },
        }

    async def initialize(self) -> None:
        """Initialize the configuration manager"""
        async with self._lock:
            # Create config directory if it doesn't exist
            self.config_dir.mkdir(parents=True, exist_ok=True)

            # Load all configuration files
            await self._load_all_configs()

            # Start file watching
            await self._start_file_watching()

    async def _load_all_configs(self) -> None:
        """Load all configuration files from the config directory"""
        if not self.config_dir.exists():
            logger.warning(f"Config directory {self.config_dir} does not exist")
            return

        for file_path in self.config_dir.rglob("*.yaml"):
            await self._load_config_file(file_path)

        for file_path in self.config_dir.rglob("*.yml"):
            await self._load_config_file(file_path)

        for file_path in self.config_dir.rglob("*.json"):
            await self._load_config_file(file_path)

    async def _load_config_file(self, file_path: Path) -> None:
        """Load a single configuration file"""
        try:
            config_name = file_path.stem

            with open(file_path, "r", encoding="utf-8") as f:
                if file_path.suffix in [".yaml", ".yml"]:
                    config_data = yaml.safe_load(f)
                elif file_path.suffix == ".json":
                    config_data = json.load(f)
                else:
                    logger.warning(f"Unsupported config file format: {file_path}")
                    return

            if config_data is None:
                config_data = {}

            self.config_data[config_name] = config_data
            self.config_files[config_name] = file_path

            logger.info(f"Loaded configuration: {config_name} from {file_path}")

        except Exception as e:
            logger.error(f"Failed to load config file {file_path}: {e}")
            raise ConfigurationError(f"Failed to load config file {file_path}: {e}")

    async def _reload_config_file(self, file_path: Path) -> None:
        """Reload a specific configuration file"""
        async with self._lock:
            config_name = file_path.stem
            # old_config = self.config_data.get(config_name, {}).copy()  # Unused variable

            await self._load_config_file(file_path)

            new_config = self.config_data.get(config_name, {})

            # Notify callbacks of configuration change
            for callback in self.reload_callbacks:
                try:
                    callback(config_name, new_config)
                except Exception as e:
                    logger.error(f"Config reload callback failed: {e}")

            logger.info(f"Reloaded configuration: {config_name}")

    async def _start_file_watching(self) -> None:
        """Start watching configuration files for changes"""
        if self.is_watching:
            return

        try:
            self.file_observer = Observer()
            event_handler = ConfigFileHandler(self)

            self.file_observer.schedule(
                event_handler, str(self.config_dir), recursive=True
            )

            self.file_observer.start()
            self.is_watching = True

            logger.info(f"Started watching config directory: {self.config_dir}")

        except Exception as e:
            logger.error(f"Failed to start file watching: {e}")

    async def stop_file_watching(self) -> None:
        """Stop watching configuration files"""
        if self.file_observer and self.is_watching:
            self.file_observer.stop()
            self.file_observer.join()
            self.is_watching = False
            logger.info("Stopped watching config files")

    def get_config(self, config_name: str, default: Any = None) -> Any:
        """
        Get configuration by name

        Args:
            config_name: Name of the configuration
            default: Default value if config not found

        Returns:
            Configuration data
        """
        return self.config_data.get(config_name, default)

    def get_nested_config(self, path: str, default: Any = None) -> Any:
        """
        Get nested configuration using dot notation

        Args:
            path: Dot-separated path (e.g., 'system.log_level')
            default: Default value if config not found

        Returns:
            Configuration value
        """
        parts = path.split(".")
        current = self.config_data

        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default

        return current

    def set_config(self, config_name: str, config_data: Dict[str, Any]) -> None:
        """
        Set configuration data

        Args:
            config_name: Name of the configuration
            config_data: Configuration data to set
        """
        self.config_data[config_name] = config_data

    def update_config(self, config_name: str, updates: Dict[str, Any]) -> None:
        """
        Update existing configuration

        Args:
            config_name: Name of the configuration
            updates: Updates to apply
        """
        if config_name not in self.config_data:
            self.config_data[config_name] = {}

        self._deep_update(self.config_data[config_name], updates)

    def _deep_update(
        self, base_dict: Dict[str, Any], update_dict: Dict[str, Any]
    ) -> None:
        """Recursively update nested dictionaries"""
        for key, value in update_dict.items():
            if (
                key in base_dict
                and isinstance(base_dict[key], dict)
                and isinstance(value, dict)
            ):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value

    async def save_config(self, config_name: str, file_format: str = "yaml") -> None:
        """
        Save configuration to file

        Args:
            config_name: Name of the configuration
            file_format: File format ('yaml' or 'json')
        """
        if config_name not in self.config_data:
            raise ConfigurationError(f"Configuration '{config_name}' not found")

        file_extension = "yaml" if file_format == "yaml" else "json"
        file_path = self.config_dir / f"{config_name}.{file_extension}"

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                if file_format == "yaml":
                    yaml.dump(
                        self.config_data[config_name], f, default_flow_style=False
                    )
                else:
                    json.dump(self.config_data[config_name], f, indent=2)

            self.config_files[config_name] = file_path
            logger.info(f"Saved configuration '{config_name}' to {file_path}")

        except Exception as e:
            raise ConfigurationError(f"Failed to save config '{config_name}': {e}")

    def add_reload_callback(
        self, callback: Callable[[str, Dict[str, Any]], None]
    ) -> None:
        """
        Add a callback to be called when configuration is reloaded

        Args:
            callback: Callback function that takes (config_name, config_data)
        """
        self.reload_callbacks.append(callback)

    def remove_reload_callback(
        self, callback: Callable[[str, Dict[str, Any]], None]
    ) -> None:
        """
        Remove a reload callback

        Args:
            callback: Callback function to remove
        """
        if callback in self.reload_callbacks:
            self.reload_callbacks.remove(callback)

    def get_agent_config(self, agent_type: AgentType) -> AgentConfig:
        """
        Get configuration for a specific agent type

        Args:
            agent_type: Type of agent

        Returns:
            AgentConfig: Agent configuration
        """
        # Get agent-specific config
        agent_configs = self.get_config("agents", {})
        agent_specific = agent_configs.get(agent_type.value, {})

        # Merge with defaults
        default_agent_config = {
            "agent_type": agent_type,
            "enabled": True,
            "max_retries": self.get_nested_config("agents.default_max_retries", 3),
            "timeout_seconds": self.get_nested_config("system.default_timeout", 300),
            "temperature": self.get_nested_config("agents.default_temperature", 0.7),
            "quality_threshold": self.get_nested_config(
                "agents.quality_threshold", 0.8
            ),
        }

        # Update with agent-specific config
        default_agent_config.update(agent_specific)

        return AgentConfig(**default_agent_config)

    def get_all_configs(self) -> Dict[str, Any]:
        """Get all loaded configurations"""
        return self.config_data.copy()

    def get_config_files(self) -> Dict[str, Path]:
        """Get mapping of config names to file paths"""
        return self.config_files.copy()

    def validate_config(self, config_name: str, schema: Dict[str, Any]) -> bool:
        """
        Validate configuration against a schema

        Args:
            config_name: Name of configuration to validate
            schema: JSON schema for validation

        Returns:
            bool: True if valid

        Raises:
            ConfigurationError: If validation fails
        """
        # This is a simplified validation - in production you might use jsonschema
        config = self.get_config(config_name)
        if config is None:
            raise ConfigurationError(f"Configuration '{config_name}' not found")

        # Basic validation logic here
        # For now, just check if config is a dictionary
        if not isinstance(config, dict):
            raise ConfigurationError(
                f"Configuration '{config_name}' must be a dictionary"
            )

        return True

    async def cleanup(self) -> None:
        """Cleanup resources"""
        await self.stop_file_watching()


# Global configuration manager instance
config_manager = ConfigManager()
