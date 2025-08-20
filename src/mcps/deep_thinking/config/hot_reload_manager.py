"""
Hot reload manager for configuration files with file system monitoring
"""

import asyncio
import logging
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Union

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from .config_validator import config_validator
from .exceptions import ConfigurationError
from .yaml_config_loader import YAMLConfigLoader

logger = logging.getLogger(__name__)


class ConfigFileEventHandler(FileSystemEventHandler):
    """
    File system event handler for configuration file changes
    """

    def __init__(self, hot_reload_manager: "HotReloadManager"):
        self.hot_reload_manager = hot_reload_manager
        self.debounce_delay = 1.0  # seconds
        self.pending_reloads: Dict[str, float] = {}

    def on_modified(self, event: FileSystemEvent) -> None:
        """Handle file modification events"""
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # Only process YAML files
        if file_path.suffix not in [".yaml", ".yml"]:
            return

        # Debounce rapid file changes
        current_time = time.time()
        file_key = str(file_path)

        if file_key in self.pending_reloads:
            # Update the timestamp for debouncing
            self.pending_reloads[file_key] = current_time
        else:
            # Schedule reload with debouncing
            self.pending_reloads[file_key] = current_time
            asyncio.create_task(self._debounced_reload(file_path))

    def on_created(self, event: FileSystemEvent) -> None:
        """Handle file creation events"""
        self.on_modified(event)  # Treat creation same as modification

    def on_deleted(self, event: FileSystemEvent) -> None:
        """Handle file deletion events"""
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        if file_path.suffix not in [".yaml", ".yml"]:
            return

        logger.warning(f"Configuration file deleted: {file_path}")
        asyncio.create_task(self.hot_reload_manager._handle_file_deletion(file_path))

    async def _debounced_reload(self, file_path: Path) -> None:
        """
        Debounced reload to handle rapid file changes

        Args:
            file_path: Path to the file that changed
        """
        file_key = str(file_path)

        # Wait for debounce delay
        await asyncio.sleep(self.debounce_delay)

        # Check if there were more recent changes
        if file_key in self.pending_reloads:
            last_change_time = self.pending_reloads[file_key]
            if time.time() - last_change_time < self.debounce_delay:
                # More recent changes, skip this reload
                return

            # Remove from pending reloads
            del self.pending_reloads[file_key]

        try:
            await self.hot_reload_manager._reload_config_file(file_path)
        except Exception as e:
            logger.error(f"Failed to reload config file {file_path}: {e}")


