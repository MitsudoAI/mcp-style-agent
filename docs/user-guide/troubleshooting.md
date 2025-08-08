# 故障排除和FAQ

本文档提供Deep Thinking Engine常见问题的解决方案和故障排除指南。

## 常见问题 (FAQ)

### 基础使用问题

#### Q1: 如何开始使用Deep Thinking Engine？
**A**: 按照以下步骤开始：
1. 确保已正确安装和配置MCP服务器
2. 在Cursor中配置MCP连接
3. 使用`start_thinking`工具开始思考会话
4. 按照返回的Prompt模板执行思维步骤

#### Q2: 为什么我的会话丢失了？
**A**: 会话丢失可能的原因：
- 会话超时（默认60分钟）
- MCP服务器重启
- 数据库连接问题

**解决方案**:
```bash
# 检查服务器状态
docker-compose ps  # Docker部署
# 或
ps aux | grep start_mcp_server  # 本地部署

# 重新开始思考会话
start_thinking("您的问题")
```

#### Q3: 如何调整思维流程的复杂度？
**A**: 在开始思考时指定复杂度：
```json
{
  "topic": "您的问题",
  "complexity": "simple|moderate|complex",
  "flow_type": "quick_analysis|comprehensive_analysis"
}
```

#### Q4: 可以自定义思维流程吗？
**A**: 是的，您可以：
1. 修改`config/flows.yaml`文件
2. 创建自定义模板
3. 定义新的流程步骤
4. 参考[配置指南](configuration.md)了解详情

### 技术问题

#### Q5: MCP服务器启动失败怎么办？
**A**: 按以下步骤排查：

1. **检查Python版本**:
```bash
python --version  # 需要3.8+
```

2. **检查依赖安装**:
```bash
pip list | grep mcp
uv sync  # 如果使用uv
```

3. **验证配置文件**:
```bash
python scripts/start_mcp_server.py --validate-only
```

4. **查看详细错误**:
```bash
python scripts/start_mcp_server.py --log-level DEBUG
```

#### Q6: 数据库连接错误如何解决？
**A**: 数据库问题排查：

1. **检查数据目录权限**:
```bash
ls -la data/
chmod 755 data/
```

2. **重新初始化数据库**:
```bash
rm data/deep_thinking.db
python scripts/start_mcp_server.py --validate-only
```

3. **检查磁盘空间**:
```bash
df -h
```

#### Q7: 模板加载失败怎么办？
**A**: 模板问题解决：

1. **检查模板目录**:
```bash
ls -la templates/
```

2. **验证模板格式**:
```python
from mcps.deep_thinking.templates.template_manager import TemplateManager
tm = TemplateManager()
print("模板加载成功")
```

3. **重置模板缓存**:
```bash
# 重启服务器以清除缓存
docker-compose restart  # Docker
# 或重新启动本地服务器
```

### 性能问题

#### Q8: 系统响应很慢怎么办？
**A**: 性能优化建议：

1. **调整缓存设置**:
```yaml
# config/mcp_server.yaml
server:
  performance:
    template_cache_size: 100
    session_cache_size: 50
```

2. **检查系统资源**:
```bash
# 检查内存使用
free -h
# 检查CPU使用
top
```

3. **优化数据库**:
```bash
# 清理旧会话数据
sqlite3 data/deep_thinking.db "DELETE FROM thinking_sessions WHERE start_time < datetime('now', '-30 days');"
```

#### Q9: 内存使用过高怎么办？
**A**: 内存优化方案：

1. **调整会话限制**:
```yaml
server:
  runtime:
    max_sessions: 50  # 减少最大会话数
    session_timeout_minutes: 30  # 缩短超时时间
```

2. **清理缓存**:
```bash
# 重启服务器清理内存
docker-compose restart deep-thinking-mcp
```

3. **监控内存使用**:
```bash
# 查看容器内存使用
docker stats deep-thinking-mcp-server
```

### 质量问题

#### Q10: 分析质量评分总是很低怎么办？
**A**: 提高分析质量的方法：

1. **提供更详细的输入**:
   - 使用具体、明确的问题表述
   - 提供相关背景信息
   - 明确分析重点

2. **调整质量门槛**:
```yaml
# config/flows.yaml
flows:
  quality_gates:
    default_threshold: 0.6  # 降低门槛
```

