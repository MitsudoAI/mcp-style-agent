#!/usr/bin/env python3
"""
Test script for uvx deployment of Deep Thinking MCP Server

This script tests whether the MCP server can be properly started using uvx
and validates the basic functionality.
"""

import asyncio
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path


def test_uvx_installation():
    """Test if uvx is installed and available"""
    try:
        result = subprocess.run(["uvx", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ uvx is installed: {result.stdout.strip()}")
            return True
        else:
            print("❌ uvx is not working properly")
            return False
    except FileNotFoundError:
        print("❌ uvx is not installed")
        print("Please install uv first: https://docs.astral.sh/uv/getting-started/installation/")
        return False


def test_package_installation():
    """Test if the package can be installed via uvx"""
    project_root = Path(__file__).parent.parent
    
    try:
        # Test installation from local path
        cmd = ["uvx", "--from", str(project_root), "deep-thinking-mcp-server", "--help"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Package can be installed and executed via uvx")
            print(f"Command output: {result.stdout[:200]}...")
            return True
        else:
            print("❌ Package installation failed")
            print(f"Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Package installation timed out")
        return False
    except Exception as e:
        print(f"❌ Package installation error: {e}")
        return False


def test_mcp_server_startup():
    """Test if the MCP server can start properly"""
    project_root = Path(__file__).parent.parent
    
    try:
        # Create a temporary config for testing
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            test_config = {
                "mcpServers": {
                    "deep-thinking-engine": {
                        "command": "uvx",
                        "args": ["--from", str(project_root), "deep-thinking-mcp-server", "--validate-only"],
                        "env": {
                            "LOG_LEVEL": "INFO"
                        }
                    }
                }
            }
            json.dump(test_config, f, indent=2)
            config_path = f.name
        
        # Test server validation
        cmd = ["uvx", "--from", str(project_root), "deep-thinking-mcp-server", "--validate-only"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        
        # Clean up temp file
        Path(config_path).unlink()
        
        if result.returncode == 0:
            print("✅ MCP server validation passed")
            return True
        else:
            print("❌ MCP server validation failed")
            print(f"Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ MCP server startup timed out")
        return False
    except Exception as e:
        print(f"❌ MCP server startup error: {e}")
        return False


def generate_sample_configs():
    """Generate sample MCP client configurations"""
    project_root = Path(__file__).parent.parent
    
    configs = {
        "local_development": {
            "mcpServers": {
                "deep-thinking-engine": {
                    "command": "uvx",
                    "args": ["--from", str(project_root), "deep-thinking-mcp-server"],
                    "env": {
                        "LOG_LEVEL": "DEBUG",
                        "DATA_DIR": str(project_root / "data")
                    }
                }
            }
        },
        "production": {
            "mcpServers": {
                "deep-thinking-engine": {
                    "command": "uvx",
                    "args": ["--from", "mcp-style-agent", "deep-thinking-mcp-server"],
                    "env": {
                        "LOG_LEVEL": "INFO"
                    }
                }
            }
        },
        "git_repository": {
            "mcpServers": {
                "deep-thinking-engine": {
                    "command": "uvx",
                    "args": ["--from", "git+https://github.com/your-org/mcp-style-agent.git", "deep-thinking-mcp-server"],
                    "env": {
                        "LOG_LEVEL": "INFO"
                    }
                }
            }
        }
    }
    
    print("\n📋 Sample MCP Client Configurations:")
    print("=" * 50)
    
    for name, config in configs.items():
        print(f"\n{name.upper()}:")
        print(json.dumps(config, indent=2))


def main():
    """Main test function"""
    print("🧪 Testing uvx deployment for Deep Thinking MCP Server")
    print("=" * 60)
    
    tests = [
        ("uvx Installation", test_uvx_installation),
        ("Package Installation", test_package_installation),
        ("MCP Server Startup", test_mcp_server_startup),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 Testing {test_name}...")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n📊 Test Results Summary:")
    print("=" * 30)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nPassed: {passed}/{len(results)} tests")
    
    if passed == len(results):
        print("\n🎉 All tests passed! uvx deployment is ready.")
        generate_sample_configs()
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()