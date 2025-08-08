# 配置和自定义指南

本文档详细介绍如何配置和自定义Deep Thinking Engine，以适应不同的使用需求和场景。

## 配置文件概览

Deep Thinking Engine使用YAML格式的配置文件来管理系统行为。主要配置文件包括：

- `config/mcp_server.yaml` - MCP服务器配置
- `config/flows.yaml` - 思维流程定义
- `config/templates.yaml` - 模板配置
- `config/system.yaml` - 系统级配置

## MCP服务器配置

### 基础配置 (config/mcp_server.yaml)

```yaml
# MCP服务器基础配置
server:
  name: "deep-thinking-engine"
  version: "0.1.0"
  description: "Zero-cost local MCP server for systematic deep thinking"
  
  # 运行时设置
  runtime:
    log_level: "INFO"           # 日志级别: DEBUG, INFO, WARNING, ERROR
    max_sessions: 100           # 最大并发会话数
    session_timeout_minutes: 60 # 会话超时时间（分钟）
    enable_debug: false         # 是否启用调试模式
    
  # 性能设置
  performance:
    template_cache_size: 50     # 模板缓存大小
    session_cache_size: 20      # 会话缓存大小
    database_pool_size: 5       # 数据库连接池大小
    
  # 安全设置
  security:
    enable_input_validation: true    # 启用输入验证
    max_input_length: 10000         # 最大输入长度
    rate_limiting:
      enabled: false                # 速率限制（本地使用通常禁用）
      requests_per_minute: 60       # 每分钟请求数限制

# 数据库配置
database:
  type: "sqlite"                    # 数据库类型
  path: "data/deep_thinking.db"     # 数据库文件路径
  backup:
    enabled: true                   # 启用自动备份
    interval_hours: 24              # 备份间隔（小时）
    max_backups: 7                  # 最大备份文件数

# 模板配置
templates:
  base_path: "templates"            # 模板基础路径
  cache_enabled: true               # 启用模板缓存
  hot_reload: true                  # 启用热重载
  validation:
    enabled: true                   # 启用模板验证
    strict_mode: false              # 严格模式

# 流程配置
flows:
  default_flow: "comprehensive_analysis"  # 默认思维流程
  enable_adaptive_flows: true             # 启用自适应流程
  quality_gates:
    enabled: true                         # 启用质量门槛
    default_threshold: 0.7                # 默认质量门槛

# 日志配置
logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "logs/mcp_server.log"
  max_size_mb: 10
  backup_count: 5

# 开发设置
development:
  enable_hot_reload: true           # 启用热重载
  debug_mode: false                 # 调试模式
  profiling: false                  # 性能分析
```

### 环境特定配置

您可以为不同环境创建特定的配置文件：

**开发环境** (`config/development.yaml`):
```yaml
server:
  runtime:
    log_level: "DEBUG"
    enable_debug: true
    
development:
  enable_hot_reload: true
  debug_mode: true
  profiling: true
  
logging:
  level: "DEBUG"
```

**生产环境** (`config/production.yaml`):
```yaml
server:
  runtime:
    log_level: "WARNING"
    max_sessions: 200
    
  performance:
    template_cache_size: 100
    session_cache_size: 50
    
development:
  enable_hot_reload: false
  debug_mode: false
  profiling: false
```

## 思维流程配置

### 流程定义 (config/flows.yaml)

