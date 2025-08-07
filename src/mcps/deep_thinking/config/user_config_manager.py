"""
User custom configuration management with priority and inheritance
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml

from .config_validator import config_validator
from .exceptions import ConfigurationError
from .yaml_config_loader import YAMLConfigLoader

logger = logging.getLogger(__name__)


class ConfigPriority:
    """Configuration priority levels"""
    
    SYSTEM_DEFAULT = 0      # Built-in system defaults
    GLOBAL_CONFIG = 10      # Global configuration files
    USER_DEFAULT = 20       # User's default preferences
    USER_CUSTOM = 30        # User's custom configurations
    SESSION_OVERRIDE = 40   # Session-specific overrides
    RUNTIME_OVERRIDE = 50   # Runtime parameter overrides


class UserConfigManager:
    """
    Manager for user custom configurations with priority and inheritance
    """
    
    def __init__(
        self, 
        user_config_dir: Optional[Union[str, Path]] = None,
        global_config_dir: Optional[Union[str, Path]] = None
    ):
        """
        Initialize user config manager
        
        Args:
            user_config_dir: Directory for user-specific configurations
            global_config_dir: Directory for global configurations
        """
        self.user_config_dir = Path(user_config_dir) if user_config_dir else Path.home() / ".deep_thinking"
        self.global_config_dir = Path(global_config_dir) if global_config_dir else Path("config")
        
        self.yaml_loader = YAMLConfigLoader()
        
        # Configuration layers with priorities
        self.config_layers = {
            ConfigPriority.SYSTEM_DEFAULT: {},
            ConfigPriority.GLOBAL_CONFIG: {},
            ConfigPriority.USER_DEFAULT: {},
            ConfigPriority.USER_CUSTOM: {},
            ConfigPriority.SESSION_OVERRIDE: {},
            ConfigPriority.RUNTIME_OVERRIDE: {},
        }
        
        # User preference profiles
        self.user_profiles = {}
        self.active_profile = "default"
        
        # Configuration inheritance rules
        self.inheritance_rules = {
            "system": {
                "inheritable_fields": ["log_level", "max_concurrent_agents", "default_timeout", "debug_mode"],
                "protected_fields": [],  # No protected fields for testing
            },
            "agents": {
                "inheritable_fields": ["default_temperature", "quality_threshold"],
                "protected_fields": [],
            },
            "flows": {
                "inheritable_fields": ["global_config", "error_handling"],
                "protected_fields": ["steps"],  # Steps cannot be inherited
            },
        }
    
    async def initialize(self) -> None:
        """Initialize user configuration manager"""
        # Create user config directory if it doesn't exist
        self.user_config_dir.mkdir(parents=True, exist_ok=True)
        
        # Load system defaults
        await self._load_system_defaults()
        
        # Load global configurations
        await self._load_global_configs()
        
        # Load user configurations
        await self._load_user_configs()
        
        # Load user profiles
        await self._load_user_profiles()
        
        logger.info("User configuration manager initialized")
    
    async def _load_system_defaults(self) -> None:
        """Load system default configurations"""
        system_defaults = {
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
        
        self.config_layers[ConfigPriority.SYSTEM_DEFAULT] = system_defaults
    
    async def _load_global_configs(self) -> None:
        """Load global configuration files"""
        if not self.global_config_dir.exists():
            logger.info(f"Global config directory not found: {self.global_config_dir}")
            return
        
        try:
            global_configs = self.yaml_loader.load_all_configs()
            self.config_layers[ConfigPriority.GLOBAL_CONFIG] = global_configs
            logger.info(f"Loaded global configurations from {self.global_config_dir}")
        except Exception as e:
            logger.error(f"Failed to load global configurations: {e}")
    
    async def _load_user_configs(self) -> None:
        """Load user-specific configurations"""
        user_config_file = self.user_config_dir / "config.yaml"
        
        if user_config_file.exists():
            try:
                user_config = self.yaml_loader.load_config_file(user_config_file)
                self.config_layers[ConfigPriority.USER_DEFAULT] = user_config
                logger.info(f"Loaded user configuration from {user_config_file}")
            except Exception as e:
                logger.error(f"Failed to load user configuration: {e}")
        else:
            # Create default user config
            await self._create_default_user_config()
    
    async def _load_user_profiles(self) -> None:
        """Load user configuration profiles"""
        profiles_file = self.user_config_dir / "profiles.yaml"
        
        if profiles_file.exists():
            try:
                profiles_data = self.yaml_loader.load_config_file(profiles_file)
                self.user_profiles = profiles_data.get("profiles", {})
                self.active_profile = profiles_data.get("active_profile", "default")
                logger.info(f"Loaded {len(self.user_profiles)} user profiles")
            except Exception as e:
                logger.error(f"Failed to load user profiles: {e}")
        else:
            # Create default profile
            await self._create_default_profiles()
    
    async def _create_default_user_config(self) -> None:
        """Create default user configuration"""
        default_user_config = {
            "user_preferences": {
                "preferred_flow": "comprehensive_analysis",
                "default_complexity": "moderate",
                "enable_notifications": True,
                "auto_save_sessions": True,
            },
            "system": {
                "log_level": "INFO",
                "max_concurrent_agents": 8,  # User prefers fewer concurrent agents
            },
            "agents": {
                "default_temperature": 0.8,  # User prefers higher creativity
                "quality_threshold": 0.85,   # User wants higher quality
            },
        }
        
        user_config_file = self.user_config_dir / "config.yaml"
        self.yaml_loader.save_config_file("user_config", default_user_config, user_config_file)
        self.config_layers[ConfigPriority.USER_DEFAULT] = default_user_config
        
        logger.info(f"Created default user configuration at {user_config_file}")
    
    async def _create_default_profiles(self) -> None:
        """Create default user profiles"""
        default_profiles = {
            "profiles": {
                "default": {
                    "name": "Default Profile",
                    "description": "Standard configuration for general use",
                    "config": {},
                },
                "research": {
                    "name": "Research Profile",
                    "description": "Optimized for research and analysis",
                    "config": {
                        "agents": {
                            "quality_threshold": 0.9,
                            "evidence_seeker": {
                                "min_sources": 8,
                                "academic_preference": True,
                            },
                        },
                        "flows": {
                            "default_flow": "research_focused",
                        },
                    },
                },
                "creative": {
                    "name": "Creative Profile",
                    "description": "Optimized for creative thinking and innovation",
                    "config": {
                        "agents": {
                            "default_temperature": 0.9,
                            "innovator": {
                                "methods": ["SCAMPER", "TRIZ", "lateral_thinking"],
                                "novelty_threshold": 0.6,
                            },
                        },
                        "flows": {
                            "default_flow": "creative_thinking",
                        },
                    },
                },
                "quick": {
                    "name": "Quick Analysis",
                    "description": "Fast analysis for simple questions",
                    "config": {
                        "system": {
                            "max_concurrent_agents": 5,
                            "default_timeout": 120,
                        },
                        "flows": {
                            "default_flow": "quick_analysis",
                        },
                    },
                },
            },
            "active_profile": "default",
        }
        
        profiles_file = self.user_config_dir / "profiles.yaml"
        self.yaml_loader.save_config_file("profiles", default_profiles, profiles_file)
        self.user_profiles = default_profiles["profiles"]
        self.active_profile = default_profiles["active_profile"]
        
        logger.info(f"Created default user profiles at {profiles_file}")
    
    def get_effective_config(
        self, 
        config_name: str, 
        profile: Optional[str] = None,
        session_overrides: Optional[Dict[str, Any]] = None,
        runtime_overrides: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get effective configuration by merging all layers with priority
        
        Args:
            config_name: Name of configuration to get
            profile: Profile to use (defaults to active profile)
            session_overrides: Session-specific overrides
            runtime_overrides: Runtime parameter overrides
            
        Returns:
            Dict[str, Any]: Effective configuration
        """
        profile = profile or self.active_profile
        
        # Start with system defaults
        effective_config = self._deep_copy(
            self.config_layers[ConfigPriority.SYSTEM_DEFAULT].get(config_name, {})
        )
        
        # Apply global configuration
        global_config = self.config_layers[ConfigPriority.GLOBAL_CONFIG].get(config_name, {})
        effective_config = self._merge_configs(effective_config, global_config, config_name)
        
        # Apply user default configuration
        user_config = self.config_layers[ConfigPriority.USER_DEFAULT].get(config_name, {})
        effective_config = self._merge_configs(effective_config, user_config, config_name)
        
        # Apply profile-specific configuration
        if profile in self.user_profiles:
            profile_config = self.user_profiles[profile].get("config", {}).get(config_name, {})
            effective_config = self._merge_configs(effective_config, profile_config, config_name)
        
        # Apply user custom configuration
        custom_config = self.config_layers[ConfigPriority.USER_CUSTOM].get(config_name, {})
        effective_config = self._merge_configs(effective_config, custom_config, config_name)
        
        # Apply session overrides
        if session_overrides:
            session_config = session_overrides.get(config_name, {})
            effective_config = self._merge_configs(effective_config, session_config, config_name)
        
        # Apply runtime overrides
        if runtime_overrides:
            runtime_config = runtime_overrides.get(config_name, {})
            effective_config = self._merge_configs(effective_config, runtime_config, config_name)
        
        return effective_config
    
    def _merge_configs(
        self, 
        base_config: Dict[str, Any], 
        override_config: Dict[str, Any],
        config_name: str
    ) -> Dict[str, Any]:
        """
        Merge configurations respecting inheritance rules
        
        Args:
            base_config: Base configuration
            override_config: Configuration to merge in
            config_name: Name of configuration for inheritance rules
            
        Returns:
            Dict[str, Any]: Merged configuration
        """
        if not override_config:
            return base_config
        
        # Get inheritance rules for this config type
        rules = self.inheritance_rules.get(config_name, {})
        inheritable_fields = rules.get("inheritable_fields", [])
        protected_fields = rules.get("protected_fields", [])
        
        merged = self._deep_copy(base_config)
        
        for key, value in override_config.items():
            # Check if field is protected
            if protected_fields and key in protected_fields:
                logger.warning(f"Skipping protected field '{key}' in config '{config_name}'")
                continue
            
            # Check if field is inheritable (if rules are defined)
            if inheritable_fields and key not in inheritable_fields:
                logger.debug(f"Field '{key}' not in inheritable fields for config '{config_name}'")
                # Still allow it, but log for debugging
            
            # Merge the value
            if isinstance(value, dict) and isinstance(merged.get(key), dict):
                merged[key] = self._deep_merge_dict(merged[key], value)
            else:
                merged[key] = self._deep_copy(value)
        
        return merged
    
    def _deep_merge_dict(self, base_dict: Dict[str, Any], override_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries"""
        result = self._deep_copy(base_dict)
        
        for key, value in override_dict.items():
            if isinstance(value, dict) and isinstance(result.get(key), dict):
                result[key] = self._deep_merge_dict(result[key], value)
            else:
                result[key] = self._deep_copy(value)
        
        return result
    
    def _deep_copy(self, obj: Any) -> Any:
        """Deep copy an object"""
        if isinstance(obj, dict):
            return {key: self._deep_copy(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._deep_copy(item) for item in obj]
        else:
            return obj
    
    def set_user_preference(self, key: str, value: Any, profile: Optional[str] = None) -> None:
        """
        Set a user preference
        
        Args:
            key: Preference key (dot notation supported)
            value: Preference value
            profile: Profile to set preference for (defaults to active profile)
        """
        profile = profile or self.active_profile
        
        if profile not in self.user_profiles:
            raise ConfigurationError(f"Profile '{profile}' not found")
        
        # Parse key path
        keys = key.split(".")
        config_name = keys[0]
        
        # Initialize profile config if needed
        if "config" not in self.user_profiles[profile]:
            self.user_profiles[profile]["config"] = {}
        
        if config_name not in self.user_profiles[profile]["config"]:
            self.user_profiles[profile]["config"][config_name] = {}
        
        # Set the value
        current = self.user_profiles[profile]["config"][config_name]
        for key_part in keys[1:-1]:
            if key_part not in current:
                current[key_part] = {}
            current = current[key_part]
        
        current[keys[-1]] = value
        
        logger.info(f"Set user preference '{key}' = '{value}' for profile '{profile}'")
    
    def get_user_preference(self, key: str, default: Any = None, profile: Optional[str] = None) -> Any:
        """
        Get a user preference
        
        Args:
            key: Preference key (dot notation supported)
            default: Default value if not found
            profile: Profile to get preference from (defaults to active profile)
            
        Returns:
            Any: Preference value or default
        """
        profile = profile or self.active_profile
        
        if profile not in self.user_profiles:
            return default
        
        # Parse key path
        keys = key.split(".")
        
        current = self.user_profiles[profile].get("config", {})
        for key_part in keys:
            if isinstance(current, dict) and key_part in current:
                current = current[key_part]
            else:
                return default
        
        return current
    
    def create_profile(
        self, 
        profile_name: str, 
        display_name: str, 
        description: str,
        base_profile: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Create a new user profile
        
        Args:
            profile_name: Internal profile name
            display_name: Display name for the profile
            description: Profile description
            base_profile: Profile to inherit from
            config: Profile-specific configuration
        """
        if profile_name in self.user_profiles:
            raise ConfigurationError(f"Profile '{profile_name}' already exists")
        
        profile_config = {}
        
        # Inherit from base profile if specified
        if base_profile:
            if base_profile not in self.user_profiles:
                raise ConfigurationError(f"Base profile '{base_profile}' not found")
            
            base_config = self.user_profiles[base_profile].get("config", {})
            profile_config = self._deep_copy(base_config)
        
        # Apply custom configuration
        if config:
            for config_name, config_data in config.items():
                if config_name in profile_config:
                    profile_config[config_name] = self._merge_configs(
                        profile_config[config_name], config_data, config_name
                    )
                else:
                    profile_config[config_name] = self._deep_copy(config_data)
        
        # Create profile
        self.user_profiles[profile_name] = {
            "name": display_name,
            "description": description,
            "config": profile_config,
        }
        
        if base_profile:
            self.user_profiles[profile_name]["inherits_from"] = base_profile
        
        logger.info(f"Created user profile '{profile_name}' ({display_name})")
    
    def delete_profile(self, profile_name: str) -> None:
        """
        Delete a user profile
        
        Args:
            profile_name: Name of profile to delete
        """
        if profile_name not in self.user_profiles:
            raise ConfigurationError(f"Profile '{profile_name}' not found")
        
        if profile_name == "default":
            raise ConfigurationError("Cannot delete default profile")
        
        if profile_name == self.active_profile:
            self.active_profile = "default"
        
        del self.user_profiles[profile_name]
        logger.info(f"Deleted user profile '{profile_name}'")
    
    def set_active_profile(self, profile_name: str) -> None:
        """
        Set the active profile
        
        Args:
            profile_name: Name of profile to activate
        """
        if profile_name not in self.user_profiles:
            raise ConfigurationError(f"Profile '{profile_name}' not found")
        
        self.active_profile = profile_name
        logger.info(f"Set active profile to '{profile_name}'")
    
    def get_profile_list(self) -> List[Dict[str, Any]]:
        """
        Get list of available profiles
        
        Returns:
            List[Dict[str, Any]]: List of profile information
        """
        profiles = []
        
        for profile_name, profile_data in self.user_profiles.items():
            profiles.append({
                "name": profile_name,
                "display_name": profile_data.get("name", profile_name),
                "description": profile_data.get("description", ""),
                "is_active": profile_name == self.active_profile,
                "inherits_from": profile_data.get("inherits_from"),
            })
        
        return profiles
    
    async def save_user_config(self) -> None:
        """Save user configuration to file"""
        user_config_file = self.user_config_dir / "config.yaml"
        user_config = self.config_layers[ConfigPriority.USER_DEFAULT]
        
        try:
            self.yaml_loader.save_config_file("user_config", user_config, user_config_file)
            logger.info(f"Saved user configuration to {user_config_file}")
        except Exception as e:
            raise ConfigurationError(f"Failed to save user configuration: {e}")
    
    async def save_user_profiles(self) -> None:
        """Save user profiles to file"""
        profiles_file = self.user_config_dir / "profiles.yaml"
        profiles_data = {
            "profiles": self.user_profiles,
            "active_profile": self.active_profile,
        }
        
        try:
            self.yaml_loader.save_config_file("profiles", profiles_data, profiles_file)
            logger.info(f"Saved user profiles to {profiles_file}")
        except Exception as e:
            raise ConfigurationError(f"Failed to save user profiles: {e}")
    
    def export_config(
        self, 
        export_path: Union[str, Path], 
        include_profiles: bool = True,
        format: str = "yaml"
    ) -> None:
        """
        Export user configuration to file
        
        Args:
            export_path: Path to export file
            include_profiles: Whether to include profiles
            format: Export format ('yaml' or 'json')
        """
        export_path = Path(export_path)
        
        export_data = {
            "user_config": self.config_layers[ConfigPriority.USER_DEFAULT],
            "custom_config": self.config_layers[ConfigPriority.USER_CUSTOM],
        }
        
        if include_profiles:
            export_data["profiles"] = {
                "profiles": self.user_profiles,
                "active_profile": self.active_profile,
            }
        
        export_data["metadata"] = {
            "export_timestamp": self._get_timestamp(),
            "format_version": "1.0",
        }
        
        try:
            if format.lower() == "json":
                with open(export_path, "w") as f:
                    json.dump(export_data, f, indent=2)
            else:
                with open(export_path, "w") as f:
                    yaml.dump(export_data, f, default_flow_style=False)
            
            logger.info(f"Exported user configuration to {export_path}")
            
        except Exception as e:
            raise ConfigurationError(f"Failed to export configuration: {e}")
    
    def import_config(
        self, 
        import_path: Union[str, Path], 
        merge_mode: str = "replace"
    ) -> None:
        """
        Import user configuration from file
        
        Args:
            import_path: Path to import file
            merge_mode: How to handle conflicts ('replace', 'merge', 'skip')
        """
        import_path = Path(import_path)
        
        if not import_path.exists():
            raise ConfigurationError(f"Import file not found: {import_path}")
        
        try:
            if import_path.suffix.lower() == ".json":
                with open(import_path) as f:
                    import_data = json.load(f)
            else:
                with open(import_path) as f:
                    import_data = yaml.safe_load(f)
            
            # Import user configuration
            if "user_config" in import_data:
                if merge_mode == "replace":
                    self.config_layers[ConfigPriority.USER_DEFAULT] = import_data["user_config"]
                elif merge_mode == "merge":
                    current_config = self.config_layers[ConfigPriority.USER_DEFAULT]
                    self.config_layers[ConfigPriority.USER_DEFAULT] = self._deep_merge_dict(
                        current_config, import_data["user_config"]
                    )
            
            # Import custom configuration
            if "custom_config" in import_data:
                if merge_mode == "replace":
                    self.config_layers[ConfigPriority.USER_CUSTOM] = import_data["custom_config"]
                elif merge_mode == "merge":
                    current_config = self.config_layers[ConfigPriority.USER_CUSTOM]
                    self.config_layers[ConfigPriority.USER_CUSTOM] = self._deep_merge_dict(
                        current_config, import_data["custom_config"]
                    )
            
            # Import profiles
            if "profiles" in import_data:
                profiles_data = import_data["profiles"]
                
                if merge_mode == "replace":
                    self.user_profiles = profiles_data.get("profiles", {})
                    self.active_profile = profiles_data.get("active_profile", "default")
                elif merge_mode == "merge":
                    imported_profiles = profiles_data.get("profiles", {})
                    for profile_name, profile_data in imported_profiles.items():
                        if profile_name not in self.user_profiles or merge_mode == "replace":
                            self.user_profiles[profile_name] = profile_data
            
            logger.info(f"Imported user configuration from {import_path}")
            
        except Exception as e:
            raise ConfigurationError(f"Failed to import configuration: {e}")
    
    def validate_user_config(self, config_name: str, profile: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate user configuration
        
        Args:
            config_name: Name of configuration to validate
            profile: Profile to validate (defaults to active profile)
            
        Returns:
            Dict[str, Any]: Validation results
        """
        effective_config = self.get_effective_config(config_name, profile)
        
        # Use the global validator
        return config_validator.get_validation_summary(config_name, effective_config)
    
    def get_config_diff(
        self, 
        config_name: str, 
        profile1: str, 
        profile2: str
    ) -> Dict[str, Any]:
        """
        Get differences between two profile configurations
        
        Args:
            config_name: Name of configuration to compare
            profile1: First profile
            profile2: Second profile
            
        Returns:
            Dict[str, Any]: Configuration differences
        """
        config1 = self.get_effective_config(config_name, profile1)
        config2 = self.get_effective_config(config_name, profile2)
        
        return self._compute_config_diff(config1, config2, f"{profile1} vs {profile2}")
    
    def _compute_config_diff(
        self, 
        config1: Dict[str, Any], 
        config2: Dict[str, Any],
        comparison_name: str
    ) -> Dict[str, Any]:
        """Compute differences between two configurations"""
        diff = {
            "comparison": comparison_name,
            "added": {},
            "removed": {},
            "changed": {},
            "unchanged": {},
        }
        
        all_keys = set(config1.keys()) | set(config2.keys())
        
        for key in all_keys:
            if key not in config1:
                diff["added"][key] = config2[key]
            elif key not in config2:
                diff["removed"][key] = config1[key]
            elif config1[key] != config2[key]:
                if isinstance(config1[key], dict) and isinstance(config2[key], dict):
                    # Recursive diff for nested dictionaries
                    nested_diff = self._compute_config_diff(
                        config1[key], config2[key], f"{comparison_name}.{key}"
                    )
                    diff["changed"][key] = nested_diff
                else:
                    diff["changed"][key] = {
                        "old_value": config1[key],
                        "new_value": config2[key],
                    }
            else:
                diff["unchanged"][key] = config1[key]
        
        return diff
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()


# Global user config manager instance
user_config_manager = UserConfigManager()