# 贡献指南

欢迎为Deep Thinking Engine项目做出贡献！本文档将指导您如何参与项目开发，包括代码贡献、文档改进、问题报告等。

## 贡献方式

### 1. 代码贡献
- 修复Bug
- 添加新功能
- 性能优化
- 代码重构

### 2. 文档贡献
- 改进现有文档
- 添加使用示例
- 翻译文档
- 编写教程

### 3. 测试贡献
- 编写单元测试
- 添加集成测试
- 性能测试
- 用户验收测试

### 4. 社区贡献
- 回答问题
- 参与讨论
- 分享使用经验
- 推广项目

## 开发环境设置

### 1. 环境要求

- **Python**: 3.8+ (推荐3.12+)
- **Git**: 2.20+
- **操作系统**: Linux, macOS, Windows

### 2. 克隆项目

```bash
# 克隆主仓库
git clone https://github.com/your-org/deep-thinking-engine.git
cd deep-thinking-engine

# 添加上游仓库（如果是Fork）
git remote add upstream https://github.com/original-org/deep-thinking-engine.git
```

### 3. 安装依赖

```bash
# 使用uv（推荐）
pip install uv
uv sync --dev

# 或使用pip
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# 或 .venv\Scripts\activate  # Windows
pip install -e ".[dev]"
```

### 4. 安装开发工具

```bash
# 安装pre-commit钩子
pre-commit install

# 验证安装
make check
```

## 开发工作流

### 1. 创建功能分支

```bash
# 从main分支创建新分支
git checkout main
git pull upstream main
git checkout -b feature/your-feature-name

# 分支命名规范
# feature/功能名称 - 新功能
# fix/问题描述 - Bug修复
# docs/文档类型 - 文档更新
# refactor/重构内容 - 代码重构
# test/测试内容 - 测试相关
```

### 2. 开发和测试

```bash
# 运行测试
make test

# 代码格式化
make format

# 代码检查
make lint

# 类型检查
make type-check

# 完整检查
make check
```

### 3. 提交代码

```bash
# 添加文件
git add .

# 提交（遵循提交规范）
git commit -m "feat: add new thinking flow for business analysis"

# 推送分支
git push origin feature/your-feature-name
```

### 4. 创建Pull Request

1. 在GitHub上创建Pull Request
2. 填写PR模板
3. 等待代码审查
4. 根据反馈修改代码
5. 合并到主分支

## 代码规范

### 1. Python代码规范

#### 代码风格

```python
# 使用Black格式化，行长度88字符
# 使用isort整理导入语句

# 好的示例
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from mcps.deep_thinking.models.base import BaseThinkingModel


class SessionState(BaseThinkingModel):
    """思考会话状态模型"""
    
    session_id: str = Field(..., description="会话唯一标识")
    topic: str = Field(..., description="思考主题")
    
    def get_duration(self) -> float:
        """获取会话持续时间"""
        return (self.updated_at - self.created_at).total_seconds()
```

#### 命名规范

```python
# 类名：PascalCase
class ThinkingSession:
    pass

# 函数和变量名：snake_case
def create_session(session_data: dict) -> bool:
    user_id = session_data.get("user_id")
    return True

# 常量：UPPER_SNAKE_CASE
MAX_SESSION_COUNT = 100
DEFAULT_TIMEOUT = 3600

# 私有方法：前缀下划线
def _internal_method(self):
    pass
```

#### 类型提示

```python
from typing import Dict, List, Optional, Union

# 函数类型提示
def process_session(
    session_id: str,
    options: Optional[Dict[str, Any]] = None
) -> Optional[SessionState]:
    """处理会话，返回会话状态或None"""
    pass

# 类属性类型提示
class SessionManager:
    sessions: Dict[str, SessionState]
    max_sessions: int
    
    def __init__(self, max_sessions: int = 100):
        self.sessions = {}
        self.max_sessions = max_sessions
```

#### 文档字符串

```python
def analyze_step(
    session_id: str,
    step_name: str,
    step_result: str,
    analysis_type: str = "quality"
) -> MCPToolOutput:
    """
    分析步骤执行质量
    
    Args:
        session_id: 思考会话ID
        step_name: 要分析的步骤名称
        step_result: 步骤执行结果
        analysis_type: 分析类型，可选值：quality, format, completeness
        
    Returns:
        MCPToolOutput: 包含分析结果的工具输出
        
    Raises:
        SessionNotFoundError: 会话不存在时抛出
        ValidationError: 输入参数无效时抛出
        
    Example:
        >>> result = analyze_step("session-123", "decompose", "结果内容")
        >>> print(result.prompt_template)
    """
    pass
```

