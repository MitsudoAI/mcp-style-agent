# Deep Thinking Engine - 部署指南

本文档提供了Deep Thinking Engine MCP Server的完整部署方案，支持本地部署和Docker容器化部署。

## 概述

Deep Thinking Engine是一个零成本的本地MCP Server，专为Cursor等MCP Host设计。它遵循智能分工原则：
- **MCP Host端LLM**: 负责智能生成和推理
- **MCP Server端**: 提供流程控制和Prompt模板管理，零LLM API调用

## 系统要求

### 基础要求
- **Python**: 3.8+ (推荐3.12+)
- **操作系统**: Linux, macOS, Windows
- **内存**: 最小256MB，推荐512MB
- **存储**: 最小100MB可用空间

### Docker部署要求
- **Docker**: 20.10+
- **Docker Compose**: 2.0+

## 快速开始

### 1. 克隆项目
```bash
git clone <repository-url>
cd mcp-style-agent
```

### 2. 一键部署
```bash
# Docker部署（推荐）
./scripts/deploy.sh

# 本地部署
./scripts/deploy.sh -m local

# 同时部署两种方式
./scripts/deploy.sh -m both -b
```

## 部署方式

### Docker部署（推荐）

Docker部署提供了最佳的隔离性和可移植性。

#### 使用Docker Compose
```bash
# 构建并启动服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

#### 使用部署脚本
```bash
# 基础部署
./scripts/deploy.sh

# 清理后部署
./scripts/deploy.sh -c

# 备份后部署
./scripts/deploy.sh -b
```

#### Docker配置

**资源限制**:
- 内存限制: 512MB
- CPU限制: 0.5核心
- 内存预留: 256MB
- CPU预留: 0.25核心

**数据持久化**:
- 数据库: `./data:/app/data`
- 日志: `./logs:/app/logs`
- 配置: `./config:/app/config:ro`
- 模板: `./templates:/app/templates:ro`

### 本地部署

本地部署适合开发和调试环境。

#### 使用uv（推荐）

uv是现代Python包管理器，提供更快的依赖解析和虚拟环境管理。

```bash
# 安装uv
pip install uv

# 安装依赖
uv sync

# 启动服务器
uv run python scripts/start_mcp_server.py
```

**为什么使用 `uv run`？**
- 自动管理项目虚拟环境
- 确保使用正确的Python版本和依赖
- 无需手动激活虚拟环境
- 更好的依赖隔离和版本管理

**项目CLI命令**：
```bash
# 使用项目定义的CLI命令
uv run deep-thinking --help

# 或直接运行脚本
uv run python scripts/start_mcp_server.py
```

#### 使用pip
```bash
# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# 或
.venv\Scripts\activate     # Windows

# 安装依赖
pip install -e .

# 启动服务器
python scripts/start_mcp_server.py
```

## 配置

### 服务器配置

主配置文件: `config/mcp_server.yaml`

```yaml
server:
  name: "deep-thinking-engine"
  version: "0.1.0"
  runtime:
    log_level: "INFO"
    max_sessions: 100
    session_timeout_minutes: 60

database:
  type: "sqlite"
  path: "data/deep_thinking.db"

templates:
  base_path: "templates"
  cache_enabled: true
  hot_reload: true

flows:
  default_flow: "comprehensive_analysis"
  quality_gates:
    enabled: true
    default_threshold: 0.7
```

### 环境变量

| 变量名 | 默认值 | 描述 |
|--------|--------|------|
| `LOG_LEVEL` | `INFO` | 日志级别 |
| `CONFIG_PATH` | `config/mcp_server.yaml` | 配置文件路径 |
| `DATA_DIR` | `data` | 数据目录 |
| `TEMPLATE_DIR` | `templates` | 模板目录 |

### 启动参数

```bash
uv run python scripts/start_mcp_server.py [OPTIONS]

选项:
  -c, --config PATH     配置文件路径
  -l, --log-level LEVEL 日志级别 (DEBUG|INFO|WARNING|ERROR)
  -f, --log-file PATH   日志文件路径
  -v, --validate-only   仅验证配置并退出
