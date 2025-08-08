#!/usr/bin/env python3
"""
Startup script for Deep Thinking MCP Server

This script provides a convenient way to start the MCP server with
proper configuration and error handling.
"""

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mcps.deep_thinking.server import DeepThinkingMCPServer


def setup_logging(log_level: str = "INFO", log_file: str = None):
    """Setup logging configuration"""
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create logs directory if it doesn't exist
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file) if log_file else logging.NullHandler()
        ]
    )


def ensure_directories():
    """Ensure required directories exist"""
    directories = [
        "data",
        "logs",
        "config",
        "templates"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)


def validate_environment():
    """Validate the environment before starting the server"""
    # Check Python version
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required")
        sys.exit(1)
    
    # Check required directories
    ensure_directories()
    
    # Check if config file exists
    config_file = Path("config/mcp_server.yaml")
    if not config_file.exists():
        print(f"Warning: Config file {config_file} not found, using defaults")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Start Deep Thinking MCP Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/start_mcp_server.py
  python scripts/start_mcp_server.py --config config/custom.yaml
  python scripts/start_mcp_server.py --log-level DEBUG --log-file logs/debug.log
        """
    )
    
    parser.add_argument(
        "--config", "-c",
        type=str,
        help="Path to configuration file"
    )
    
    parser.add_argument(
        "--log-level", "-l",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level"
    )
    
    parser.add_argument(
        "--log-file", "-f",
        type=str,
        default="logs/mcp_server.log",
        help="Log file path"
    )
    
    parser.add_argument(
        "--validate-only", "-v",
        action="store_true",
        help="Only validate configuration and exit"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level, args.log_file)
    logger = logging.getLogger(__name__)
    
    try:
        # Validate environment
        validate_environment()
        logger.info("Environment validation passed")
        
        if args.validate_only:
            logger.info("Validation complete, exiting")
            return
        
        # Initialize and start server
        logger.info("Initializing Deep Thinking MCP Server...")
        server = DeepThinkingMCPServer(config_path=args.config)
        
        logger.info("Starting MCP Server...")
        logger.info("Server is ready to accept connections via stdio")
        logger.info("Press Ctrl+C to stop the server")
        
        await server.run()
        
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server startup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())