### 2. 错误处理规范

```python
# 自定义异常
class DeepThinkingError(Exception):
    """基础异常类"""
    
    def __init__(self, message: str, error_code: str = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__

# 异常处理
def create_session(session_data: dict) -> SessionState:
    try:
        # 验证输入
        if not session_data.get("topic"):
            raise ValidationError("Topic is required")
        
        # 业务逻辑
        session = SessionState(**session_data)
        return session
        
    except ValidationError:
        # 重新抛出业务异常
        raise
    except Exception as e:
        # 包装系统异常
        logger.error(f"Unexpected error creating session: {e}")
        raise SessionCreationError(f"Failed to create session: {e}")
```

### 3. 测试规范

```python
import pytest
from unittest.mock import Mock, patch

from mcps.deep_thinking.tools.mcp_tools import MCPTools
from mcps.deep_thinking.models.mcp_models import StartThinkingInput


class TestMCPTools:
    """MCP工具测试类"""
    
    def setup_method(self):
        """测试前置设置"""
        self.session_manager = Mock()
        self.template_manager = Mock()
        self.flow_manager = Mock()
        self.mcp_tools = MCPTools(
            self.session_manager,
            self.template_manager,
            self.flow_manager
        )
    
    def test_start_thinking_success(self):
        """测试成功开始思考"""
        # Arrange
        input_data = StartThinkingInput(topic="测试问题")
        self.template_manager.get_template.return_value = "模板内容"
        
        # Act
        result = self.mcp_tools.start_thinking(input_data)
        
        # Assert
        assert result.tool_name == "start_thinking"
        assert result.session_id is not None
        assert "模板内容" in result.prompt_template
        self.session_manager.create_session.assert_called_once()
    
    def test_start_thinking_validation_error(self):
        """测试输入验证错误"""
        # Arrange
        input_data = StartThinkingInput(topic="")  # 空主题
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            self.mcp_tools.start_thinking(input_data)
        
        assert "Topic cannot be empty" in str(exc_info.value)
    
    @patch('mcps.deep_thinking.tools.mcp_tools.uuid.uuid4')
    def test_session_id_generation(self, mock_uuid):
        """测试会话ID生成"""
        # Arrange
        mock_uuid.return_value = "test-uuid"
        input_data = StartThinkingInput(topic="测试问题")
        
        # Act
        result = self.mcp_tools.start_thinking(input_data)
        
        # Assert
        assert result.session_id == "test-uuid"
```

## 提交规范

### 1. 提交消息格式

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

#### 类型说明

- **feat**: 新功能
- **fix**: Bug修复
- **docs**: 文档更新
- **style**: 代码格式调整（不影响功能）
- **refactor**: 代码重构
- **test**: 测试相关
- **chore**: 构建过程或辅助工具的变动
- **perf**: 性能优化
- **ci**: CI/CD相关

#### 范围说明

- **mcp**: MCP工具相关
- **session**: 会话管理相关
- **template**: 模板系统相关
- **flow**: 流程管理相关
- **config**: 配置管理相关
- **docs**: 文档相关
- **test**: 测试相关

#### 示例

```bash
# 新功能
git commit -m "feat(mcp): add bias detection tool for cognitive bias analysis"

# Bug修复
git commit -m "fix(session): resolve session timeout issue in long-running analysis"

# 文档更新
git commit -m "docs(api): update MCP tools API reference with new parameters"

# 重构
git commit -m "refactor(template): improve template caching mechanism for better performance"

# 测试
git commit -m "test(integration): add comprehensive integration tests for thinking flows"
```

### 2. 提交最佳实践

- 每个提交只包含一个逻辑变更
- 提交消息简洁明了，描述变更内容
- 包含必要的测试
- 确保代码通过所有检查

## Pull Request规范

### 1. PR标题

使用与提交消息相同的格式：

```
feat(mcp): add custom evaluation criteria support
```

### 2. PR描述模板

