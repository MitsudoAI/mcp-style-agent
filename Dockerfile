# Dockerfile for Deep Thinking MCP Server
# Multi-stage build for optimized production image

# Build stage
FROM python:3.12-slim as builder

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast Python package management
RUN pip install uv

# Set work directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install Python dependencies
RUN uv sync --frozen --no-dev

# Production stage
FROM python:3.12-slim as production

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r deepthinking && useradd -r -g deepthinking deepthinking

# Set work directory
WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY src/ src/
COPY config/ config/
COPY templates/ templates/
COPY scripts/ scripts/

# Create required directories
RUN mkdir -p data logs && \
    chown -R deepthinking:deepthinking /app

# Switch to non-root user
USER deepthinking

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.path.insert(0, 'src'); from mcps.deep_thinking.server import DeepThinkingMCPServer; print('OK')" || exit 1

# Expose port (if needed for future HTTP interface)
EXPOSE 8000

# Default command
CMD ["python", "scripts/start_mcp_server.py", "--log-level", "INFO"]