```yaml
# 思维流程定义
thinking_flows:
  # 全面分析流程
  comprehensive_analysis:
    name: "全面深度分析"
    description: "适用于复杂问题的全面分析流程"
    steps:
      - step: "decompose_problem"
        name: "问题分解"
        template: "decomposition"
        required: true
        quality_threshold: 0.7
        
      - step: "collect_evidence"
        name: "证据收集"
        template: "evidence_collection"
        parallel: true
        for_each: "sub_questions"
        quality_threshold: 0.8
        
      - step: "multi_perspective_debate"
        name: "多角度辩论"
        template: "debate"
        depends_on: ["collect_evidence"]
        quality_threshold: 0.7
        
      - step: "critical_evaluation"
        name: "批判性评估"
        template: "critical_evaluation"
        quality_gate: 0.8
        retry_on_failure: true
        
      - step: "bias_detection"
        name: "偏见检测"
        template: "bias_detection"
        quality_threshold: 0.7
        
      - step: "innovation_thinking"
        name: "创新思维"
        template: "innovation"
        conditional: "evaluation_score >= 0.8"
        quality_threshold: 0.6
        
      - step: "reflection"
        name: "反思总结"
        template: "reflection"
        final: true
        quality_threshold: 0.7

  # 快速分析流程
  quick_analysis:
    name: "快速分析"
    description: "适用于简单问题的快速分析流程"
    steps:
      - step: "simple_decompose"
        name: "简化分解"
        template: "simple_decomposition"
        quality_threshold: 0.6
        
      - step: "basic_evidence"
        name: "基础证据收集"
        template: "basic_evidence"
        quality_threshold: 0.6
        
      - step: "quick_evaluation"
        name: "快速评估"
        template: "basic_evaluation"
        quality_threshold: 0.6
        
      - step: "brief_reflection"
        name: "简要反思"
        template: "brief_reflection"
        final: true
        quality_threshold: 0.6

  # 自定义流程示例
  business_analysis:
    name: "商业分析流程"
    description: "专门用于商业决策分析"
    steps:
      - step: "market_analysis"
        name: "市场分析"
        template: "market_analysis"
        quality_threshold: 0.8
        
      - step: "competitive_analysis"
        name: "竞争分析"
        template: "competitive_analysis"
        quality_threshold: 0.7
        
      - step: "financial_analysis"
        name: "财务分析"
        template: "financial_analysis"
        quality_threshold: 0.8
        
      - step: "risk_assessment"
        name: "风险评估"
        template: "risk_assessment"
        quality_threshold: 0.7
        
      - step: "strategic_recommendation"
        name: "战略建议"
        template: "strategic_recommendation"
        final: true
        quality_threshold: 0.8

# 流程控制配置
flow_control:
  # 自适应流程设置
  adaptive_flows:
    enabled: true
    complexity_thresholds:
      simple: 0.3
      moderate: 0.7
      complex: 1.0
    
  # 质量门槛设置
  quality_gates:
    enabled: true
    thresholds:
      academic_research: 0.9
      business_decision: 0.8
      quick_analysis: 0.6
      default: 0.7
    
  # 重试机制
  retry_mechanism:
    enabled: true
    max_retries: 2
    retry_threshold: 0.6
    
  # 并行处理
  parallel_processing:
    enabled: true
    max_parallel_steps: 3
```

### 条件流程控制

您可以定义基于条件的流程控制：

```yaml
conditional_flows:
  # 基于复杂度的流程选择
  complexity_based:
    conditions:
      - if: "complexity == 'simple'"
        then: "quick_analysis"
      - if: "complexity == 'complex'"
        then: "comprehensive_analysis"
      - else: "comprehensive_analysis"
  
  # 基于领域的流程选择
  domain_based:
    conditions:
      - if: "domain == 'business'"
        then: "business_analysis"
      - if: "domain == 'technical'"
        then: "technical_analysis"
      - else: "comprehensive_analysis"
```

## 模板配置

### 模板管理 (config/templates.yaml)

```yaml
# 模板配置
templates:
  # 基础设置
  base_path: "templates"
  encoding: "utf-8"
  
  # 缓存设置
  cache:
    enabled: true
    size: 50
    ttl_minutes: 60
    
  # 热重载设置
  hot_reload:
    enabled: true
    watch_directories: ["templates"]
    reload_delay_seconds: 1
    
  # 验证设置
  validation:
    enabled: true
    strict_mode: false
    required_fields: ["template_name", "content"]
    
  # 模板分类
  categories:
    core:
      - "decomposition"
      - "evidence_collection"
      - "critical_evaluation"
      - "reflection"
    
    analysis:
      - "debate"
      - "bias_detection"
      - "innovation"
    
    domain_specific:
      - "business_analysis"
      - "technical_analysis"
      - "academic_research"

# 模板参数配置
template_parameters:
  # 全局参数
  global:
    system_name: "Deep Thinking Engine"
    version: "0.1.0"
    timestamp_format: "%Y-%m-%d %H:%M:%S"
    
  # 默认参数值
  defaults:
    complexity: "moderate"
    quality_threshold: 0.7
    max_sub_questions: 7
    min_sub_questions: 3
    
  # 参数验证规则
  validation_rules:
    complexity:
      type: "string"
      allowed_values: ["simple", "moderate", "complex"]
    quality_threshold:
      type: "float"
      min_value: 0.0
      max_value: 1.0
    topic:
      type: "string"
      max_length: 500
      required: true
```