```

## MCP客户端配置

### 使用 uvx 部署（推荐）

`uvx` 是最符合 MCP 客户端最佳实践的部署方式，提供更好的依赖隔离和版本管理。

#### 方式1: 使用已发布的包（推荐）

如果项目已发布到 PyPI：

```json
{
  "mcpServers": {
    "deep-thinking-engine": {
      "command": "uvx",
      "args": ["--from", "mcp-style-agent", "deep-thinking-mcp-server"],
      "env": {
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

#### 方式2: 使用本地项目路径

对于本地开发或未发布的版本：

```json
{
  "mcpServers": {
    "deep-thinking-engine": {
      "command": "uvx",
      "args": ["--from", "/path/to/mcp-style-agent", "deep-thinking-mcp-server"],
      "env": {
        "LOG_LEVEL": "INFO",
        "DATA_DIR": "/path/to/mcp-style-agent/data"
      }
    }
  }
}
```

**注意**: 使用 `deep-thinking-mcp-server` 命令而不是 `deep-thinking`，这是专门为 MCP 服务器设计的入口点。

#### 方式3: 使用 Git 仓库

直接从 Git 仓库安装：

```json
{
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
```

### 传统 uv run 方式

如果需要使用传统方式或进行开发调试：

#### Cursor配置

```json
{
  "mcpServers": {
    "deep-thinking-engine": {
      "command": "uv",
      "args": ["run", "python", "scripts/start_mcp_server.py"],
      "cwd": "/path/to/mcp-style-agent",
      "env": {
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

#### Claude Desktop配置

```json
{
  "mcpServers": {
    "deep-thinking-engine": {
      "command": "uv",
      "args": ["run", "python", "/path/to/mcp-style-agent/scripts/start_mcp_server.py"],
      "cwd": "/path/to/mcp-style-agent",
      "env": {
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### 配置说明

**uvx 的优势**：
- 自动管理虚拟环境和依赖
- 更好的版本隔离
- 符合 MCP 客户端最佳实践
- 支持从多种源安装（PyPI、Git、本地路径）
- 无需手动管理项目路径

**环境变量**：
- `LOG_LEVEL`: 日志级别（DEBUG、INFO、WARNING、ERROR）
- `DATA_DIR`: 数据目录路径（仅本地路径方式需要）
- `CONFIG_PATH`: 自定义配置文件路径

**路径配置**：
- 使用绝对路径确保配置的可靠性
- 本地路径方式需要指定 `DATA_DIR` 环境变量
- Git 和 PyPI 方式会自动处理数据目录

### 完整配置示例

#### 生产环境配置（推荐）

适用于稳定的生产环境，使用已发布的包：

```json
{
  "mcpServers": {
    "deep-thinking-engine": {
      "command": "uvx",
      "args": ["--from", "mcp-style-agent", "deep-thinking-mcp-server"],
      "env": {
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

#### 开发环境配置

适用于本地开发和测试：

```json
{
  "mcpServers": {
    "deep-thinking-engine": {
      "command": "uvx",
      "args": [
        "--from", "/Users/username/projects/mcp-style-agent", 
        "deep-thinking-mcp-server",
        "--log-level", "DEBUG",
        "--log-file", "logs/mcp_debug.log"
      ],
      "env": {
        "LOG_LEVEL": "DEBUG",
        "DATA_DIR": "/Users/username/projects/mcp-style-agent/data"
      }
    }
  }
}
```

#### 多实例配置

运行多个不同配置的实例：

```json
{
  "mcpServers": {
    "deep-thinking-main": {
      "command": "uvx",
      "args": ["--from", "mcp-style-agent", "deep-thinking-mcp-server"],
      "env": {
        "LOG_LEVEL": "INFO",
        "CONFIG_PATH": "config/production.yaml"
      }
    },
    "deep-thinking-debug": {
      "command": "uvx",
      "args": [
        "--from", "/path/to/local/mcp-style-agent", 
        "deep-thinking-mcp-server",
        "--log-level", "DEBUG"
      ],
      "env": {
        "LOG_LEVEL": "DEBUG",
        "DATA_DIR": "/path/to/local/mcp-style-agent/debug_data"
      }
    }
  }
}
```

## 监控和维护

### 健康检查

```bash
# Docker环境
docker-compose ps
docker-compose exec deep-thinking-mcp python -c "from mcps.deep_thinking.server import DeepThinkingMCPServer; print('OK')"

# 本地环境
uv run python -c "from mcps.deep_thinking.server import DeepThinkingMCPServer; print('OK')"
```

### 日志管理

**日志位置**:
- Docker: `logs/mcp_server.log`
- 本地: `logs/mcp_server.log`

**日志轮转**:
- 最大文件大小: 10MB
- 保留文件数: 5个

**查看日志**:
```bash
# 实时日志
tail -f logs/mcp_server.log

# Docker日志
docker-compose logs -f deep-thinking-mcp
```

### 数据库维护

**备份**:
```bash
# 手动备份
cp data/deep_thinking.db backups/deep_thinking_$(date +%Y%m%d_%H%M%S).db

# 自动备份（Docker）
docker-compose up db-backup
```

**清理**:
```bash
# 清理旧会话（30天前）
sqlite3 data/deep_thinking.db "DELETE FROM thinking_sessions WHERE start_time < datetime('now', '-30 days');"
```

## 测试和验证

### 测试 uvx 部署

项目提供了专门的测试脚本来验证 uvx 部署是否正常工作：

```bash
# 运行 uvx 部署测试
make test-uvx

# 或直接运行测试脚本
uv run python scripts/test_uvx_deployment.py
```

测试脚本会验证：
- uvx 是否正确安装
- 包是否可以通过 uvx 安装和执行
- MCP server 是否可以正常启动
- 生成示例配置文件

**成功的测试输出示例**：
```
🧪 Testing uvx deployment for Deep Thinking MCP Server
============================================================

🔍 Testing uvx Installation...
✅ uvx is installed: uv-tool-uvx 0.6.14

🔍 Testing Package Installation...
✅ Package can be installed and executed via uvx

🔍 Testing MCP Server Startup...
✅ MCP server validation passed

📊 Test Results Summary:
==============================
✅ PASS uvx Installation
✅ PASS Package Installation
✅ PASS MCP Server Startup

Passed: 3/3 tests

🎉 All tests passed! uvx deployment is ready.
```

### 验证 MCP server

```bash
# 验证服务器配置
make mcp-server-validate

# 或直接验证
uv run deep-thinking-mcp-server --validate-only
```

### 本地测试

```bash
# 启动 MCP server（开发模式）
make mcp-server-debug

# 或使用 uvx（推荐）
uvx --from . deep-thinking-mcp-server --log-level DEBUG
```

### 配置验证

在配置 MCP 客户端之前，建议先验证配置：

```bash
# 测试本地路径配置
uvx --from /path/to/mcp-style-agent deep-thinking-mcp-server --validate-only

# 测试 Git 仓库配置（如果可用）
uvx --from git+https://github.com/your-org/mcp-style-agent.git deep-thinking-mcp-server --validate-only
```

## 故障排除

### 常见问题

#### 1. 服务器启动失败
```bash
# 检查Python版本
uv run python --version

# 检查依赖
uv run pip list | grep mcp

# 验证配置
uv run python scripts/start_mcp_server.py --validate-only
```

#### 2. 数据库连接错误
```bash
# 检查数据目录权限
ls -la data/

# 重新初始化数据库
rm data/deep_thinking.db
uv run python scripts/start_mcp_server.py --validate-only
```

#### 3. 模板加载失败
```bash
# 检查模板目录
ls -la templates/

# 验证模板格式
uv run python -c "from mcps.deep_thinking.templates.template_manager import TemplateManager; tm = TemplateManager(); print('Templates OK')"
```

#### 4. Docker容器问题
```bash
# 查看容器状态
docker-compose ps

# 查看容器日志
docker-compose logs deep-thinking-mcp

# 重启容器
docker-compose restart deep-thinking-mcp
```

#### 5. uvx 部署问题

**uvx 未安装**:
```bash
# 检查 uv 和 uvx 是否安装
uv --version
uvx --version

# 安装 uv（如果未安装）
curl -LsSf https://astral.sh/uv/install.sh | sh
# 或使用 pip
pip install uv
```

**包安装失败**:
```bash
# 清理 uvx 缓存
uvx --refresh deep-thinking-mcp-server --help

# 使用详细输出查看错误
uvx --verbose --from /path/to/project deep-thinking-mcp-server --help

# 检查项目结构
ls -la /path/to/project/pyproject.toml
```

**权限问题**:
```bash
# 检查目录权限
ls -la /path/to/project
chmod -R 755 /path/to/project

# 检查数据目录权限
mkdir -p data logs
chmod -R 755 data logs
```

**环境变量问题**:
```bash
# 验证环境变量
echo $DATA_DIR
echo $LOG_LEVEL

# 在 MCP 配置中明确设置路径
{
  "env": {
    "DATA_DIR": "/absolute/path/to/data",
    "LOG_LEVEL": "INFO"
  }
}
```

### 性能优化

#### 1. 内存优化
- 调整会话缓存大小: `session_cache_size`
- 限制最大会话数: `max_sessions`
- 启用模板缓存: `template_cache_enabled: true`

#### 2. 存储优化
- 定期清理旧会话数据
- 启用数据库WAL模式
- 配置自动备份

#### 3. 网络优化
- 使用本地Unix socket（如果支持）
- 调整超时设置
- 启用连接池

## 安全考虑

### 数据安全
- 所有数据存储在本地
- 不向外部服务发送敏感信息
- 支持数据库加密（可选）

### 访问控制
- 仅本地访问
- 无网络端口暴露
- 用户权限隔离

### 隐私保护
- 零网络通信（MCP Server端）
- 完全本地处理
- 用户完全控制数据

## 升级指南

### 版本升级
```bash
# 备份数据
./scripts/deploy.sh -b

# 拉取新版本
git pull origin main

# 重新部署
./scripts/deploy.sh -c
```

### 配置迁移
1. 备份现有配置
2. 比较新旧配置文件
3. 合并必要的配置更改
4. 验证配置有效性

## 支持和反馈

如果遇到问题或需要帮助：

1. 查看日志文件获取详细错误信息
2. 检查配置文件格式和内容
3. 验证系统要求和依赖
4. 参考故障排除部分

## 附录

### 目录结构
```
mcp-style-agent/
├── src/mcps/deep_thinking/    # 源代码
├── config/                    # 配置文件
├── templates/                 # Prompt模板
├── scripts/                   # 部署脚本
├── data/                      # 数据库文件
├── logs/                      # 日志文件
├── backups/                   # 备份文件
├── Dockerfile                 # Docker镜像定义
├── docker-compose.yml         # Docker Compose配置
└── docs/deployment/           # 部署文档
```

### 端口使用
- MCP Server: stdio通信，无网络端口
- 健康检查: 内部检查，无外部端口
- 未来HTTP接口: 8000端口（预留）