3. **使用analyze_step工具**:
```json
{
  "session_id": "your-session-id",
  "step_name": "current_step",
  "step_result": "your-result",
  "analysis_type": "quality"
}
```

#### Q11: 如何提高证据收集的质量？
**A**: 证据收集最佳实践：

1. **多样化信息源**:
   - 学术论文和研究报告
   - 政府和权威机构数据
   - 新闻媒体和专家观点
   - 行业报告和案例研究

2. **评估信息可信度**:
   - 检查来源权威性
   - 验证数据时效性
   - 识别潜在偏见
   - 交叉验证信息

3. **结构化整理**:
   - 按主题分类证据
   - 标注可信度评分
   - 记录来源信息
   - 识别相互冲突的观点

## 故障排除指南

### 系统级问题

#### 服务器无法启动

**症状**: 运行启动脚本时出现错误

**诊断步骤**:
1. 检查错误日志
2. 验证配置文件
3. 检查依赖安装
4. 验证文件权限

**解决方案**:
```bash
# 1. 查看详细错误信息
python scripts/start_mcp_server.py --log-level DEBUG --log-file logs/debug.log

# 2. 验证环境
python --version
pip list | grep -E "(mcp|pydantic|sqlalchemy)"

# 3. 重新安装依赖
pip install -e . --force-reinstall

# 4. 检查配置
python scripts/start_mcp_server.py --validate-only
```

#### Docker容器问题

**症状**: Docker容器启动失败或异常退出

**诊断步骤**:
```bash
# 查看容器状态
docker-compose ps

# 查看容器日志
docker-compose logs deep-thinking-mcp

# 检查容器资源使用
docker stats deep-thinking-mcp-server
```

**解决方案**:
```bash
# 重新构建镜像
docker-compose build --no-cache

# 清理并重启
docker-compose down -v
docker-compose up -d

# 进入容器调试
docker-compose exec deep-thinking-mcp bash
```

### 应用级问题

#### 会话管理问题

**症状**: 会话状态不一致或丢失

**诊断步骤**:
```bash
# 检查数据库
sqlite3 data/deep_thinking.db ".tables"
sqlite3 data/deep_thinking.db "SELECT COUNT(*) FROM thinking_sessions;"

# 检查会话缓存
grep -i "session" logs/mcp_server.log
```

**解决方案**:
```bash
# 清理异常会话
sqlite3 data/deep_thinking.db "DELETE FROM thinking_sessions WHERE status = 'error';"

# 重置会话缓存
# 重启服务器即可
```

#### 模板系统问题

**症状**: 模板加载失败或格式错误

**诊断步骤**:
```python
# 测试模板加载
from mcps.deep_thinking.templates.template_manager import TemplateManager
tm = TemplateManager()
try:
    template = tm.get_template("decomposition", {"topic": "test"})
    print("模板加载成功")
except Exception as e:
    print(f"模板加载失败: {e}")
```

**解决方案**:
```bash
# 验证模板文件
find templates/ -name "*.py" -exec python -m py_compile {} \;

# 重置模板缓存
rm -rf __pycache__/
rm -rf templates/__pycache__/

# 检查模板语法
python -c "from templates.decomposition_template import DECOMPOSITION_TEMPLATE; print('OK')"
```

### 性能问题

#### 响应时间过长

**症状**: MCP工具调用响应缓慢

**诊断步骤**:
```bash
# 检查系统资源
htop
iotop

# 分析日志中的响应时间
grep -i "response_time" logs/mcp_server.log

# 检查数据库性能
sqlite3 data/deep_thinking.db ".timer on" "SELECT COUNT(*) FROM thinking_sessions;"
```

**优化方案**:
```yaml
# 调整性能配置
server:
  performance:
    template_cache_size: 100
    session_cache_size: 50
    database_pool_size: 10

templates:
  cache:
    enabled: true
    size: 100
    ttl_minutes: 120
```

#### 内存泄漏

**症状**: 内存使用持续增长

**诊断步骤**:
```bash
# 监控内存使用
watch -n 5 'ps aux | grep start_mcp_server'

# Docker环境监控
docker stats deep-thinking-mcp-server
```

**解决方案**:
```yaml
# 调整内存管理配置
server:
  runtime:
    max_sessions: 50
    session_timeout_minutes: 30
  performance:
    template_cache_size: 50
    session_cache_size: 20
```

## 调试技巧

### 启用调试模式