### 自定义模板

您可以创建自定义的Prompt模板：

**商业分析模板** (`templates/business_analysis.py`):
```python
BUSINESS_ANALYSIS_TEMPLATE = """
# 商业分析：{topic}

## 分析框架

### 1. 市场环境分析
- 市场规模和增长趋势
- 目标客户群体特征
- 市场需求变化趋势

### 2. 竞争环境分析
- 主要竞争对手分析
- 竞争优势和劣势
- 市场定位比较

### 3. 内部能力分析
- 核心竞争力评估
- 资源和能力匹配度
- 组织能力分析

### 4. 财务影响分析
- 投资需求评估
- 预期收益分析
- 风险成本评估

### 5. 战略建议
- 短期行动计划
- 长期战略规划
- 风险缓解措施

请基于以上框架进行详细分析：
"""
```

**技术评估模板** (`templates/technical_analysis.py`):
```python
TECHNICAL_ANALYSIS_TEMPLATE = """
# 技术方案分析：{topic}

## 技术评估维度

### 1. 技术可行性
- 技术成熟度评估
- 实现难度分析
- 技术风险识别

### 2. 架构设计
- 系统架构方案
- 技术栈选择
- 扩展性考虑

### 3. 性能分析
- 性能指标要求
- 性能瓶颈识别
- 优化方案设计

### 4. 安全性评估
- 安全威胁分析
- 安全措施设计
- 合规性要求

### 5. 实施计划
- 开发里程碑
- 资源需求评估
- 时间进度安排

请进行详细的技术分析：
"""
```

## 用户配置管理

### 个人配置文件

用户可以创建个人配置文件来覆盖默认设置：

**用户配置** (`~/.deep_thinking/user_config.yaml`):
```yaml
# 用户个人配置
user_preferences:
  # 默认设置
  default_complexity: "moderate"
  default_flow: "comprehensive_analysis"
  preferred_language: "zh-CN"
  
  # 质量标准
  quality_preferences:
    strict_mode: false
    personal_threshold: 0.8
    
  # 输出格式
  output_preferences:
    include_metadata: true
    verbose_explanations: true
    show_quality_scores: true
    
  # 模板偏好
  template_preferences:
    preferred_style: "detailed"
    include_examples: true
    show_instructions: true

# 个人模板
personal_templates:
  my_analysis:
    name: "我的分析模板"
    content: |
      # 个人分析框架
      
      ## 核心问题
      {topic}
      
      ## 我的分析方法
      1. 直觉判断
      2. 逻辑分析
      3. 经验对比
      4. 风险评估
      
      请按照我的方法进行分析：

# 快捷配置
shortcuts:
  quick_business: 
    flow: "business_analysis"
    complexity: "moderate"
  deep_research:
    flow: "comprehensive_analysis" 
    complexity: "complex"
```

### 团队配置

团队可以共享配置文件：

**团队配置** (`config/team_config.yaml`):
```yaml
# 团队共享配置
team_settings:
  organization: "我的团队"
  default_standards:
    quality_threshold: 0.8
    required_evidence_sources: 3
    min_debate_rounds: 2
    
  # 团队模板
  team_templates:
    project_analysis:
      name: "项目分析模板"
      steps: ["需求分析", "技术评估", "风险分析", "实施计划"]
      
  # 审核流程
  review_process:
    peer_review_required: true
    min_reviewers: 2
    review_criteria: ["逻辑性", "完整性", "可行性"]
```

## 高级配置

### 插件系统配置

