"""
Tests for configuration management system
"""

import asyncio
import json
import tempfile
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import yaml

from src.mcps.deep_thinking.config.config_manager import ConfigManager
from src.mcps.deep_thinking.config.config_validator import ConfigValidator
from src.mcps.deep_thinking.config.exceptions import ConfigurationError
from src.mcps.deep_thinking.config.hot_reload_manager import HotReloadManager
from src.mcps.deep_thinking.config.yaml_config_loader import YAMLConfigLoader


class TestYAMLConfigLoader:
    """Test YAML configuration loader"""

    def test_load_config_file_success(self, tmp_path):
        """Test successful config file loading"""
        loader = YAMLConfigLoader(tmp_path)

        # Create test config file
        config_data = {
            "system": {
                "log_level": "INFO",
                "max_concurrent_agents": 5,
            },
            "agents": {
                "default_temperature": 0.8,
            },
        }

        config_file = tmp_path / "test.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        # Load config
        loaded_config = loader.load_config_file(config_file)

        assert loaded_config == config_data

    def test_load_config_file_not_found(self, tmp_path):
        """Test loading non-existent config file"""
        loader = YAMLConfigLoader(tmp_path)

        with pytest.raises(ConfigurationError, match="Configuration file not found"):
            loader.load_config_file(tmp_path / "nonexistent.yaml")

    def test_load_config_file_invalid_yaml(self, tmp_path):
        """Test loading invalid YAML file"""
        loader = YAMLConfigLoader(tmp_path)

        # Create invalid YAML file
        config_file = tmp_path / "invalid.yaml"
        with open(config_file, "w") as f:
            f.write("invalid: yaml: content: [")

        with pytest.raises(ConfigurationError, match="Failed to parse YAML file"):
            loader.load_config_file(config_file)

    def test_load_all_configs(self, tmp_path):
        """Test loading all configuration files"""
        loader = YAMLConfigLoader(tmp_path)

        # Create system config
        system_config = {
            "system": {"log_level": "DEBUG"},
            "agents": {"default_temperature": 0.7},
        }
        with open(tmp_path / "system.yaml", "w") as f:
            yaml.dump(system_config, f)

        # Create flows config
        flows_config = {
            "test_flow": {
                "description": "Test flow",
                "steps": [{"agent": "decomposer", "name": "Test step"}],
            }
        }
        with open(tmp_path / "flows.yaml", "w") as f:
            yaml.dump(flows_config, f)

        # Create flows directory with additional flow
        flows_dir = tmp_path / "flows"
        flows_dir.mkdir()

        additional_flow = {
            "additional_flow": {
                "description": "Additional flow",
                "steps": [{"agent": "critic", "name": "Additional step"}],
            }
        }
        with open(flows_dir / "additional.yaml", "w") as f:
            yaml.dump(additional_flow, f)

        # Load all configs
        configs = loader.load_all_configs()

        assert "system" in configs
        assert "flows" in configs
        assert configs["system"] == system_config
        assert "test_flow" in configs["flows"]
        assert "additional_flow" in configs["flows"]

    def test_merge_with_defaults(self, tmp_path):
        """Test merging configuration with defaults"""
        loader = YAMLConfigLoader(tmp_path)

        config_data = {
            "system": {
                "log_level": "DEBUG",  # Override default
                "custom_setting": "value",  # New setting
            }
        }

        merged = loader.merge_with_defaults("system", config_data)

        # Should have both default and custom values
        assert merged["system"]["log_level"] == "DEBUG"  # Overridden
        assert merged["system"]["max_concurrent_agents"] == 10  # Default
        assert merged["system"]["custom_setting"] == "value"  # Custom

    def test_save_config_file(self, tmp_path):
        """Test saving configuration file"""
        loader = YAMLConfigLoader(tmp_path)

        config_data = {
            "test": {
                "setting1": "value1",
                "setting2": 42,
            }
        }

        # Save config
        saved_path = loader.save_config_file("test", config_data)

        assert saved_path.exists()
        assert saved_path == tmp_path / "test.yaml"

        # Verify content
        with open(saved_path) as f:
            loaded_data = yaml.safe_load(f)

        assert loaded_data == config_data

    def test_create_default_configs(self, tmp_path):
        """Test creating default configuration files"""
        loader = YAMLConfigLoader(tmp_path)

        # Create default configs
        loader.create_default_configs()

        # Check that files were created
        assert (tmp_path / "system.yaml").exists()
        assert (tmp_path / "flows.yaml").exists()

        # Verify content
        with open(tmp_path / "system.yaml") as f:
            system_config = yaml.safe_load(f)

        assert "system" in system_config
        assert "agents" in system_config
        assert system_config["system"]["log_level"] == "INFO"


