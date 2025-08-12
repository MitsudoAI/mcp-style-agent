# MCP Style Agent Collection 🧠

A collection of local MCP-style agents for cognitive enhancement, deep thinking, and systematic reasoning.

## Overview

This project implements multiple specialized MCP (Model Context Protocol) agents that work together to enhance human cognitive capabilities:

### 🧠 Deep Thinking Engine
A comprehensive framework for breaking cognitive limitations through:
- **Problem Decomposition**: Break complex questions into manageable sub-problems
- **Evidence Gathering**: Leverage LLM web search for multi-source evidence collection  
- **Multi-Agent Debate**: Organize structured debates from multiple perspectives
- **Critical Evaluation**: Apply Paul-Elder standards for rigorous thinking assessment
- **Bias Detection**: Identify and mitigate cognitive biases systematically
- **Innovation Methods**: Use SCAMPER/TRIZ for breakthrough thinking
- **Socratic Reflection**: Guide metacognitive awareness and self-assessment

## Project Structure

```
mcp-style-agent/
├── .kiro/                     # Kiro IDE specs and configurations
│   └── specs/                 # Feature specifications
├── src/                       # Source code
│   └── mcps/                  # MCP collection
│       ├── deep_thinking/     # Deep thinking engine
│       └── shared/            # Shared utilities
├── tests/                     # Test suites
└── docs/                      # Documentation
```

## Key Features

- 🔒 **Privacy-First**: Core reasoning runs locally, only search queries sent externally
- 🔧 **Pluggable Architecture**: YAML-configurable thinking flows and custom agents
- 📊 **Transparent Process**: Complete thinking traces with visualization
- 🎯 **Scientific Methods**: Based on cognitive science and learning research
- ⚡ **Optimized Performance**: Intelligent caching and async processing
- 🏗️ **Modular Design**: Shared components across multiple MCP agents

## Quick Start

```bash
# Install with uv
uv sync

# Initialize the system
uv run deep-thinking init

# Start a thinking session
uv run deep-thinking think "How can we solve climate change effectively?"
```

## MCP Server Deployment

The Deep Thinking Engine can be deployed as an MCP server for integration with MCP-compatible hosts like Cursor and Claude Desktop.

### Using uvx (Recommended)

```json
{
  "mcpServers": {
    "deep-thinking-engine": {
      "command": "uvx",
      "args": ["--from", "/path/to/mcp-style-agent", "deep-thinking-mcp-server"],
      "env": {
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### Test Deployment

```bash
# Test uvx deployment
make test-uvx

# Start MCP server locally
make mcp-server

# Validate configuration
make mcp-server-validate
```

For detailed deployment instructions, see [docs/deployment/README.md](docs/deployment/README.md).

## Development

```bash
# Setup development environment
uv sync --dev

# Run tests
uv run pytest

# Format code
uv run black .
uv run isort .
```

## Architecture

The system uses a multi-agent architecture with specialized roles:

- **Decomposer Agent**: Question analysis and breakdown
- **Evidence Seeker**: Multi-source information gathering
- **Debate Orchestrator**: Structured multi-perspective analysis
- **Critic Agent**: Paul-Elder standards evaluation
- **Bias Buster**: Cognitive bias detection and mitigation
- **Innovator Agent**: SCAMPER/TRIZ creative thinking
- **Reflector Agent**: Socratic questioning and metacognition

## License

MIT License - see LICENSE file for details.