class HotReloadManager:
    """
    Manager for hot reloading configuration files
    """

    def __init__(
        self,
        config_dir: Optional[Union[str, Path]] = None,
        yaml_loader: Optional[YAMLConfigLoader] = None,
    ):
        """
        Initialize hot reload manager

        Args:
            config_dir: Directory to monitor for configuration files
            yaml_loader: YAML configuration loader instance
        """
        self.config_dir = Path(config_dir) if config_dir else Path("config")
        self.yaml_loader = yaml_loader or YAMLConfigLoader(self.config_dir)

        self.observer: Optional[Observer] = None
        self.is_monitoring = False
        self.reload_callbacks: List[Callable[[str, Dict[str, Any]], None]] = []
        self.error_callbacks: List[Callable[[str, Exception], None]] = []

        self.current_configs: Dict[str, Dict[str, Any]] = {}
        self.config_file_mapping: Dict[Path, str] = {}  # file_path -> config_name

        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Initialize the hot reload manager"""
        async with self._lock:
            # Load initial configurations
            await self._load_initial_configs()

            # Start file monitoring
            await self._start_monitoring()

    async def _load_initial_configs(self) -> None:
        """Load initial configuration files"""
        try:
            configs = self.yaml_loader.load_all_configs()
            self.current_configs = configs

            # Build file mapping
            self._build_file_mapping()

            logger.info(f"Loaded {len(configs)} initial configurations")

        except Exception as e:
            logger.error(f"Failed to load initial configurations: {e}")
            raise ConfigurationError(f"Failed to load initial configurations: {e}")

    def _build_file_mapping(self) -> None:
        """Build mapping from file paths to configuration names"""
        self.config_file_mapping.clear()

        # Main config files
        for config_name in ["system", "flows"]:
            config_file = self.config_dir / f"{config_name}.yaml"
            if config_file.exists():
                self.config_file_mapping[config_file] = config_name

        # Flow config files in flows directory
        flows_dir = self.config_dir / "flows"
        if flows_dir.exists() and flows_dir.is_dir():
            for flow_file in flows_dir.glob("*.yaml"):
                self.config_file_mapping[flow_file] = "flows"

    async def _start_monitoring(self) -> None:
        """Start file system monitoring"""
        if self.is_monitoring:
            return

        try:
            self.observer = Observer()
            event_handler = ConfigFileEventHandler(self)

            # Monitor main config directory
            self.observer.schedule(event_handler, str(self.config_dir), recursive=True)

            self.observer.start()
            self.is_monitoring = True

            logger.info(
                f"Started monitoring configuration directory: {self.config_dir}"
            )

        except Exception as e:
            logger.error(f"Failed to start file monitoring: {e}")
            raise ConfigurationError(f"Failed to start file monitoring: {e}")

    async def stop_monitoring(self) -> None:
        """Stop file system monitoring"""
        if self.observer and self.is_monitoring:
            self.observer.stop()
            self.observer.join()
            self.is_monitoring = False
            logger.info("Stopped configuration file monitoring")

    async def _reload_config_file(self, file_path: Path) -> None:
        """
        Reload a specific configuration file

        Args:
            file_path: Path to the file to reload
        """
        async with self._lock:
            try:
                # Determine config name from file path
                config_name = self._get_config_name_from_path(file_path)
                if not config_name:
                    logger.warning(f"Unknown configuration file: {file_path}")
                    return

                # Load and validate the configuration
                if config_name == "flows" and file_path.parent.name == "flows":
                    # Handle individual flow files
                    await self._reload_flow_file(file_path)
                else:
                    # Handle main config files
                    await self._reload_main_config_file(file_path, config_name)

            except Exception as e:
                logger.error(f"Failed to reload config file {file_path}: {e}")
                await self._notify_error_callbacks(str(file_path), e)

    def _get_config_name_from_path(self, file_path: Path) -> Optional[str]:
        """
        Get configuration name from file path

        Args:
            file_path: Path to the configuration file

        Returns:
            Optional[str]: Configuration name or None if unknown
        """
        # Check direct mapping
        if file_path in self.config_file_mapping:
            return self.config_file_mapping[file_path]

        # Check if it's a main config file
        if file_path.parent == self.config_dir:
            config_name = file_path.stem
            if config_name in ["system", "flows"]:
                return config_name

        # Check if it's a flow file
        if (
            file_path.parent.name == "flows"
            and file_path.parent.parent == self.config_dir
        ):
            return "flows"

        return None

    async def _reload_main_config_file(self, file_path: Path, config_name: str) -> None:
        """
        Reload a main configuration file

        Args:
            file_path: Path to the configuration file
            config_name: Name of the configuration
        """
        try:
            # Load the configuration file
            new_config = self.yaml_loader.load_config_file(file_path)

            # Merge with defaults if needed
            merged_config = self.yaml_loader.merge_with_defaults(
                config_name, new_config
            )

            # Validate the configuration
            is_valid, errors = config_validator.validate_config(
                config_name, merged_config
            )

            if not is_valid:
                error_msg = f"Configuration validation failed for {config_name}: {'; '.join(errors)}"
                logger.error(error_msg)
                await self._notify_error_callbacks(
                    config_name, ConfigurationError(error_msg)
                )
                return

            # Store old config for rollback
            old_config = self.current_configs.get(config_name, {}).copy()

            # Update current configuration
            self.current_configs[config_name] = merged_config

            # Update file mapping
            self.config_file_mapping[file_path] = config_name

            # Notify callbacks
            await self._notify_reload_callbacks(config_name, merged_config)

            logger.info(f"Successfully reloaded configuration: {config_name}")

        except Exception as e:
            logger.error(f"Failed to reload {config_name} config from {file_path}: {e}")
            raise

    async def _reload_flow_file(self, file_path: Path) -> None:
        """
        Reload an individual flow configuration file

        Args:
            file_path: Path to the flow configuration file
        """
        try:
            # Load the flow configuration
            flow_config = self.yaml_loader.load_config_file(file_path)

            # Validate the flow configuration
            is_valid, errors = config_validator.validate_config("flows", flow_config)

            if not is_valid:
                error_msg = f"Flow configuration validation failed for {file_path}: {'; '.join(errors)}"
                logger.error(error_msg)
                await self._notify_error_callbacks(
                    str(file_path), ConfigurationError(error_msg)
                )
                return

            # Update flows configuration
            if "flows" not in self.current_configs:
                self.current_configs["flows"] = {}

            # Merge the new flow configurations
            self.current_configs["flows"].update(flow_config)

            # Update file mapping
            self.config_file_mapping[file_path] = "flows"

            # Notify callbacks
            await self._notify_reload_callbacks("flows", self.current_configs["flows"])

            logger.info(f"Successfully reloaded flow configuration from: {file_path}")

        except Exception as e:
            logger.error(f"Failed to reload flow config from {file_path}: {e}")
            raise

    async def _handle_file_deletion(self, file_path: Path) -> None:
        """
        Handle configuration file deletion

        Args:
            file_path: Path to the deleted file
        """
        async with self._lock:
            config_name = self._get_config_name_from_path(file_path)

            if not config_name:
                return

            # Remove from file mapping
            if file_path in self.config_file_mapping:
                del self.config_file_mapping[file_path]

            # Handle flow file deletion
            if config_name == "flows" and file_path.parent.name == "flows":
                # Remove specific flows from the deleted file
                try:
                    # We can't know which flows were in the deleted file,
                    # so we need to reload all remaining flow files
                    await self._reload_all_flow_files()
                except Exception as e:
                    logger.error(f"Failed to reload flows after file deletion: {e}")

            logger.warning(f"Configuration file deleted: {file_path}")

    async def _reload_all_flow_files(self) -> None:
        """Reload all flow configuration files"""
        flows_dir = self.config_dir / "flows"

        if not flows_dir.exists():
            return

        # Clear current flows
        if "flows" in self.current_configs:
            self.current_configs["flows"].clear()
        else:
            self.current_configs["flows"] = {}

        # Reload main flows.yaml if it exists
        main_flows_file = self.config_dir / "flows.yaml"
        if main_flows_file.exists():
            try:
                flows_config = self.yaml_loader.load_config_file(main_flows_file)
                self.current_configs["flows"].update(flows_config)
            except Exception as e:
                logger.error(f"Failed to reload main flows config: {e}")

        # Reload all flow files in flows directory
        for flow_file in flows_dir.glob("*.yaml"):
            try:
                flow_config = self.yaml_loader.load_config_file(flow_file)
                self.current_configs["flows"].update(flow_config)
                self.config_file_mapping[flow_file] = "flows"
            except Exception as e:
                logger.error(f"Failed to reload flow file {flow_file}: {e}")

        # Notify callbacks
        await self._notify_reload_callbacks("flows", self.current_configs["flows"])

    async def _notify_reload_callbacks(
        self, config_name: str, config_data: Dict[str, Any]
    ) -> None:
        """
        Notify reload callbacks

        Args:
            config_name: Name of the configuration that was reloaded
            config_data: New configuration data
        """
        for callback in self.reload_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(config_name, config_data)
                else:
                    callback(config_name, config_data)
            except Exception as e:
                logger.error(f"Reload callback failed: {e}")

    async def _notify_error_callbacks(self, config_name: str, error: Exception) -> None:
        """
        Notify error callbacks

        Args:
            config_name: Name of the configuration that had an error
            error: The error that occurred
        """
        for callback in self.error_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(config_name, error)
                else:
                    callback(config_name, error)
            except Exception as e:
                logger.error(f"Error callback failed: {e}")

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

    def add_error_callback(self, callback: Callable[[str, Exception], None]) -> None:
        """
        Add a callback to be called when configuration errors occur

        Args:
            callback: Callback function that takes (config_name, error)
        """
        self.error_callbacks.append(callback)

    def remove_error_callback(self, callback: Callable[[str, Exception], None]) -> None:
        """
        Remove an error callback

        Args:
            callback: Callback function to remove
        """
        if callback in self.error_callbacks:
            self.error_callbacks.remove(callback)

    def get_current_config(self, config_name: str) -> Optional[Dict[str, Any]]:
        """
        Get current configuration data

        Args:
            config_name: Name of the configuration

        Returns:
            Optional[Dict[str, Any]]: Configuration data or None if not found
        """
        return self.current_configs.get(config_name)

    def get_all_configs(self) -> Dict[str, Dict[str, Any]]:
        """Get all current configurations"""
        return self.current_configs.copy()

    def get_monitored_files(self) -> List[Path]:
        """Get list of currently monitored configuration files"""
        return list(self.config_file_mapping.keys())

    def is_file_monitored(self, file_path: Union[str, Path]) -> bool:
        """
        Check if a file is being monitored

        Args:
            file_path: Path to check

        Returns:
            bool: True if file is monitored
        """
        return Path(file_path) in self.config_file_mapping

    async def force_reload(self, config_name: Optional[str] = None) -> None:
        """
        Force reload of configuration(s)

        Args:
            config_name: Specific configuration to reload, or None for all
        """
        async with self._lock:
            if config_name:
                # Reload specific configuration
                config_files = [
                    path
                    for path, name in self.config_file_mapping.items()
                    if name == config_name
                ]

                for file_path in config_files:
                    await self._reload_config_file(file_path)
            else:
                # Reload all configurations
                await self._load_initial_configs()

                # Notify all callbacks
                for config_name, config_data in self.current_configs.items():
                    await self._notify_reload_callbacks(config_name, config_data)

    async def cleanup(self) -> None:
        """Cleanup resources"""
        await self.stop_monitoring()
        self.reload_callbacks.clear()
        self.error_callbacks.clear()


# Global hot reload manager instance
hot_reload_manager = HotReloadManager()