class TestConfigValidator:
    """Test configuration validator"""

    def test_validate_system_config_valid(self):
        """Test validating valid system configuration"""
        validator = ConfigValidator()

        config_data = {
            "system": {
                "log_level": "INFO",
                "max_concurrent_agents": 5,
                "default_timeout": 300,
            },
            "agents": {
                "default_temperature": 0.7,
                "quality_threshold": 0.8,
            },
        }

        is_valid, errors = validator.validate_system_config(config_data)

        assert is_valid
        assert len(errors) == 0

    def test_validate_system_config_invalid_log_level(self):
        """Test validating system config with invalid log level"""
        validator = ConfigValidator()

        config_data = {
            "system": {
                "log_level": "INVALID",
            }
        }

        is_valid, errors = validator.validate_system_config(config_data)

        assert not is_valid
        assert any("Invalid log_level" in error for error in errors)

    def test_validate_system_config_invalid_numeric_range(self):
        """Test validating system config with invalid numeric values"""
        validator = ConfigValidator()

        config_data = {
            "system": {
                "max_concurrent_agents": 0,  # Too low
                "default_timeout": 5000,  # Too high
            }
        }

        is_valid, errors = validator.validate_system_config(config_data)

        assert not is_valid
        assert any(
            "max_concurrent_agents must be between 1 and 100" in error
            for error in errors
        )
        assert any(
            "default_timeout must be between 1 and 3600" in error for error in errors
        )

    def test_validate_flows_config_valid(self):
        """Test validating valid flows configuration"""
        validator = ConfigValidator()

        config_data = {
            "test_flow": {
                "description": "Test flow",
                "version": "1.0",
                "steps": [
                    {
                        "agent": "decomposer",
                        "name": "Problem Decomposition",
                        "config": {
                            "max_sub_questions": 5,
                        },
                    },
                    {
                        "agent": "critic",
                        "name": "Critical Evaluation",
                        "config": {
                            "standards": "paul_elder_full",
                        },
                    },
                ],
            }
        }

        is_valid, errors = validator.validate_flows_config(config_data)

        assert is_valid
        assert len(errors) == 0

    def test_validate_flows_config_empty(self):
        """Test validating empty flows configuration"""
        validator = ConfigValidator()

        config_data = {}

        is_valid, errors = validator.validate_flows_config(config_data)

        assert not is_valid
        assert any("cannot be empty" in error for error in errors)

    def test_validate_flows_config_invalid_agent(self):
        """Test validating flows config with invalid agent type"""
        validator = ConfigValidator()

        config_data = {
            "test_flow": {
                "description": "Test flow",
                "steps": [
                    {
                        "agent": "invalid_agent",
                        "name": "Invalid step",
                    }
                ],
            }
        }

        is_valid, errors = validator.validate_flows_config(config_data)

        assert not is_valid
        assert any("unknown agent: invalid_agent" in error for error in errors)

    def test_validate_flows_config_duplicate_step_names(self):
        """Test validating flows config with duplicate step names"""
        validator = ConfigValidator()

        config_data = {
            "test_flow": {
                "description": "Test flow",
                "steps": [
                    {
                        "agent": "decomposer",
                        "name": "Duplicate Name",
                    },
                    {
                        "agent": "critic",
                        "name": "Duplicate Name",
                    },
                ],
            }
        }

        is_valid, errors = validator.validate_flows_config(config_data)

        assert not is_valid
        assert any("duplicate step name" in error for error in errors)

    def test_validate_flows_config_invalid_reference(self):
        """Test validating flows config with invalid reference"""
        validator = ConfigValidator()

        config_data = {
            "test_flow": {
                "description": "Test flow",
                "steps": [
                    {
                        "agent": "evidence_seeker",
                        "name": "Evidence Collection",
                        "for_each": "nonexistent_agent.results",
                    }
                ],
            }
        }

        is_valid, errors = validator.validate_flows_config(config_data)

        assert not is_valid
        assert any("references undefined agent" in error for error in errors)

    def test_get_validation_summary(self):
        """Test getting validation summary"""
        validator = ConfigValidator()

        config_data = {
            "system": {
                "log_level": "INVALID",
            }
        }

        summary = validator.get_validation_summary("system", config_data)

        assert summary["config_name"] == "system"
        assert not summary["is_valid"]
        assert summary["error_count"] > 0
        assert len(summary["errors"]) > 0
        assert "validation_timestamp" in summary