```bash
# 启用详细日志
python scripts/start_mcp_server.py --log-level DEBUG

# 启用开发模式
export DEBUG_MODE=true
python scripts/start_mcp_server.py
```

### 日志分析

```bash
# 查看错误日志
grep -i error logs/mcp_server.log

# 查看性能日志
grep -i "response_time\|duration" logs/mcp_server.log

# 实时监控日志
tail -f logs/mcp_server.log
```

### 数据库调试

```bash
# 连接数据库
sqlite3 data/deep_thinking.db

# 查看表结构
.schema thinking_sessions

# 查看会话状态
SELECT session_id, status, created_at FROM thinking_sessions ORDER BY created_at DESC LIMIT 10;

# 清理测试数据
DELETE FROM thinking_sessions WHERE topic LIKE '%test%';
```

### 配置验证

```python
# 验证配置文件
from mcps.deep_thinking.config.config_manager import ConfigManager
try:
    config = ConfigManager()
    print("配置加载成功")
    print(f"默认流程: {config.get('flows.default_flow')}")
except Exception as e:
    print(f"配置错误: {e}")
```

## 预防措施

### 定期维护

1. **数据库维护**:
```bash
# 每周清理旧数据
sqlite3 data/deep_thinking.db "DELETE FROM thinking_sessions WHERE start_time < datetime('now', '-7 days');"

# 优化数据库
sqlite3 data/deep_thinking.db "VACUUM;"
```

2. **日志轮转**:
```bash
# 设置日志轮转
logrotate -f /etc/logrotate.d/deep-thinking
```

3. **备份数据**:
```bash
# 自动备份脚本
cp data/deep_thinking.db backups/deep_thinking_$(date +%Y%m%d).db
```

### 监控设置

```yaml
# 启用监控
monitoring:
  enabled: true
  performance:
    track_response_time: true
    track_memory_usage: true
  error_tracking:
    enabled: true
    alert_on_critical: true
```

### 健康检查

```bash
# 创建健康检查脚本
#!/bin/bash
# health_check.sh

# 检查服务器进程
if ! pgrep -f "start_mcp_server.py" > /dev/null; then
    echo "ERROR: MCP服务器未运行"
    exit 1
fi

# 检查数据库连接
if ! sqlite3 data/deep_thinking.db "SELECT 1;" > /dev/null 2>&1; then
    echo "ERROR: 数据库连接失败"
    exit 1
fi

# 检查模板加载
if ! python -c "from mcps.deep_thinking.templates.template_manager import TemplateManager; TemplateManager()" > /dev/null 2>&1; then
    echo "ERROR: 模板加载失败"
    exit 1
fi

echo "OK: 系统健康"
exit 0
```

## 获取帮助

### 日志收集

当需要技术支持时，请收集以下信息：

```bash
# 创建诊断报告
#!/bin/bash
# collect_diagnostics.sh

echo "=== 系统信息 ===" > diagnostics.txt
uname -a >> diagnostics.txt
python --version >> diagnostics.txt

echo "=== 配置信息 ===" >> diagnostics.txt
cat config/mcp_server.yaml >> diagnostics.txt

echo "=== 错误日志 ===" >> diagnostics.txt
tail -100 logs/mcp_server.log >> diagnostics.txt

echo "=== 数据库状态 ===" >> diagnostics.txt
sqlite3 data/deep_thinking.db ".tables" >> diagnostics.txt
sqlite3 data/deep_thinking.db "SELECT COUNT(*) FROM thinking_sessions;" >> diagnostics.txt

echo "诊断报告已生成: diagnostics.txt"
```

### 社区支持

1. 查看项目文档和FAQ
2. 搜索已知问题和解决方案
3. 提交详细的问题报告
4. 参与社区讨论

### 问题报告模板

```markdown
## 问题描述
[简要描述遇到的问题]

## 复现步骤
1. [步骤1]
2. [步骤2]
3. [步骤3]

## 预期行为
[描述期望的正确行为]

## 实际行为
[描述实际发生的情况]

## 环境信息
- 操作系统: [如 macOS 12.0]
- Python版本: [如 3.12.0]
- 部署方式: [Docker/本地]

## 错误日志
```
[粘贴相关错误日志]
```

## 其他信息
[任何其他相关信息]
```

通过遵循这些故障排除指南，您应该能够解决大部分常见问题。如果问题仍然存在，请不要犹豫寻求帮助。