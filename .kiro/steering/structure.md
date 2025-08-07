# Project Structure & Organization

## Root Directory Layout

```
mcp-style-agent/
├── .kiro/                     # Kiro IDE configurations
│   └── specs/                 # Feature specifications and design docs
├── src/                       # Source code
│   └── mcps/                  # MCP collection namespace
├── tests/                     # Test suites (mirrors src structure)
├── config/                    # YAML configuration files
├── docs/                      # Documentation
├── examples/                  # Demo and example scripts
└── templates/                 # Template files
```

## Source Code Organization

### Core Structure
- `src/mcps/` - Main package namespace for all MCP agents
- `src/mcps/shared/` - Shared utilities across agents
- `src/mcps/deep_thinking/` - Deep thinking engine implementation

### Deep Thinking Engine Structure
```
src/mcps/deep_thinking/
├── agents/          # Specialized agent implementations
├── config/          # Configuration management
├── controllers/     # Flow control and orchestration  
├── data/           # Database and persistence
├── flows/          # Flow execution and state management
├── models/         # Pydantic data models
├── sessions/       # Session management
├── templates/      # Prompt templates and validation
├── tools/          # MCP tools and utilities
└── cli.py          # Command-line interface
```

## Configuration Patterns

- **System Config**: `config/system.yaml` - Global system settings
- **Flow Config**: `config/flows.yaml` - Thinking flow definitions
- **Agent Config**: Embedded in flow definitions or separate files
- **Hot Reload**: Configuration changes detected automatically

## Testing Structure

- Tests mirror the `src/` directory structure
- `tests/deep_thinking/` contains all deep thinking engine tests
- Test files prefixed with `test_` and follow pytest conventions
- Integration tests for complete workflows
- Unit tests for individual components

## Naming Conventions

- **Files**: Snake_case for Python files
- **Classes**: PascalCase (e.g., `FlowExecutor`, `TemplateManager`)
- **Functions/Methods**: Snake_case
- **Constants**: UPPER_SNAKE_CASE
- **Agents**: Descriptive names (e.g., `decomposer`, `evidence_seeker`)

## Key Directories

- `.kiro/specs/` - Feature specifications and design documents
- `docs/` - Background, cognitive science docs, and architecture
- `examples/` - Runnable demos and usage examples
- `templates/` - Jinja2 templates for various purposes

## Import Patterns

- Use absolute imports from `src/mcps/`
- Shared utilities imported from `mcps.shared`
- Agent-specific imports from respective agent modules
- Models imported from `models/` subdirectories