class TestHotReloadManager:
    """Test hot reload manager"""

    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary config directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def yaml_loader(self, temp_config_dir):
        """Create YAML loader for testing"""
        return YAMLConfigLoader(temp_config_dir)

    @pytest.fixture
    def hot_reload_manager(self, temp_config_dir, yaml_loader):
        """Create hot reload manager for testing"""
        return HotReloadManager(temp_config_dir, yaml_loader)

    @pytest.mark.asyncio
    async def test_initialize(self, hot_reload_manager, temp_config_dir):
        """Test hot reload manager initialization"""
        # Create test config file
        config_data = {"system": {"log_level": "INFO"}}
        with open(temp_config_dir / "system.yaml", "w") as f:
            yaml.dump(config_data, f)

        await hot_reload_manager.initialize()

        assert hot_reload_manager.is_monitoring
        assert "system" in hot_reload_manager.get_all_configs()

        await hot_reload_manager.cleanup()

    @pytest.mark.asyncio
    async def test_reload_callbacks(self, hot_reload_manager, temp_config_dir):
        """Test reload callbacks"""
        callback_called = False
        callback_config_name = None
        callback_config_data = None

        def test_callback(config_name, config_data):
            nonlocal callback_called, callback_config_name, callback_config_data
            callback_called = True
            callback_config_name = config_name
            callback_config_data = config_data

        hot_reload_manager.add_reload_callback(test_callback)

        # Initialize to start monitoring
        await hot_reload_manager.initialize()

        # Simulate config reload
        config_data = {"system": {"log_level": "DEBUG"}}
        await hot_reload_manager._notify_reload_callbacks("system", config_data)

        assert callback_called
        assert callback_config_name == "system"
        assert callback_config_data == config_data

        await hot_reload_manager.cleanup()

    @pytest.mark.asyncio
    async def test_error_callbacks(self, hot_reload_manager):
        """Test error callbacks"""
        callback_called = False
        callback_config_name = None
        callback_error = None

        def test_error_callback(config_name, error):
            nonlocal callback_called, callback_config_name, callback_error
            callback_called = True
            callback_config_name = config_name
            callback_error = error

        hot_reload_manager.add_error_callback(test_error_callback)

        # Simulate error
        test_error = ConfigurationError("Test error")
        await hot_reload_manager._notify_error_callbacks("system", test_error)

        assert callback_called
        assert callback_config_name == "system"
        assert callback_error == test_error

    @pytest.mark.asyncio
    async def test_force_reload(self, hot_reload_manager, temp_config_dir):
        """Test force reload functionality"""
        # Create initial config
        config_data = {"system": {"log_level": "INFO"}}
        with open(temp_config_dir / "system.yaml", "w") as f:
            yaml.dump(config_data, f)

        await hot_reload_manager.initialize()

        # Modify config file
        new_config_data = {"system": {"log_level": "DEBUG"}}
        with open(temp_config_dir / "system.yaml", "w") as f:
            yaml.dump(new_config_data, f)

        # Force reload
        await hot_reload_manager.force_reload("system")

        # Check that config was reloaded
        current_config = hot_reload_manager.get_current_config("system")
        assert current_config["system"]["log_level"] == "DEBUG"

        await hot_reload_manager.cleanup()