```markdown
## 变更类型
- [ ] Bug修复
- [ ] 新功能
- [ ] 重大变更
- [ ] 文档更新
- [ ] 性能优化
- [ ] 代码重构

## 变更描述
简要描述此PR的变更内容和目的。

## 相关Issue
Fixes #123
Closes #456

## 测试
- [ ] 添加了新的测试
- [ ] 所有测试通过
- [ ] 手动测试通过

## 检查清单
- [ ] 代码遵循项目规范
- [ ] 添加了必要的文档
- [ ] 更新了CHANGELOG
- [ ] 通过了所有CI检查

## 截图（如适用）
如果有UI变更，请添加截图。

## 其他说明
任何其他需要说明的内容。
```

### 3. 代码审查要求

- 至少需要一个维护者的审查
- 所有CI检查必须通过
- 解决所有审查意见
- 保持提交历史清洁

## 测试指南

### 1. 测试类型

#### 单元测试
```python
# tests/test_session_manager.py
def test_create_session():
    """测试会话创建"""
    manager = SessionManager()
    session_data = {
        "session_id": "test-123",
        "topic": "测试主题",
        "flow_type": "comprehensive_analysis"
    }
    
    result = manager.create_session(SessionState(**session_data))
    assert result is True
    
    session = manager.get_session("test-123")
    assert session is not None
    assert session.topic == "测试主题"
```

#### 集成测试
```python
# tests/integration/test_thinking_flow.py
def test_complete_thinking_flow():
    """测试完整思考流程"""
    # 初始化组件
    mcp_tools = create_mcp_tools()
    
    # 开始思考
    start_result = mcp_tools.start_thinking(
        StartThinkingInput(topic="测试问题")
    )
    session_id = start_result.session_id
    
    # 执行步骤
    step_result = simulate_step_execution(start_result.prompt_template)
    
    # 获取下一步
    next_result = mcp_tools.next_step(
        NextStepInput(session_id=session_id, step_result=step_result)
    )
    
    # 验证流程继续
    assert next_result.step == "collect_evidence"
```

#### 性能测试
```python
# tests/performance/test_template_performance.py
def test_template_rendering_performance():
    """测试模板渲染性能"""
    template_manager = TemplateManager()
    
    # 预热
    for _ in range(10):
        template_manager.get_template("decomposition", {"topic": "测试"})
    
    # 性能测试
    start_time = time.time()
    for _ in range(100):
        template_manager.get_template("decomposition", {"topic": "测试"})
    end_time = time.time()
    
    avg_time = (end_time - start_time) / 100
    assert avg_time < 0.01  # 平均渲染时间应小于10ms
```

### 2. 测试覆盖率

- 目标覆盖率：≥80%
- 核心组件覆盖率：≥90%
- 新增代码覆盖率：≥85%

```bash
# 运行覆盖率测试
make test-coverage

# 查看覆盖率报告
open htmlcov/index.html
```

### 3. 测试数据管理

```python
# tests/fixtures/session_fixtures.py
@pytest.fixture
def sample_session():
    """示例会话数据"""
    return SessionState(
        session_id="test-session-123",
        topic="测试主题",
        current_step="decompose_problem",
        flow_type="comprehensive_analysis",
        context={"complexity": "moderate"}
    )

@pytest.fixture
def mock_template_manager():
    """模拟模板管理器"""
    manager = Mock()
    manager.get_template.return_value = "模拟模板内容"
    return manager
```

## 文档贡献

### 1. 文档类型

- **用户文档**: 面向最终用户的使用指南
- **开发者文档**: 面向开发者的技术文档
- **API文档**: 接口参考文档
- **教程文档**: 分步骤的学习教程

### 2. 文档规范

#### Markdown格式
```markdown
# 一级标题

## 二级标题

### 三级标题

- 无序列表项
- 另一个列表项

1. 有序列表项
2. 另一个有序列表项

**粗体文本**
*斜体文本*
`代码片段`

```python
# 代码块
def example_function():
    return "Hello, World!"
```

> 引用文本

[链接文本](URL)
![图片描述](图片URL)
```

#### 代码示例
```python
# 好的代码示例
def start_thinking(topic: str, complexity: str = "moderate") -> dict:
    """
    开始深度思考会话
    
    Args:
        topic: 思考主题
        complexity: 复杂度级别
        
    Returns:
        包含会话信息的字典
        
    Example:
        >>> result = start_thinking("如何提高效率？")
        >>> print(result["session_id"])
        550e8400-e29b-41d4-a716-446655440000
    """
    pass
```

