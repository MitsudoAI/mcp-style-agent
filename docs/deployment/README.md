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
```bash
# 安装uv
pip install uv

# 安装依赖
uv sync

# 启动服务器
python scripts/start_mcp_server.py
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
python scripts/start_mcp_server.py [OPTIONS]

选项:
  -c, --config PATH     配置文件路径
  -l, --log-level LEVEL 日志级别 (DEBUG|INFO|WARNING|ERROR)
  -f, --log-file PATH   日志文件路径
  -v, --validate-only   仅验证配置并退出
```

## MCP客户端配置

### Cursor配置

在Cursor中配置MCP服务器：

1. 打开Cursor设置
2. 找到MCP配置部分
3. 添加服务器配置：

```json
{
  "mcpServers": {
    "deep-thinking-engine": {
      "command": "python",
      "args": ["scripts/start_mcp_server.py"],
      "cwd": "/path/to/mcp-style-agent",
      "env": {
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### Claude Desktop配置

```json
{
  "mcpServers": {
    "deep-thinking-engine": {
      "command": "python",
      "args": ["/path/to/mcp-style-agent/scripts/start_mcp_server.py"],
      "env": {
        "LOG_LEVEL": "INFO"
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
python -c "from src.mcps.deep_thinking.server import DeepThinkingMCPServer; print('OK')"
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

## 故障排除

### 常见问题

#### 1. 服务器启动失败
```bash
# 检查Python版本
python --version

# 检查依赖
pip list | grep mcp

# 验证配置
python scripts/start_mcp_server.py --validate-only
```

#### 2. 数据库连接错误
```bash
# 检查数据目录权限
ls -la data/

# 重新初始化数据库
rm data/deep_thinking.db
python scripts/start_mcp_server.py --validate-only
```

#### 3. 模板加载失败
```bash
# 检查模板目录
ls -la templates/

# 验证模板格式
python -c "from src.mcps.deep_thinking.templates.template_manager import TemplateManager; tm = TemplateManager(); print('Templates OK')"
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