class TestConfigManager:
    """Test configuration manager"""

    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary config directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def config_manager(self, temp_config_dir):
        """Create config manager for testing"""
        return ConfigManager(temp_config_dir)

    @pytest.mark.asyncio
    async def test_initialize(self, config_manager, temp_config_dir):
        """Test config manager initialization"""
        await config_manager.initialize()

        assert config_manager.config_dir.exists()
        assert config_manager.hot_reload_manager.is_monitoring
        assert len(config_manager.config_data) > 0

        await config_manager.cleanup()

    @pytest.mark.asyncio
    async def test_get_config(self, config_manager, temp_config_dir):
        """Test getting configuration"""
        # Create test config
        config_data = {"system": {"log_level": "INFO"}}
        with open(temp_config_dir / "system.yaml", "w") as f:
            yaml.dump(config_data, f)

        await config_manager.initialize()

        system_config = config_manager.get_config("system")
        assert system_config is not None
        assert system_config["system"]["log_level"] == "INFO"

        await config_manager.cleanup()

    @pytest.mark.asyncio
    async def test_get_nested_config(self, config_manager, temp_config_dir):
        """Test getting nested configuration"""
        # Create test config
        config_data = {
            "system": {"log_level": "INFO", "nested": {"deep_value": "test"}}
        }
        with open(temp_config_dir / "system.yaml", "w") as f:
            yaml.dump(config_data, f)

        await config_manager.initialize()

        log_level = config_manager.get_nested_config("system.log_level")
        assert log_level == "INFO"

        deep_value = config_manager.get_nested_config("system.nested.deep_value")
        assert deep_value == "test"

        missing_value = config_manager.get_nested_config("system.missing", "default")
        assert missing_value == "default"

        await config_manager.cleanup()

    @pytest.mark.asyncio
    async def test_validate_config(self, config_manager, temp_config_dir):
        """Test configuration validation"""
        # Create valid config
        config_data = {
            "system": {
                "log_level": "INFO",
                "max_concurrent_agents": 5,
            }
        }
        with open(temp_config_dir / "system.yaml", "w") as f:
            yaml.dump(config_data, f)

        await config_manager.initialize()

        # Should validate successfully
        assert config_manager.validate_config("system")

        # Test validation with invalid data
        invalid_config = {
            "system": {
                "log_level": "INVALID",
            }
        }

        with pytest.raises(ConfigurationError, match="validation failed"):
            config_manager.validate_config("system", invalid_config)

        await config_manager.cleanup()

    @pytest.mark.asyncio
    async def test_save_config_with_validation(self, config_manager, temp_config_dir):
        """Test saving configuration with validation"""
        await config_manager.initialize()

        # Valid config should save successfully
        valid_config = {
            "system": {
                "log_level": "DEBUG",
                "max_concurrent_agents": 8,
            }
        }

        await config_manager.save_config_with_validation("system", valid_config)

        # Check that file was saved
        config_file = temp_config_dir / "system.yaml"
        assert config_file.exists()

        # Check content
        with open(config_file) as f:
            saved_data = yaml.safe_load(f)
        assert saved_data == valid_config

        # Invalid config should raise error
        invalid_config = {
            "system": {
                "log_level": "INVALID",
            }
        }

        with pytest.raises(ConfigurationError, match="validation failed"):
            await config_manager.save_config_with_validation("system", invalid_config)

        await config_manager.cleanup()

    @pytest.mark.asyncio
    async def test_hot_reload_callback(self, config_manager, temp_config_dir):
        """Test hot reload callback handling"""
        callback_called = False
        callback_config_name = None

        def test_callback(config_name, config_data):
            nonlocal callback_called, callback_config_name
            callback_called = True
            callback_config_name = config_name

        config_manager.add_reload_callback(test_callback)

        await config_manager.initialize()

        # Simulate hot reload
        config_manager._on_hot_reload("system", {"test": "data"})

        assert callback_called
        assert callback_config_name == "system"

        await config_manager.cleanup()

    @pytest.mark.asyncio
    async def test_backup_config(self, config_manager, temp_config_dir):
        """Test configuration backup"""
        # Create test config
        config_data = {"system": {"log_level": "INFO"}}
        with open(temp_config_dir / "system.yaml", "w") as f:
            yaml.dump(config_data, f)

        await config_manager.initialize()

        # Create backup
        backup_path = config_manager.backup_config("system")

        assert backup_path is not None
        assert backup_path.exists()
        assert "backup" in backup_path.name

        # Verify backup content
        with open(backup_path) as f:
            backup_data = yaml.safe_load(f)
        assert backup_data == config_data

        await config_manager.cleanup()


@pytest.mark.asyncio
async def test_integration_config_management(tmp_path):
    """Integration test for complete configuration management system"""
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    # Create initial configurations
    system_config = {
        "system": {
            "log_level": "INFO",
            "max_concurrent_agents": 5,
        },
        "agents": {
            "default_temperature": 0.7,
        },
    }

    flows_config = {
        "test_flow": {
            "description": "Test flow",
            "version": "1.0",
            "steps": [
                {
                    "agent": "decomposer",
                    "name": "Problem Decomposition",
                    "config": {"max_sub_questions": 3},
                },
                {
                    "agent": "critic",
                    "name": "Critical Evaluation",
                    "config": {"standards": "paul_elder_basic"},
                },
            ],
        }
    }

    with open(config_dir / "system.yaml", "w") as f:
        yaml.dump(system_config, f)

    with open(config_dir / "flows.yaml", "w") as f:
        yaml.dump(flows_config, f)

    # Initialize config manager
    config_manager = ConfigManager(config_dir)
    await config_manager.initialize()

    try:
        # Test loading configurations
        assert config_manager.get_config("system") is not None
        assert config_manager.get_config("flows") is not None

        # Test nested access
        log_level = config_manager.get_nested_config("system.log_level")
        assert log_level == "INFO"

        # Test validation
        assert config_manager.validate_config("system")
        assert config_manager.validate_config("flows")

        # Test validation summary
        summary = config_manager.get_validation_summary("flows")
        assert summary["is_valid"]
        assert summary["error_count"] == 0

        # Test configuration update
        new_system_config = {
            "system": {
                "log_level": "DEBUG",
                "max_concurrent_agents": 8,
            }
        }

        await config_manager.save_config_with_validation("system", new_system_config)

        # Verify update
        updated_config = config_manager.get_config("system")
        assert updated_config["system"]["log_level"] == "DEBUG"

        # Test backup functionality
        backup_path = config_manager.backup_config("system")
        assert backup_path is not None
        assert backup_path.exists()

    finally:
        await config_manager.cleanup()


if __name__ == "__main__":
    pytest.main([__file__])
