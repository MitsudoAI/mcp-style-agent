"""
Tests for user configuration management system
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.mcps.deep_thinking.config.exceptions import ConfigurationError
from src.mcps.deep_thinking.config.user_config_manager import ConfigPriority, UserConfigManager


class TestUserConfigManager(unittest.TestCase):
    """Test user configuration manager"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
        # Create separate directories for user and global configs
        self.user_config_dir = self.temp_path / "user"
        self.global_config_dir = self.temp_path / "global"
        
        self.user_config_dir.mkdir(parents=True)
        self.global_config_dir.mkdir(parents=True)
        
        # Create global config
        global_config = {
            "system": {
                "log_level": "INFO",
                "max_concurrent_agents": 10,
            },
            "agents": {
                "default_temperature": 0.7,
                "quality_threshold": 0.8,
            }
        }
        
        with open(self.global_config_dir / "system.yaml", "w") as f:
            yaml.dump({"system": global_config["system"]}, f)
        
        with open(self.global_config_dir / "agents.yaml", "w") as f:
            yaml.dump({"agents": global_config["agents"]}, f)
        
        self.manager = UserConfigManager(
            user_config_dir=self.user_config_dir,
            global_config_dir=self.global_config_dir
        )
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_initialization(self):
        """Test manager initialization"""
        async def run_test():
            await self.manager.initialize()
            
            # Check that directories were created
            self.assertTrue(self.user_config_dir.exists())
            
            # Check that default files were created
            self.assertTrue((self.user_config_dir / "config.yaml").exists())
            self.assertTrue((self.user_config_dir / "profiles.yaml").exists())
            
            # Check that system defaults were loaded
            system_defaults = self.manager.config_layers[ConfigPriority.SYSTEM_DEFAULT]
            self.assertIn("system", system_defaults)
            self.assertIn("agents", system_defaults)
        
        import asyncio
        asyncio.run(run_test())
    
    def test_config_priority_merging(self):
        """Test configuration priority and merging"""
        async def run_test():
            await self.manager.initialize()
            
            # Get effective system config
            effective_config = self.manager.get_effective_config("system")
            
            # Should have system defaults
            self.assertIn("log_level", effective_config)
            self.assertIn("max_concurrent_agents", effective_config)
            
            # Should have global config overrides
            self.assertEqual(effective_config["log_level"], "INFO")
            
            # Should have user config overrides (from default user config)
            # The default user config sets max_concurrent_agents to 8 (higher priority than global)
            self.assertEqual(effective_config["max_concurrent_agents"], 8)
        
        import asyncio
        asyncio.run(run_test())
    
    def test_user_preferences(self):
        """Test user preference management"""
        async def run_test():
            await self.manager.initialize()
            
            # Set a user preference
            self.manager.set_user_preference("system.log_level", "DEBUG")
            
            # Get the preference
            log_level = self.manager.get_user_preference("system.log_level")
            self.assertEqual(log_level, "DEBUG")
            
            # Get effective config should include the preference
            effective_config = self.manager.get_effective_config("system")
            self.assertEqual(effective_config["log_level"], "DEBUG")
        
        import asyncio
        asyncio.run(run_test())
    
    def test_profile_management(self):
        """Test user profile management"""
        async def run_test():
            await self.manager.initialize()
            
            # Create a new profile
            self.manager.create_profile(
                profile_name="test_profile",
                display_name="Test Profile",
                description="Profile for testing",
                config={
                    "system": {
                        "log_level": "DEBUG",
                        "max_concurrent_agents": 5,
                    }
                }
            )
            
            # Check that profile was created
            profiles = self.manager.get_profile_list()
            profile_names = [p["name"] for p in profiles]
            self.assertIn("test_profile", profile_names)
            
            # Get effective config with the profile
            effective_config = self.manager.get_effective_config("system", profile="test_profile")
            self.assertEqual(effective_config["log_level"], "DEBUG")
            self.assertEqual(effective_config["max_concurrent_agents"], 5)
            
            # Set active profile
            self.manager.set_active_profile("test_profile")
            self.assertEqual(self.manager.active_profile, "test_profile")
            
            # Get effective config should now use the active profile
            effective_config = self.manager.get_effective_config("system")
            self.assertEqual(effective_config["log_level"], "DEBUG")
        
        import asyncio
        asyncio.run(run_test())
    
    def test_profile_inheritance(self):
        """Test profile inheritance"""
        async def run_test():
            await self.manager.initialize()
            
            # Create base profile
            self.manager.create_profile(
                profile_name="base_profile",
                display_name="Base Profile",
                description="Base profile for inheritance",
                config={
                    "system": {
                        "log_level": "DEBUG",
                        "max_concurrent_agents": 5,
                    },
                    "agents": {
                        "default_temperature": 0.9,
                    }
                }
            )
            
            # Create derived profile
            self.manager.create_profile(
                profile_name="derived_profile",
                display_name="Derived Profile",
                description="Profile derived from base",
                base_profile="base_profile",
                config={
                    "system": {
                        "log_level": "WARNING",  # Override
                    },
                    "agents": {
                        "quality_threshold": 0.9,  # Add new setting
                    }
                }
            )
            
            # Get effective config for derived profile
            effective_config = self.manager.get_effective_config("system", profile="derived_profile")
            
            # Should have overridden value
            self.assertEqual(effective_config["log_level"], "WARNING")
            
            # Should have inherited value
            self.assertEqual(effective_config["max_concurrent_agents"], 5)
            
            # Check agents config
            agents_config = self.manager.get_effective_config("agents", profile="derived_profile")
            self.assertEqual(agents_config["default_temperature"], 0.9)  # Inherited
            self.assertEqual(agents_config["quality_threshold"], 0.9)    # Added
        
        import asyncio
        asyncio.run(run_test())
    
    def test_runtime_overrides(self):
        """Test runtime configuration overrides"""
        async def run_test():
            await self.manager.initialize()
            
            # Set up session and runtime overrides
            session_overrides = {
                "system": {
                    "max_concurrent_agents": 3,
                }
            }
            
            runtime_overrides = {
                "system": {
                    "log_level": "ERROR",
                }
            }
            
            # Get effective config with overrides
            effective_config = self.manager.get_effective_config(
                "system",
                session_overrides=session_overrides,
                runtime_overrides=runtime_overrides
            )
            
            # Should have runtime override (highest priority)
            self.assertEqual(effective_config["log_level"], "ERROR")
            
            # Should have session override
            self.assertEqual(effective_config["max_concurrent_agents"], 3)
        
        import asyncio
        asyncio.run(run_test())
    
    def test_config_export_import(self):
        """Test configuration export and import"""
        async def run_test():
            await self.manager.initialize()
            
            # Create a custom profile
            self.manager.create_profile(
                profile_name="export_test",
                display_name="Export Test Profile",
                description="Profile for export testing",
                config={
                    "system": {
                        "log_level": "DEBUG",
                    }
                }
            )
            
            # Set some user preferences
            self.manager.set_user_preference("agents.default_temperature", 0.9)
            
            # Export configuration
            export_file = self.temp_path / "exported_config.yaml"
            self.manager.export_config(export_file, include_profiles=True, format="yaml")
            
            self.assertTrue(export_file.exists())
            
            # Create a new manager and import
            new_manager = UserConfigManager(
                user_config_dir=self.temp_path / "new_user",
                global_config_dir=self.global_config_dir
            )
            await new_manager.initialize()
            
            # Import the configuration
            new_manager.import_config(export_file, merge_mode="replace")
            
            # Check that profile was imported
            profiles = new_manager.get_profile_list()
            profile_names = [p["name"] for p in profiles]
            self.assertIn("export_test", profile_names)
            
            # Check that preference was imported
            temp_value = new_manager.get_user_preference("agents.default_temperature")
            self.assertEqual(temp_value, 0.9)
        
        import asyncio
        asyncio.run(run_test())
    
    def test_config_validation(self):
        """Test configuration validation"""
        async def run_test():
            await self.manager.initialize()
            
            # Create profile with valid config
            self.manager.create_profile(
                profile_name="valid_profile",
                display_name="Valid Profile",
                description="Profile with valid configuration",
                config={
                    "system": {
                        "log_level": "INFO",
                        "max_concurrent_agents": 5,
                    }
                }
            )
            
            # Validate the configuration
            validation_result = self.manager.validate_user_config("system", profile="valid_profile")
            
            self.assertIn("is_valid", validation_result)
            self.assertIn("error_count", validation_result)
            self.assertIn("errors", validation_result)
        
        import asyncio
        asyncio.run(run_test())
    
    def test_config_diff(self):
        """Test configuration difference computation"""
        async def run_test():
            await self.manager.initialize()
            
            # Create two different profiles
            self.manager.create_profile(
                profile_name="profile1",
                display_name="Profile 1",
                description="First profile",
                config={
                    "system": {
                        "log_level": "INFO",
                        "max_concurrent_agents": 5,
                    }
                }
            )
            
            self.manager.create_profile(
                profile_name="profile2",
                display_name="Profile 2",
                description="Second profile",
                config={
                    "system": {
                        "log_level": "DEBUG",  # Different
                        "max_concurrent_agents": 5,  # Same
                        "debug_mode": True,  # Added
                    }
                }
            )
            
            # Get configuration diff
            diff = self.manager.get_config_diff("system", "profile1", "profile2")
            
            self.assertIn("comparison", diff)
            self.assertIn("added", diff)
            self.assertIn("removed", diff)
            self.assertIn("changed", diff)
            self.assertIn("unchanged", diff)
            
            # Check specific differences
            # debug_mode is in "changed" because it exists in both configs with different values
            self.assertIn("debug_mode", diff["changed"])
            self.assertIn("log_level", diff["changed"])
            self.assertIn("max_concurrent_agents", diff["unchanged"])
        
        import asyncio
        asyncio.run(run_test())
    
    def test_profile_deletion(self):
        """Test profile deletion"""
        async def run_test():
            await self.manager.initialize()
            
            # Create a profile
            self.manager.create_profile(
                profile_name="delete_me",
                display_name="Delete Me",
                description="Profile to be deleted",
                config={}
            )
            
            # Verify it exists
            profiles = self.manager.get_profile_list()
            profile_names = [p["name"] for p in profiles]
            self.assertIn("delete_me", profile_names)
            
            # Delete the profile
            self.manager.delete_profile("delete_me")
            
            # Verify it's gone
            profiles = self.manager.get_profile_list()
            profile_names = [p["name"] for p in profiles]
            self.assertNotIn("delete_me", profile_names)
            
            # Try to delete default profile (should fail)
            with self.assertRaises(ConfigurationError):
                self.manager.delete_profile("default")
        
        import asyncio
        asyncio.run(run_test())
    
    def test_inheritance_rules(self):
        """Test configuration inheritance rules"""
        async def run_test():
            await self.manager.initialize()
            
            # Test that inheritance rules are respected
            base_config = {"log_level": "INFO", "debug_mode": False}
            override_config = {"log_level": "DEBUG", "debug_mode": True}
            
            # Merge with system config rules
            merged = self.manager._merge_configs(base_config, override_config, "system")
            
            # Both fields should be merged since system config allows them
            self.assertEqual(merged["log_level"], "DEBUG")
            self.assertEqual(merged["debug_mode"], True)
        
        import asyncio
        asyncio.run(run_test())
    
    def test_deep_merge(self):
        """Test deep dictionary merging"""
        base_dict = {
            "level1": {
                "level2": {
                    "setting1": "value1",
                    "setting2": "value2",
                }
            }
        }
        
        override_dict = {
            "level1": {
                "level2": {
                    "setting2": "new_value2",  # Override
                    "setting3": "value3",     # Add
                }
            }
        }
        
        merged = self.manager._deep_merge_dict(base_dict, override_dict)
        
        # Check that deep merge worked correctly
        self.assertEqual(merged["level1"]["level2"]["setting1"], "value1")  # Preserved
        self.assertEqual(merged["level1"]["level2"]["setting2"], "new_value2")  # Overridden
        self.assertEqual(merged["level1"]["level2"]["setting3"], "value3")  # Added


def run_user_config_tests():
    """Run user configuration tests"""
    print("Running user configuration tests...")
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestUserConfigManager))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    if result.wasSuccessful():
        print(f"\n✅ All {result.testsRun} tests passed!")
        return True
    else:
        print(f"\n❌ {len(result.failures)} failures, {len(result.errors)} errors")
        for failure in result.failures:
            print(f"FAILURE: {failure[0]}")
            print(failure[1])
        for error in result.errors:
            print(f"ERROR: {error[0]}")
            print(error[1])
        return False


if __name__ == "__main__":
    success = run_user_config_tests()
    exit(0 if success else 1)