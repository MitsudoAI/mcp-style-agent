"""
Basic tests for configuration management system using unittest
"""

import asyncio
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.mcps.deep_thinking.config.config_validator import ConfigValidator
from src.mcps.deep_thinking.config.exceptions import ConfigurationError
from src.mcps.deep_thinking.config.yaml_config_loader import YAMLConfigLoader


class TestYAMLConfigLoader(unittest.TestCase):
    """Test YAML configuration loader"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        self.loader = YAMLConfigLoader(self.temp_path)
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_load_config_file_success(self):
        """Test successful config file loading"""
        # Create test config file
        config_data = {
            "system": {
                "log_level": "INFO",
                "max_concurrent_agents": 5,
            },
            "agents": {
                "default_temperature": 0.8,
            }
        }
        
        config_file = self.temp_path / "test.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)
        
        # Load config
        loaded_config = self.loader.load_config_file(config_file)
        
        self.assertEqual(loaded_config, config_data)
    
    def test_load_config_file_not_found(self):
        """Test loading non-existent config file"""
        with self.assertRaises(ConfigurationError):
            self.loader.load_config_file(self.temp_path / "nonexistent.yaml")
    
    def test_merge_with_defaults(self):
        """Test merging configuration with defaults"""
        config_data = {
            "system": {
                "log_level": "DEBUG",  # Override default
                "custom_setting": "value",  # New setting
            }
        }
        
        merged = self.loader.merge_with_defaults("system", config_data)
        
        # Should have both default and custom values
        self.assertEqual(merged["system"]["log_level"], "DEBUG")  # Overridden
        self.assertEqual(merged["system"]["max_concurrent_agents"], 10)  # Default
        self.assertEqual(merged["system"]["custom_setting"], "value")  # Custom
    
    def test_save_config_file(self):
        """Test saving configuration file"""
        config_data = {
            "test": {
                "setting1": "value1",
                "setting2": 42,
            }
        }
        
        # Save config
        saved_path = self.loader.save_config_file("test", config_data)
        
        self.assertTrue(saved_path.exists())
        self.assertEqual(saved_path, self.temp_path / "test.yaml")
        
        # Verify content
        with open(saved_path) as f:
            loaded_data = yaml.safe_load(f)
        
        self.assertEqual(loaded_data, config_data)
    
    def test_create_default_configs(self):
        """Test creating default configuration files"""
        # Create default configs
        self.loader.create_default_configs()
        
        # Check that files were created
        self.assertTrue((self.temp_path / "system.yaml").exists())
        self.assertTrue((self.temp_path / "flows.yaml").exists())
        
        # Verify content
        with open(self.temp_path / "system.yaml") as f:
            system_config = yaml.safe_load(f)
        
        self.assertIn("system", system_config)
        self.assertIn("agents", system_config)
        self.assertEqual(system_config["system"]["log_level"], "INFO")


class TestConfigValidator(unittest.TestCase):
    """Test configuration validator"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.validator = ConfigValidator()
    
    def test_validate_system_config_valid(self):
        """Test validating valid system configuration"""
        config_data = {
            "system": {
                "log_level": "INFO",
                "max_concurrent_agents": 5,
                "default_timeout": 300,
            },
            "agents": {
                "default_temperature": 0.7,
                "quality_threshold": 0.8,
            }
        }
        
        is_valid, errors = self.validator.validate_system_config(config_data)
        
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
    
    def test_validate_system_config_invalid_log_level(self):
        """Test validating system config with invalid log level"""
        config_data = {
            "system": {
                "log_level": "INVALID",
            }
        }
        
        is_valid, errors = self.validator.validate_system_config(config_data)
        
        self.assertFalse(is_valid)
        self.assertTrue(any("Invalid log_level" in error for error in errors))
    
    def test_validate_flows_config_valid(self):
        """Test validating valid flows configuration"""
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
                        }
                    },
                    {
                        "agent": "critic",
                        "name": "Critical Evaluation",
                        "config": {
                            "standards": "paul_elder_full",
                        }
                    }
                ]
            }
        }
        
        is_valid, errors = self.validator.validate_flows_config(config_data)
        
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
    
    def test_validate_flows_config_empty(self):
        """Test validating empty flows configuration"""
        config_data = {}
        
        is_valid, errors = self.validator.validate_flows_config(config_data)
        
        self.assertFalse(is_valid)
        self.assertTrue(any("cannot be empty" in error for error in errors))
    
    def test_validate_flows_config_invalid_agent(self):
        """Test validating flows config with invalid agent type"""
        config_data = {
            "test_flow": {
                "description": "Test flow",
                "steps": [
                    {
                        "agent": "invalid_agent",
                        "name": "Invalid step",
                    }
                ]
            }
        }
        
        is_valid, errors = self.validator.validate_flows_config(config_data)
        
        self.assertFalse(is_valid)
        self.assertTrue(any("unknown agent: invalid_agent" in error for error in errors))
    
    def test_get_validation_summary(self):
        """Test getting validation summary"""
        config_data = {
            "system": {
                "log_level": "INVALID",
            }
        }
        
        summary = self.validator.get_validation_summary("system", config_data)
        
        self.assertEqual(summary["config_name"], "system")
        self.assertFalse(summary["is_valid"])
        self.assertGreater(summary["error_count"], 0)
        self.assertGreater(len(summary["errors"]), 0)
        self.assertIn("validation_timestamp", summary)


def run_basic_tests():
    """Run basic configuration tests"""
    print("Running basic configuration management tests...")
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTest(unittest.makeSuite(TestYAMLConfigLoader))
    suite.addTest(unittest.makeSuite(TestConfigValidator))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    if result.wasSuccessful():
        print(f"\n✅ All {result.testsRun} tests passed!")
        return True
    else:
        print(f"\n❌ {len(result.failures)} failures, {len(result.errors)} errors")
        return False


if __name__ == "__main__":
    success = run_basic_tests()
    exit(0 if success else 1)