### 3. 文档更新流程

1. 识别需要更新的文档
2. 创建文档分支
3. 编写或更新文档
4. 本地预览检查
5. 提交PR并请求审查
6. 根据反馈修改
7. 合并到主分支

## 问题报告

### 1. Bug报告模板

```markdown
## Bug描述
简要描述遇到的问题。

## 复现步骤
1. 执行操作A
2. 执行操作B
3. 观察到错误

## 预期行为
描述期望的正确行为。

## 实际行为
描述实际发生的情况。

## 环境信息
- 操作系统: [如 macOS 12.0]
- Python版本: [如 3.12.0]
- 项目版本: [如 0.1.0]
- 部署方式: [Docker/本地]

## 错误日志
```
粘贴相关错误日志
```

## 其他信息
任何其他相关信息，如截图、配置文件等。
```

### 2. 功能请求模板

```markdown
## 功能描述
简要描述希望添加的功能。

## 使用场景
描述什么情况下需要这个功能。

## 建议的解决方案
如果有想法，描述如何实现这个功能。

## 替代方案
描述其他可能的解决方案。

## 其他信息
任何其他相关信息。
```

## 发布流程

### 1. 版本号规范

使用语义化版本控制（SemVer）：

- **主版本号**: 不兼容的API修改
- **次版本号**: 向后兼容的功能性新增
- **修订号**: 向后兼容的问题修正

### 2. 发布检查清单

- [ ] 所有测试通过
- [ ] 文档已更新
- [ ] CHANGELOG已更新
- [ ] 版本号已更新
- [ ] 创建发布标签
- [ ] 构建和测试发布包
- [ ] 发布到PyPI（如适用）
- [ ] 更新Docker镜像
- [ ] 发布公告

### 3. 发布命令

```bash
# 更新版本号
bump2version patch  # 或 minor, major

# 创建发布标签
git tag -a v0.1.1 -m "Release version 0.1.1"
git push origin v0.1.1

# 构建发布包
python -m build

# 发布到PyPI
twine upload dist/*
```

## 社区参与

### 1. 讨论参与

- 参与GitHub Discussions
- 回答用户问题
- 分享使用经验
- 提供改进建议

### 2. 代码审查

- 审查其他贡献者的PR
- 提供建设性反馈
- 分享最佳实践
- 帮助新贡献者

### 3. 社区活动

- 参与在线会议
- 分享技术博客
- 制作教程视频
- 参加技术会议

## 行为准则

### 1. 基本原则

- 尊重所有参与者
- 保持专业和友善
- 欢迎不同观点
- 专注于建设性讨论

### 2. 不当行为

- 人身攻击或侮辱
- 骚扰或歧视
- 发布不当内容
- 恶意破坏

### 3. 举报机制

如果遇到不当行为，请通过以下方式举报：

- 发送邮件到：conduct@deep-thinking-engine.org
- 联系项目维护者
- 使用GitHub的举报功能

## 获得帮助

### 1. 文档资源

- [用户指南](../user-guide/README.md)
- [开发者文档](README.md)
- [API参考](api-reference.md)
- [架构设计](architecture.md)

### 2. 社区支持

- GitHub Issues: 报告问题和请求功能
- GitHub Discussions: 一般讨论和问答
- 邮件列表: dev@deep-thinking-engine.org

### 3. 联系方式

- 项目维护者: maintainers@deep-thinking-engine.org
- 技术支持: support@deep-thinking-engine.org
- 安全问题: security@deep-thinking-engine.org

## 致谢

感谢所有为Deep Thinking Engine项目做出贡献的开发者、用户和支持者！您的参与使这个项目变得更好。

### 贡献者名单

- [贡献者1](https://github.com/contributor1) - 核心开发
- [贡献者2](https://github.com/contributor2) - 文档改进
- [贡献者3](https://github.com/contributor3) - 测试完善

### 特别感谢

- 感谢所有提供反馈和建议的用户
- 感谢参与测试和调试的志愿者
- 感谢提供技术支持的社区成员

---

再次感谢您对Deep Thinking Engine项目的关注和贡献！让我们一起构建更好的深度思考工具。