```yaml
# 插件配置
plugins:
  enabled: true
  plugin_directory: "plugins"
  
  # 已启用的插件
  active_plugins:
    - name: "web_search_enhancer"
      config:
        search_engines: ["google", "bing"]
        max_results: 10
        
    - name: "citation_manager"
      config:
        citation_style: "APA"
        auto_format: true
        
    - name: "export_manager"
      config:
        supported_formats: ["pdf", "docx", "html"]
        template_path: "export_templates"

# 集成配置
integrations:
  # 外部工具集成
  external_tools:
    enabled: true
    tools:
      - name: "mermaid"
        type: "diagram"
        command: "mmdc"
        
      - name: "pandoc"
        type: "converter"
        command: "pandoc"
        
  # API集成（可选）
  api_integrations:
    enabled: false
    services: []
```

### 监控和分析配置

```yaml
# 监控配置
monitoring:
  enabled: true
  
  # 性能监控
  performance:
    track_response_time: true
    track_memory_usage: true
    track_session_duration: true
    
  # 使用分析
  analytics:
    track_flow_usage: true
    track_template_usage: true
    track_quality_scores: true
    
  # 错误监控
  error_tracking:
    enabled: true
    log_errors: true
    alert_on_critical: false

# 报告配置
reporting:
  enabled: true
  
  # 使用报告
  usage_reports:
    enabled: true
    frequency: "weekly"
    include_metrics: ["session_count", "avg_quality", "popular_flows"]
    
  # 质量报告
  quality_reports:
    enabled: true
    frequency: "monthly"
    include_trends: true
```

## 配置验证和测试

### 配置验证

使用内置工具验证配置文件：

```bash
# 验证所有配置文件
python scripts/start_mcp_server.py --validate-only

# 验证特定配置文件
python -m mcps.deep_thinking.config.validator config/flows.yaml

# 测试配置加载
python -c "from mcps.deep_thinking.config import ConfigManager; cm = ConfigManager(); print('配置加载成功')"
```

### 配置测试

创建测试配置来验证功能：

**测试配置** (`config/test_config.yaml`):
```yaml
# 测试环境配置
server:
  runtime:
    log_level: "DEBUG"
    max_sessions: 10
    session_timeout_minutes: 5
    
database:
  path: ":memory:"  # 使用内存数据库进行测试
  
templates:
  cache_enabled: false  # 禁用缓存以便测试
  hot_reload: false
  
flows:
  default_flow: "quick_analysis"  # 使用快速流程进行测试
```

## 故障排除

### 常见配置问题

1. **YAML语法错误**
   ```bash
   # 检查YAML语法
   python -c "import yaml; yaml.safe_load(open('config/mcp_server.yaml'))"
   ```

2. **路径配置错误**
   ```bash
   # 检查路径是否存在
   ls -la data/
   ls -la templates/
   ```

3. **权限问题**
   ```bash
   # 检查文件权限
   chmod 644 config/*.yaml
   chmod 755 data/
   ```

### 配置重置

如果配置出现问题，可以重置为默认配置：

```bash
# 备份当前配置
cp -r config config_backup

# 重置为默认配置
python scripts/reset_config.py

# 或者手动重置
rm config/*.yaml
python scripts/start_mcp_server.py --init-config
```

## 最佳实践

### 配置管理建议

1. **版本控制**: 将配置文件纳入版本控制
2. **环境分离**: 为不同环境使用不同的配置文件
3. **敏感信息**: 使用环境变量存储敏感配置
4. **文档化**: 为自定义配置添加注释说明
5. **测试验证**: 定期验证配置文件的正确性

### 性能优化配置

```yaml
# 高性能配置示例
server:
  performance:
    template_cache_size: 100      # 增大缓存
    session_cache_size: 50        # 增大会话缓存
    database_pool_size: 10        # 增大连接池
    
templates:
  cache:
    enabled: true
    size: 100
    ttl_minutes: 120              # 延长缓存时间
    
flows:
  parallel_processing:
    enabled: true
    max_parallel_steps: 5         # 增加并行步骤数
```

通过合理配置Deep Thinking Engine，您可以获得最佳的使用体验和性能表现。记住定期检查和更新配置，以适应不断变化的需求。