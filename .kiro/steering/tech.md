# Technology Stack & Build System

## Core Technologies

- **Python 3.12+** - Primary language with modern type hints
- **Pydantic 2.0+** - Data validation and settings management
- **SQLAlchemy 2.0+** - Database ORM for session and data persistence
- **PyYAML** - Configuration management for flows and system settings
- **Click** - CLI interface framework
- **Rich** - Enhanced terminal output and formatting
- **Jinja2** - Template engine for dynamic prompt generation
- **Watchdog** - File system monitoring for hot reload

## Development Tools

- **uv** - Fast Python package manager and project management
- **pytest** - Testing framework with async support
- **black** - Code formatting (line length: 88)
- **isort** - Import sorting with black profile
- **ruff** - Fast Python linter
- **mypy** - Static type checking (currently being integrated)

## Architecture Patterns

- **Multi-Agent System** - Specialized agents with defined roles
- **YAML-Driven Configuration** - Declarative flow definitions
- **Template-Based Prompts** - Reusable prompt templates with parameter replacement
- **State Machine Pattern** - Flow execution with state transitions
- **Plugin Architecture** - Extensible agent and tool system
- **Hot Reload** - Configuration changes without restart

## Common Commands

```bash
# Development setup
make dev-install          # Install with dev dependencies
make install-and-refresh  # Install and refresh UVX cache

# Code quality
make format              # Format with black and isort
make lint               # Run ruff, black, and isort checks
make test               # Run pytest suite
make check              # Run all quality checks

# Deep thinking specific
make deep-thinking-init  # Initialize the engine
make deep-thinking-demo  # Run demo session

# Build and release
make build              # Build Python package
make clean              # Clean build artifacts
make all                # Complete development workflow
```

## Project Scripts

- `deep-thinking` - Main CLI entry point for the thinking engine
- Core interfaces available via `uv run python examples/core_interfaces_demo.py`