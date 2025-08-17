"""
Template Manager for Deep Thinking Engine

Provides dynamic loading, caching, and version management for templates.
Enhanced with performance optimization features.
"""

import json
import logging
import os
import re
import shutil
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from .parameter_replacer import ParameterReplacer, ParameterConfig, ReplacementContext, ParameterValidationError
from .performance_optimizer import TemplatePerformanceOptimizer

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Configuration error"""
    pass


class TemplateVersionError(Exception):
    """Template version error"""
    pass


class TemplateFileHandler(FileSystemEventHandler):
    """File system event handler for template files"""

    def __init__(self, template_manager):
        self.template_manager = template_manager
        self.last_reload_time = {}  # Track last reload time per file
        self.debounce_interval = 0.5  # seconds
        self.pending_reloads = set()  # Track pending reloads

    def on_modified(self, event):
        """Handle file modification events"""
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        if file_path.suffix != '.tmpl':
            return
            
        template_name = file_path.stem
        
        # Debounce to avoid multiple reloads for the same file
        current_time = time.time()
        last_time = self.last_reload_time.get(template_name, 0)
        if current_time - last_time < self.debounce_interval:
            # Add to pending reloads if we're debouncing
            self.pending_reloads.add(template_name)
            return
        
        # Update last reload time
        self.last_reload_time[template_name] = current_time
        
        # Remove from pending if it was there
        if template_name in self.pending_reloads:
            self.pending_reloads.remove(template_name)
        
        # Reload the template
        print(f"Hot reloading template: {template_name}")
        self.template_manager.reload_template(template_name)
        
    def on_created(self, event):
        """Handle file creation events"""
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        if file_path.suffix == '.tmpl':
            template_name = file_path.stem
            print(f"New template detected: {template_name}")
            self.template_manager.reload_template(template_name)


class TemplateManager:
    """Advanced template manager with dynamic loading, caching, and version management"""

    def __init__(self, templates_dir: str = "templates", enable_performance_optimization: bool = True):
        self.templates_dir = Path(templates_dir)
        self.cache: Dict[str, str] = {}
        self.metadata: Dict[str, Dict[str, Any]] = {}
        self.versions: Dict[str, List[Dict[str, Any]]] = {}  # Template version history
        self.usage_stats: Dict[str, int] = {}  # Template usage statistics
        self.lock = threading.RLock()
        self.hot_reload_enabled = False
        self.observer = None

        # Initialize parameter replacer
        self.parameter_replacer = ParameterReplacer()
        self._setup_parameter_configs()

        # Create templates directory and versions subdirectory
        self.templates_dir.mkdir(exist_ok=True)
        self.versions_dir = self.templates_dir / "versions"
        self.versions_dir.mkdir(exist_ok=True)
        
        # Initialize performance optimizer
        self.performance_optimizer = None
        if enable_performance_optimization:
            self.performance_optimizer = TemplatePerformanceOptimizer(
                self.templates_dir,
                cache_size=100,
                cache_memory_mb=50
            )
        
        # Scan for existing template files first
        self._scan_template_files()
        
        # Initialize built-in templates (only if they don't exist)
        self._create_builtin_templates()
        
        # Preload high-priority templates if optimizer is enabled
        if self.performance_optimizer:
            try:
                self.performance_optimizer.preload_high_priority_templates()
                logger.info("High-priority templates preloaded successfully")
            except Exception as e:
                logger.warning(f"Failed to preload templates: {e}")

    def _setup_parameter_configs(self):
        """Setup parameter configurations for common template parameters"""
        # Common parameters used across templates
        common_configs = [
            ParameterConfig(
                name="topic",
                required=True,
                description="The main topic or question to analyze",
                validator=self.parameter_replacer.validators['not_empty']
            ),
            ParameterConfig(
                name="complexity",
                required=False,
                default_value="moderate",
                description="Complexity level: low, moderate, high",
                validator=lambda x: str(x).lower() in ['low', 'moderate', 'high']
            ),
            ParameterConfig(
                name="focus",
                required=False,
                default_value="",
                description="Specific focus area or constraint"
            ),
            ParameterConfig(
                name="domain_context",
                required=False,
                default_value="general",
                description="Domain or field context for the analysis"
            ),
            ParameterConfig(
                name="sub_question",
                required=False,
                description="A specific sub-question to analyze"
            ),
            ParameterConfig(
                name="keywords",
                required=False,
                formatter=lambda x: ', '.join(x) if isinstance(x, list) else str(x),
                description="Search keywords for evidence collection"
            ),
            ParameterConfig(
                name="evidence_summary",
                required=False,
                formatter=self.parameter_replacer.formatters['truncate'],
                description="Summary of collected evidence"
            ),
            ParameterConfig(
                name="content",
                required=False,
                description="Content to be analyzed or evaluated"
            ),
            ParameterConfig(
                name="context",
                required=False,
                description="Additional context for the analysis"
            ),
            ParameterConfig(
                name="concept",
                required=False,
                description="Concept for innovation thinking"
            ),
            ParameterConfig(
                name="direction",
                required=False,
                default_value="general improvement",
                description="Direction for innovation"
            ),
            ParameterConfig(
                name="constraints",
                required=False,
                default_value="none specified",
                description="Constraints for innovation thinking"
            ),
            ParameterConfig(
                name="method",
                required=False,
                default_value="SCAMPER",
                description="Innovation method to use"
            ),
            ParameterConfig(
                name="thinking_history",
                required=False,
                formatter=self.parameter_replacer.formatters['truncate'],
                description="History of the thinking process"
            ),
            ParameterConfig(
                name="current_conclusions",
                required=False,
                description="Current conclusions reached"
            ),
        ]
        
        # Register all parameter configurations
        for config in common_configs:
            self.parameter_replacer.register_parameter_config(config)

    def _create_builtin_templates(self):
        """Create built-in templates and save them to the templates directory"""
        templates = {
            # Add a placeholder for bias_detection
            "bias_detection": "# 认知偏见检测模板",
            # Add a placeholder for innovation
            "innovation": "# 创新思维模板",
            # Add a placeholder for reflection
            "reflection": "# 反思引导模板",
            "decomposition_high": """# 深度思考：系统性问题分解（高复杂度）

你是一位专业的系统思维专家，擅长将复杂问题分解为可管理的组成部分。请对以下问题进行系统性分解：

**主要问题**: {topic}
**复杂度**: 高
**关注重点**: {focus}
**领域背景**: {domain_context}

## 复杂度自适应分解策略：

### 【高复杂度分解策略】
请使用以下多维度分解方法：
1. **系统层次分解**：将问题分解为宏观、中观、微观三个层次
2. **时间维度分解**：分析短期、中期、长期的不同阶段
3. **利益相关者分解**：识别并分析所有关键利益相关者的视角
4. **因果链分解**：分析根本原因、中间因素和最终结果
5. **跨领域分解**：从技术、经济、社会、政治、环境等多个领域分析
6. **风险维度分解**：识别潜在风险、不确定性和边界条件
7. **矛盾分析**：识别问题中的核心矛盾和冲突点

请生成5-7个深度子问题，确保全面覆盖问题空间，并建立详细的关系图。

## 分解要求：
1. 每个子问题必须具体、明确、可独立分析
2. 子问题之间应尽量减少重叠，保持相对独立性
3. 子问题集合必须完整覆盖原问题的核心方面
4. 明确标注子问题之间的依赖关系和优先级
5. 为每个子问题提供精确的搜索关键词和预期分析角度

## JSON输出格式规范：
```json
{
  "main_question": "原始主问题的准确描述",
  "complexity_level": "high",
  "decomposition_strategy": "系统层次分解",
  "sub_questions": [
    {
      "id": "SQ1",
      "question": "子问题1的具体描述",
      "priority": "high/medium/low",
      "search_keywords": ["关键词1", "关键词2", "关键词3"],
      "expected_perspectives": ["视角1", "视角2", "视角3"],
      "analysis_dimensions": ["维度1", "维度2"]
    },
    {
      "id": "SQ2",
      "question": "子问题2的具体描述",
      "priority": "high/medium/low",
      "search_keywords": ["关键词1", "关键词2", "关键词3"],
      "expected_perspectives": ["视角1", "视角2", "视角3"],
      "analysis_dimensions": ["维度1", "维度2"]
    }
    // 更多子问题...
  ],
  "relationships": [
    {
      "from": "SQ1",
      "to": "SQ2",
      "type": "depends_on/influences/contradicts/supports",
      "description": "关系的具体描述"
    }
    // 更多关系...
  ],
  "coverage_analysis": {
    "key_aspects_covered": ["方面1", "方面2", "方面3"],
    "potential_blind_spots": ["盲点1", "盲点2"]
  }
}
```

## 输出验证检查清单：
1. JSON格式是否完全符合规范？
   - 确保所有引号、括号、逗号正确
   - 移除所有注释行（如 "// 更多子问题..."）
   - 检查所有字段名和值格式是否正确

2. 子问题数量是否符合复杂度要求？
   - 高复杂度：5-7个子问题

3. 每个子问题是否都有完整的属性？
   - id：唯一标识符（如SQ1, SQ2等）
   - question：完整清晰的问题描述
   - priority：优先级（high/medium/low）
   - search_keywords：至少3个搜索关键词
   - expected_perspectives：至少2个分析视角
   - analysis_dimensions：至少2个分析维度

4. 关系描述是否清晰准确？
   - 每个子问题至少与一个其他子问题建立关系
   - 关系类型正确（depends_on/influences/contradicts/supports）
   - 关系描述具体明确

5. 是否覆盖了问题的所有关键方面？
   - coverage_analysis部分完整填写
   - 至少识别3个关键覆盖方面
   - 至少识别2个潜在盲点

请开始系统性问题分解：""",

            "decomposition_medium": """# 深度思考：系统性问题分解（中等复杂度）

你是一位专业的系统思维专家，擅长将复杂问题分解为可管理的组成部分。请对以下问题进行系统性分解：

**主要问题**: {topic}
**复杂度**: 中等
**关注重点**: {focus}
**领域背景**: {domain_context}

## 复杂度自适应分解策略：

### 【中等复杂度分解策略】
请使用以下多角度分解方法：
1. **MECE分解法**：相互独立、完全穷尽的分类方式
2. **时间序列分解**：按照问题发展的时间顺序分解
3. **利益相关者分析**：从主要相关方的角度分解问题
4. **因果分析**：识别主要原因和结果链
5. **领域分类**：按照不同专业领域分类分析

请生成4-6个核心子问题，确保覆盖问题的主要方面。

## 分解要求：
1. 每个子问题必须具体、明确、可独立分析
2. 子问题之间应尽量减少重叠，保持相对独立性
3. 子问题集合必须完整覆盖原问题的核心方面
4. 明确标注子问题之间的依赖关系和优先级
5. 为每个子问题提供精确的搜索关键词和预期分析角度

## JSON输出格式规范：
```json
{
  "main_question": "原始主问题的准确描述",
  "complexity_level": "medium",
  "decomposition_strategy": "MECE分解法",
  "sub_questions": [
    {
      "id": "SQ1",
      "question": "子问题1的具体描述",
      "priority": "high/medium/low",
      "search_keywords": ["关键词1", "关键词2", "关键词3"],
      "expected_perspectives": ["视角1", "视角2", "视角3"],
      "analysis_dimensions": ["维度1", "维度2"]
    },
    {
      "id": "SQ2",
      "question": "子问题2的具体描述",
      "priority": "high/medium/low",
      "search_keywords": ["关键词1", "关键词2", "关键词3"],
      "expected_perspectives": ["视角1", "视角2", "视角3"],
      "analysis_dimensions": ["维度1", "维度2"]
    }
    // 更多子问题...
  ],
  "relationships": [
    {
      "from": "SQ1",
      "to": "SQ2",
      "type": "depends_on/influences/contradicts/supports",
      "description": "关系的具体描述"
    }
    // 更多关系...
  ],
  "coverage_analysis": {
    "key_aspects_covered": ["方面1", "方面2", "方面3"],
    "potential_blind_spots": ["盲点1", "盲点2"]
  }
}
```

## 输出验证检查清单：
1. JSON格式是否完全符合规范？
   - 确保所有引号、括号、逗号正确
   - 移除所有注释行（如 "// 更多子问题..."）
   - 检查所有字段名和值格式是否正确

2. 子问题数量是否符合复杂度要求？
   - 中等复杂度：4-6个子问题

3. 每个子问题是否都有完整的属性？
   - id：唯一标识符（如SQ1, SQ2等）
   - question：完整清晰的问题描述
   - priority：优先级（high/medium/low）
   - search_keywords：至少3个搜索关键词
   - expected_perspectives：至少2个分析视角
   - analysis_dimensions：至少2个分析维度

4. 关系描述是否清晰准确？
   - 每个子问题至少与一个其他子问题建立关系
   - 关系类型正确（depends_on/influences/contradicts/supports）
   - 关系描述具体明确

5. 是否覆盖了问题的所有关键方面？
   - coverage_analysis部分完整填写
   - 至少识别3个关键覆盖方面
   - 至少识别2个潜在盲点

请开始系统性问题分解：""",

            "decomposition_low": """# 深度思考：系统性问题分解（基础复杂度）

你是一位专业的系统思维专家，擅长将复杂问题分解为可管理的组成部分。请对以下问题进行系统性分解：

**主要问题**: {topic}
**复杂度**: 低
**关注重点**: {focus}
**领域背景**: {domain_context}

## 复杂度自适应分解策略：

### 【基础分解策略】
请使用以下基本分解方法：
1. **5W1H分析法**：What(是什么)、Why(为什么)、Who(谁)、When(何时)、Where(何地)、How(如何)
2. **问题分类法**：将问题按照类型或领域进行分类
3. **优先级分解**：按照重要性和紧急性分解问题

请生成3-5个关键子问题，确保清晰简洁地覆盖核心问题。

## 分解要求：
1. 每个子问题必须具体、明确、可独立分析
2. 子问题之间应尽量减少重叠，保持相对独立性
3. 子问题集合必须完整覆盖原问题的核心方面
4. 明确标注子问题之间的依赖关系和优先级
5. 为每个子问题提供精确的搜索关键词和预期分析角度

## JSON输出格式规范：
```json
{
  "main_question": "原始主问题的准确描述",
  "complexity_level": "low",
  "decomposition_strategy": "5W1H分析法",
  "sub_questions": [
    {
      "id": "SQ1",
      "question": "子问题1的具体描述",
      "priority": "high/medium/low",
      "search_keywords": ["关键词1", "关键词2", "关键词3"],
      "expected_perspectives": ["视角1", "视角2", "视角3"],
      "analysis_dimensions": ["维度1", "维度2"]
    },
    {
      "id": "SQ2",
      "question": "子问题2的具体描述",
      "priority": "high/medium/low",
      "search_keywords": ["关键词1", "关键词2", "关键词3"],
      "expected_perspectives": ["视角1", "视角2", "视角3"],
      "analysis_dimensions": ["维度1", "维度2"]
    }
    // 更多子问题...
  ],
  "relationships": [
    {
      "from": "SQ1",
      "to": "SQ2",
      "type": "depends_on/influences/contradicts/supports",
      "description": "关系的具体描述"
    }
    // 更多关系...
  ],
  "coverage_analysis": {
    "key_aspects_covered": ["方面1", "方面2", "方面3"],
    "potential_blind_spots": ["盲点1", "盲点2"]
  }
}
```

## 输出验证检查清单：
1. JSON格式是否完全符合规范？
   - 确保所有引号、括号、逗号正确
   - 移除所有注释行（如 "// 更多子问题..."）
   - 检查所有字段名和值格式是否正确

2. 子问题数量是否符合复杂度要求？
   - 基础复杂度：3-5个子问题

3. 每个子问题是否都有完整的属性？
   - id：唯一标识符（如SQ1, SQ2等）
   - question：完整清晰的问题描述
   - priority：优先级（high/medium/low）
   - search_keywords：至少3个搜索关键词
   - expected_perspectives：至少2个分析视角
   - analysis_dimensions：至少2个分析维度

4. 关系描述是否清晰准确？
   - 每个子问题至少与一个其他子问题建立关系
   - 关系类型正确（depends_on/influences/contradicts/supports）
   - 关系描述具体明确

5. 是否覆盖了问题的所有关键方面？
   - coverage_analysis部分完整填写
   - 至少识别3个关键覆盖方面
   - 至少识别2个潜在盲点

请开始系统性问题分解：""",

            "decomposition": """# 深度思考：系统性问题分解

你是一位专业的系统思维专家，擅长将复杂问题分解为可管理的组成部分。请对以下问题进行系统性分解：

**主要问题**: {topic}
**复杂度**: {complexity}
**关注重点**: {focus}
**领域背景**: {domain_context}

## 复杂度自适应分解策略：

请根据问题复杂度选择适当的分解策略：

### 高复杂度问题分解策略
适用于复杂、多维度、系统性问题，请使用以下多维度分解方法：
1. **系统层次分解**：将问题分解为宏观、中观、微观三个层次
2. **时间维度分解**：分析短期、中期、长期的不同阶段
3. **利益相关者分解**：识别并分析所有关键利益相关者的视角
4. **因果链分解**：分析根本原因、中间因素和最终结果
5. **跨领域分解**：从技术、经济、社会、政治、环境等多个领域分析
6. **风险维度分解**：识别潜在风险、不确定性和边界条件
7. **矛盾分析**：识别问题中的核心矛盾和冲突点

对于高复杂度问题，请生成5-7个深度子问题，确保全面覆盖问题空间，并建立详细的关系图。

### 中等复杂度问题分解策略
适用于中等复杂度问题，请使用以下多角度分解方法：
1. **MECE分解法**：相互独立、完全穷尽的分类方式
2. **时间序列分解**：按照问题发展的时间顺序分解
3. **利益相关者分析**：从主要相关方的角度分解问题
4. **因果分析**：识别主要原因和结果链
5. **领域分类**：按照不同专业领域分类分析

对于中等复杂度问题，请生成4-6个核心子问题，确保覆盖问题的主要方面。

### 基础复杂度问题分解策略
适用于相对简单、明确的问题，请使用以下基本分解方法：
1. **5W1H分析法**：What(是什么)、Why(为什么)、Who(谁)、When(何时)、Where(何地)、How(如何)
2. **问题分类法**：将问题按照类型或领域进行分类
3. **优先级分解**：按照重要性和紧急性分解问题

对于基础复杂度问题，请生成3-5个关键子问题，确保清晰简洁地覆盖核心问题。

## 分解要求：
1. 每个子问题必须具体、明确、可独立分析
2. 子问题之间应尽量减少重叠，保持相对独立性
3. 子问题集合必须完整覆盖原问题的核心方面
4. 明确标注子问题之间的依赖关系和优先级
5. 为每个子问题提供精确的搜索关键词和预期分析角度

## JSON输出格式规范：
```json
{
  "main_question": "原始主问题的准确描述",
  "complexity_level": "high/medium/low",
  "decomposition_strategy": "使用的分解策略名称",
  "sub_questions": [
    {
      "id": "SQ1",
      "question": "子问题1的具体描述",
      "priority": "high/medium/low",
      "search_keywords": ["关键词1", "关键词2", "关键词3"],
      "expected_perspectives": ["视角1", "视角2", "视角3"],
      "analysis_dimensions": ["维度1", "维度2"]
    },
    {
      "id": "SQ2",
      "question": "子问题2的具体描述",
      "priority": "high/medium/low",
      "search_keywords": ["关键词1", "关键词2", "关键词3"],
      "expected_perspectives": ["视角1", "视角2", "视角3"],
      "analysis_dimensions": ["维度1", "维度2"]
    }
    // 更多子问题...
  ],
  "relationships": [
    {
      "from": "SQ1",
      "to": "SQ2",
      "type": "depends_on/influences/contradicts/supports",
      "description": "关系的具体描述"
    }
    // 更多关系...
  ],
  "coverage_analysis": {
    "key_aspects_covered": ["方面1", "方面2", "方面3"],
    "potential_blind_spots": ["盲点1", "盲点2"]
  }
}
```

## 输出验证检查清单：
1. JSON格式是否完全符合规范？
   - 确保所有引号、括号、逗号正确
   - 移除所有注释行（如 "// 更多子问题..."）
   - 检查所有字段名和值格式是否正确

2. 子问题数量是否符合复杂度要求？
   - 高复杂度：5-7个子问题
   - 中等复杂度：4-6个子问题
   - 基础复杂度：3-5个子问题

3. 每个子问题是否都有完整的属性？
   - id：唯一标识符（如SQ1, SQ2等）
   - question：完整清晰的问题描述
   - priority：优先级（high/medium/low）
   - search_keywords：至少3个搜索关键词
   - expected_perspectives：至少2个分析视角
   - analysis_dimensions：至少2个分析维度

4. 关系描述是否清晰准确？
   - 每个子问题至少与一个其他子问题建立关系
   - 关系类型正确（depends_on/influences/contradicts/supports）
   - 关系描述具体明确

5. 是否覆盖了问题的所有关键方面？
   - coverage_analysis部分完整填写
   - 至少识别3个关键覆盖方面
   - 至少识别2个潜在盲点

请开始系统性问题分解：""",
            "evidence_collection": """# 深度思考：证据收集

你现在需要为以下子问题收集全面、可靠的证据：

**子问题**: {{sub_question}}
**搜索关键词**: {{keywords}}
**证据要求**: 多样化来源，高可信度
**复杂度**: {{complexity}}

## 搜索策略指导：

### 1. 多源证据搜索策略
- **学术来源**: 搜索学术论文、研究报告、学位论文、会议论文
- **权威机构**: 政府报告、国际组织数据、行业标准、官方统计
- **新闻媒体**: 主流媒体报道、深度调查、案例分析、专题报道
- **专家观点**: 行业专家访谈、专业博客、演讲记录、专栏文章
- **行业资料**: 行业报告、白皮书、市场分析、技术文档
- **社区讨论**: 专业论坛、问答平台、社交媒体讨论(谨慎使用)

### 2. 证据质量要求
- **可靠性**: 优先选择经过同行评审或官方发布的信息
- **时效性**: 注意信息的发布时间，优先使用最新数据，同时保留历史数据作为比较
- **权威性**: 评估来源的专业背景和声誉
- **多样性**: 确保来源在地理、观点、领域上的多样性
- **透明度**: 优先选择方法论和数据来源透明的信息
- **相关性**: 确保证据与子问题直接相关

## 执行步骤：

1. **关键词优化**:
   - 扩展原始关键词，形成更精确的搜索词组
   - 考虑使用专业术语和同义词
   - 针对不同来源类型调整关键词策略

2. **系统性搜索**:
   - 使用你的Web搜索能力执行多轮搜索
   - 每轮搜索使用不同的关键词组合
   - 确保覆盖所有主要来源类型
   - 记录搜索过程和结果数量

3. **证据评估与筛选**:
   - 对每个来源进行可信度评分(1-10分)
   - 评估信息的完整性和准确性
   - 筛选出最相关、最可靠的证据
   - 确保证据集的多样性和平衡性

4. **冲突检测与处理**:
   - 主动识别相互矛盾的信息
   - 分析冲突的可能原因(方法差异、样本差异、时间差异等)
   - 标记争议点和不确定性
   - 提供多方观点的平衡呈现

5. **证据整合与结构化**:
   - 将收集的证据按主题或观点分类
   - 提取关键数据点和核心发现
   - 建立证据间的逻辑关联
   - 形成结构化的证据档案

## JSON输出格式规范：
```json
{
  "sub_question": "子问题的准确描述",
  "search_process": {
    "keywords_used": ["关键词1", "关键词2", "关键词3", "..."],
    "search_rounds": 3,
    "total_sources_reviewed": 15,
    "sources_selected": 8
  },
  "evidence_collection": [
    {
      "id": "E1",
      "source_type": "academic/official/news/expert/industry/community",
      "source_name": "来源名称",
      "author": "作者(如适用)",
      "publication_date": "发布日期",
      "url": "来源链接",
      "credibility_score": 8.5,
      "credibility_justification": "可信度评分理由",
      "key_findings": [
        "关键发现1",
        "关键发现2",
        "..."
      ],
      "relevant_quotes": [
        "相关引用1",
        "相关引用2",
        "..."
      ],
      "limitations": "该来源的局限性或潜在偏见"
    },
    {
      "id": "E2",
      "source_type": "academic/official/news/expert/industry/community",
      "source_name": "来源名称",
      "author": "作者(如适用)",
      "publication_date": "发布日期",
      "url": "来源链接",
      "credibility_score": 7.0,
      "credibility_justification": "可信度评分理由",
      "key_findings": [
        "关键发现1",
        "关键发现2",
        "..."
      ],
      "relevant_quotes": [
        "相关引用1",
        "相关引用2",
        "..."
      ],
      "limitations": "该来源的局限性或潜在偏见"
    }
  ],
  "conflict_analysis": [
    {
      "conflict_id": "C1",
      "topic": "冲突主题",
      "conflicting_evidence": ["E1", "E3"],
      "nature_of_conflict": "冲突的具体内容",
      "possible_explanations": [
        "可能的解释1",
        "可能的解释2"
      ],
      "resolution_approach": "如何处理或解释这一冲突"
    }
  ],
  "evidence_synthesis": {
    "main_findings": [
      "主要发现1",
      "主要发现2",
      "..."
    ],
    "consensus_points": [
      "各方共识点1",
      "各方共识点2",
      "..."
    ],
    "disputed_points": [
      "存在争议的观点1",
      "存在争议的观点2",
      "..."
    ],
    "evidence_gaps": [
      "证据缺口1",
      "证据缺口2",
      "..."
    ],
    "confidence_assessment": "对整体证据质量和结论可信度的评估"
  }
}
```

## 输出验证检查清单：
1. JSON格式是否完全符合规范？
   - 确保所有引号、括号、逗号正确
   - 移除所有注释行（如 "// 更多证据..."）
   - 检查所有字段名和值格式是否正确

2. 证据多样性是否充分？
   - 至少包含3种不同类型的来源
   - 来源发布时间应有一定跨度
   - 应包含不同观点或角度

3. 证据质量评估是否充分？
   - 每个来源都有合理的可信度评分
   - 评分理由具体且合理
   - 已标明来源的局限性

4. 冲突检测是否到位？
   - 已识别主要的证据冲突
   - 提供了冲突的可能解释
   - 给出了处理冲突的方法

5. 证据整合是否有效？
   - 主要发现清晰明确
   - 共识点和争议点分别列出
   - 对证据质量有整体评估

请开始系统性证据收集："""
        }

        # Save built-in templates to files and add to cache (only if they don't exist)
        for name, content in templates.items():
            # Only add if template doesn't already exist in cache (from file scan)
            if name not in self.cache:
                self.add_template(name, content, save_to_file=True)

    def add_template(self, name: str, template_content: str, save_to_file: bool = True):
        """
        Add a template to the manager
        
        Args:
            name: Template name
            template_content: Template content
            save_to_file: Whether to save the template to a file
        """
        with self.lock:
            # Create a new version entry
            version_id = str(uuid.uuid4())
            version_entry = {
                "version_id": version_id,
                "created_at": datetime.now().isoformat(),
                "content": template_content,
                "is_active": True
            }
            
            # Initialize version history if needed
            if name not in self.versions:
                self.versions[name] = []
            
            # Mark previous versions as inactive
            for version in self.versions[name]:
                version["is_active"] = False
            
            # Add the new version
            self.versions[name].append(version_entry)
            
            # Update cache and metadata
            self.cache[name] = template_content
            self.metadata[name] = {
                "added_at": datetime.now(),
                "size": len(template_content),
                "usage_count": 0,
                "current_version": version_id
            }
            
            # Save to file if requested
            if save_to_file:
                self._save_template_to_file(name, template_content, version_id)
    
    def _save_template_to_file(self, name: str, content: str, version_id: str):
        """Save a template to a file"""
        # Save the current version
        template_path = self.templates_dir / f"{name}.tmpl"
        template_path.write_text(content, encoding="utf-8")
        
        # Save version metadata
        version_meta = {
            "version_id": version_id,
            "created_at": datetime.now().isoformat(),
            "template_name": name
        }
        
        # Save to versions directory
        version_path = self.versions_dir / f"{name}_{version_id}.tmpl"
        version_path.write_text(content, encoding="utf-8")
        
        # Save version metadata
        version_meta_path = self.versions_dir / f"{name}_{version_id}.json"
        with open(version_meta_path, "w", encoding="utf-8") as f:
            json.dump(version_meta, f, indent=2)

    def get_template(
        self, 
        name: str, 
        params: Optional[Dict[str, Any]] = None, 
        context: Optional[ReplacementContext] = None,
        use_default_if_missing: bool = False
    ) -> str:
        """
        Get a template with parameters substituted
        
        Args:
            name: Template name
            params: Parameters to substitute in the template
            context: Replacement context with session info and variables
            use_default_if_missing: If True, return a default template if the requested one is not found
            
        Returns:
            Template with parameters substituted
        """
        if params is None:
            params = {}

        # Use performance optimizer if available
        if self.performance_optimizer:
            template = self.performance_optimizer.get_template(name, self._load_template_content)
            if template is None and not use_default_if_missing:
                raise ConfigurationError(f"Template '{name}' not found")
            elif template is None and use_default_if_missing:
                # Try fallback options
                fallback_template = self._get_fallback_template(name, params)
                if fallback_template:
                    logger.warning(f"Using fallback template for missing template '{name}'")
                    template = fallback_template
                else:
                    template = self._generate_generic_template(name, params)
        else:
            # Fallback to original implementation
            with self.lock:
                # Always check for file changes if hot reload is enabled
                if self.hot_reload_enabled and name in self.cache:
                    template_path = self.templates_dir / f"{name}.tmpl"
                    if template_path.exists():
                        # Check if file was modified since last load
                        last_modified = template_path.stat().st_mtime
                        last_loaded = self.metadata.get(name, {}).get("last_loaded_time", 0)
                        if last_modified > last_loaded:
                            self.reload_template(name)
                
                # Try to load from file if not in cache
                if name not in self.cache:
                    self._load_template_from_file(name)
                
                # If still not found, handle according to flag
                if name not in self.cache:
                    if use_default_if_missing:
                        # Try to find a suitable fallback template
                        fallback_template = self._get_fallback_template(name, params)
                        if fallback_template:
                            logger.warning(f"Using fallback template for missing template '{name}'")
                            return fallback_template
                        else:
                            # Return generic template as last resort
                            return self._generate_generic_template(name, params)
                    else:
                        raise ConfigurationError(f"Template '{name}' not found")

                template = self.cache[name]
                
                # Update usage statistics
                if name not in self.metadata:
                    self.metadata[name] = {"usage_count": 0}
                
                self.metadata[name]["usage_count"] = self.metadata[name].get("usage_count", 0) + 1
                self.metadata[name]["last_used"] = datetime.now()
                self.usage_stats[name] = self.usage_stats.get(name, 0) + 1

        # Use the advanced parameter replacer
        try:
            result = self.parameter_replacer.replace_parameters(template, params, context)
            return result
        except ParameterValidationError as e:
            # Log the validation error but continue with basic replacement
            print(f"Parameter validation warning for template '{name}': {e}")
            
            # Fallback to basic replacement
            for key, value in params.items():
                placeholder = "{" + key + "}"
                if value is None:
                    value = f"[{key}]"  # Use placeholder for None values
                template = template.replace(placeholder, str(value))

            # Replace any remaining {param} with [param]
            template = re.sub(r"{([^{}]+)}", r"[\1]", template)
            return template
    
    def _load_template_content(self, name: str) -> Optional[str]:
        """
        Load template content for performance optimizer
        
        Args:
            name: Template name
            
        Returns:
            Template content or None if not found
        """
        # First try to load from cache
        if name in self.cache:
            return self.cache[name]
        
        # Try to load from file
        if self._load_template_from_file(name):
            return self.cache.get(name)
        
        return None

    def _load_template_from_file(self, name: str) -> bool:
        """
        Load a template from file
        
        Args:
            name: Template name
            
        Returns:
            True if template was loaded, False otherwise
        """
        template_path = self.templates_dir / f"{name}.tmpl"
        
        if not template_path.exists():
            return False
        
        try:
            content = template_path.read_text(encoding="utf-8")
            
            # Get file modification time
            last_modified = template_path.stat().st_mtime
            
            # Create a new version entry
            version_id = str(uuid.uuid4())
            version_entry = {
                "version_id": version_id,
                "created_at": datetime.now().isoformat(),
                "content": content,
                "is_active": True,
                "loaded_from_file": True,
                "file_modified_time": last_modified
            }
            
            # Initialize version history if needed
            if name not in self.versions:
                self.versions[name] = []
            
            # Mark previous versions as inactive
            for version in self.versions[name]:
                version["is_active"] = False
            
            # Add the new version
            self.versions[name].append(version_entry)
            
            # Update cache and metadata
            self.cache[name] = content
            self.metadata[name] = {
                "added_at": datetime.now(),
                "size": len(content),
                "usage_count": 0,
                "current_version": version_id,
                "loaded_from_file": True,
                "last_loaded_time": last_modified
            }
            
            return True
        except Exception as e:
            print(f"Error loading template {name}: {e}")
            return False

    def list_templates(self) -> List[str]:
        """
        List all available templates
        
        Returns:
            List of template names
        """
        # First check for templates in the file system
        self._scan_template_files()
        
        with self.lock:
            return list(self.cache.keys())
    
    def _scan_template_files(self):
        """Scan the templates directory for template files"""
        if not self.templates_dir.exists():
            return
        
        for file_path in self.templates_dir.glob("*.tmpl"):
            template_name = file_path.stem
            if template_name not in self.cache:
                self._load_template_from_file(template_name)

    def get_usage_statistics(self) -> Dict[str, Any]:
        """
        Get usage statistics for templates
        
        Returns:
            Dictionary with usage statistics
        """
        with self.lock:
            stats = {
                "total_templates": len(self.cache),
                "total_usage": sum(
                    meta.get("usage_count", 0) for meta in self.metadata.values()
                ),
                "templates": {
                    name: {
                        "usage_count": meta.get("usage_count", 0),
                        "last_used": meta.get("last_used", None),
                        "current_version": meta.get("current_version", None)
                    }
                    for name, meta in self.metadata.items()
                },
            }
            return stats
    
    def reload_template(self, name: str) -> bool:
        """
        Reload a template from file
        
        Args:
            name: Template name
            
        Returns:
            True if template was reloaded, False otherwise
        """
        with self.lock:
            # Remove from cache to force reload
            if name in self.cache:
                del self.cache[name]
            
            # Force reload from file
            result = self._load_template_from_file(name)
            
            if result:
                print(f"Template '{name}' reloaded successfully")
            else:
                print(f"Failed to reload template '{name}'")
                
            return result
    
    def get_template_versions(self, name: str) -> List[Dict[str, Any]]:
        """
        Get version history for a template
        
        Args:
            name: Template name
            
        Returns:
            List of version entries
        """
        with self.lock:
            if name not in self.versions:
                raise ConfigurationError(f"Template '{name}' not found")
            
            # Return version info without the content to save memory
            return [
                {
                    "version_id": v["version_id"],
                    "created_at": v["created_at"],
                    "is_active": v["is_active"]
                }
                for v in self.versions[name]
            ]
    
    def rollback_template(self, name: str, version_id: str) -> bool:
        """
        Rollback a template to a previous version
        
        Args:
            name: Template name
            version_id: Version ID to rollback to
            
        Returns:
            True if rollback was successful, False otherwise
        """
        with self.lock:
            if name not in self.versions:
                raise ConfigurationError(f"Template '{name}' not found")
            
            # Find the version
            target_version = None
            for version in self.versions[name]:
                if version["version_id"] == version_id:
                    target_version = version
                    break
            
            if target_version is None:
                raise TemplateVersionError(f"Version '{version_id}' not found for template '{name}'")
            
            # Mark all versions as inactive
            for version in self.versions[name]:
                version["is_active"] = False
            
            # Mark the target version as active
            target_version["is_active"] = True
            
            # Update cache and metadata
            self.cache[name] = target_version["content"]
            self.metadata[name]["current_version"] = version_id
            
            # Save to file
            self._save_template_to_file(name, target_version["content"], version_id)
            
            return True
    
    def enable_hot_reload(self):
        """Enable hot reload for template files"""
        if self.observer is not None:
            # Already enabled
            return
        
        # Make sure the templates directory exists
        self.templates_dir.mkdir(exist_ok=True)
        
        # Create and start the observer
        self.hot_reload_enabled = True
        self.observer = Observer()
        event_handler = TemplateFileHandler(self)
        self.observer.schedule(event_handler, str(self.templates_dir), recursive=False)
        
        try:
            self.observer.start()
            print(f"Hot reload enabled for templates directory: {self.templates_dir}")
        except Exception as e:
            print(f"Error enabling hot reload: {e}")
            self.observer = None
            self.hot_reload_enabled = False
            raise
    
    def disable_hot_reload(self):
        """Disable hot reload for template files"""
        if self.observer is None:
            return
        
        self.hot_reload_enabled = False
        self.observer.stop()
        self.observer.join()
        self.observer = None
    
    def is_hot_reload_enabled(self) -> bool:
        """Check if hot reload is enabled"""
        return self.hot_reload_enabled
    
    def register_parameter_config(self, config: ParameterConfig):
        """Register a parameter configuration"""
        self.parameter_replacer.register_parameter_config(config)
    
    def register_formatter(self, name: str, formatter):
        """Register a custom formatter"""
        self.parameter_replacer.register_formatter(name, formatter)
    
    def register_validator(self, name: str, validator):
        """Register a custom validator"""
        self.parameter_replacer.register_validator(name, validator)
    
    def set_global_context(self, context: Dict[str, Any]):
        """Set global context variables"""
        self.parameter_replacer.set_global_context(context)
    
    def extract_template_parameters(self, name: str) -> List[str]:
        """Extract all parameter names from a template"""
        if name not in self.cache:
            self._load_template_from_file(name)
        
        if name not in self.cache:
            raise ConfigurationError(f"Template '{name}' not found")
        
        return self.parameter_replacer.extract_parameters(self.cache[name])
    
    def validate_template(self, name: str) -> Dict[str, Any]:
        """Validate a template and return analysis"""
        if name not in self.cache:
            self._load_template_from_file(name)
        
        if name not in self.cache:
            raise ConfigurationError(f"Template '{name}' not found")
        
        return self.parameter_replacer.validate_template(self.cache[name])
    
    def get_parameter_documentation(self) -> str:
        """Get documentation for all registered parameters"""
        return self.parameter_replacer.create_parameter_documentation()
    
    def test_parameter_replacement(
        self, 
        name: str, 
        params: Dict[str, Any], 
        context: Optional[ReplacementContext] = None
    ) -> Dict[str, Any]:
        """Test parameter replacement and return detailed results"""
        if name not in self.cache:
            self._load_template_from_file(name)
        
        if name not in self.cache:
            raise ConfigurationError(f"Template '{name}' not found")
        
        template = self.cache[name]
        
        # Extract parameters from template
        template_params = self.parameter_replacer.extract_parameters(template)
        
        # Validate template
        validation_result = self.parameter_replacer.validate_template(template)
        
        # Attempt replacement
        try:
            result = self.parameter_replacer.replace_parameters(template, params, context)
            replacement_success = True
            replacement_error = None
        except Exception as e:
            result = str(e)
            replacement_success = False
            replacement_error = str(e)
        
        return {
            'template_name': name,
            'template_parameters': template_params,
            'provided_parameters': list(params.keys()),
            'missing_parameters': [p for p in template_params if p not in params],
            'extra_parameters': [p for p in params.keys() if p not in template_params],
            'validation_result': validation_result,
            'replacement_success': replacement_success,
            'replacement_error': replacement_error,
            'result': result if replacement_success else None,
            'result_length': len(result) if replacement_success else 0
        }

    def _get_fallback_template(self, name: str, params: Dict[str, Any]) -> Optional[str]:
        """
        Get a suitable fallback template for a missing template
        
        Args:
            name: Name of the missing template
            params: Parameters that would be used with the template
            
        Returns:
            Fallback template content if found, None otherwise
        """
        # Define fallback mappings for common templates
        fallback_mappings = {
            # Specific templates can fall back to more general ones
            "advanced_decomposition": "decomposition",
            "advanced_critical_evaluation": "critical_evaluation",
            "comprehensive_evidence_collection": "evidence_collection",
            "detailed_bias_detection": "bias_detection",
            "enhanced_innovation": "innovation",
            "deep_reflection": "reflection",
            
            # Analysis templates can fall back to generic analysis
            "analyze_decomposition": "generic_analysis",
            "analyze_evidence": "generic_analysis", 
            "analyze_debate": "generic_analysis",
            "analyze_evaluation": "generic_analysis",
            "analyze_reflection": "generic_analysis",
            
            # Step-specific templates can fall back to generic step template
            "step_guidance": "generic_step",
            "step_instructions": "generic_step",
        }
        
        # Try direct fallback mapping first
        fallback_name = fallback_mappings.get(name)
        if fallback_name and fallback_name in self.cache:
            logger.info(f"Using fallback template '{fallback_name}' for missing template '{name}'")
            return self.cache[fallback_name]
        
        # Try to find templates with similar names
        similar_templates = self._find_similar_templates(name)
        if similar_templates:
            best_match = similar_templates[0]
            logger.info(f"Using similar template '{best_match}' for missing template '{name}'")
            return self.cache[best_match]
        
        # Try category-based fallbacks
        category_fallbacks = {
            "decompos": "decomposition",
            "evidence": "evidence_collection", 
            "debate": "debate",
            "evaluat": "critical_evaluation",
            "bias": "bias_detection",
            "innovat": "innovation",
            "reflect": "reflection",
            "analyz": "generic_analysis"
        }
        
        for keyword, fallback_template in category_fallbacks.items():
            if keyword in name.lower() and fallback_template in self.cache:
                logger.info(f"Using category fallback template '{fallback_template}' for missing template '{name}'")
                return self.cache[fallback_template]
        
        return None

    def _find_similar_templates(self, name: str) -> List[str]:
        """
        Find templates with similar names to the missing template
        
        Args:
            name: Name of the missing template
            
        Returns:
            List of similar template names, sorted by similarity
        """
        similar_templates = []
        name_lower = name.lower()
        
        for template_name in self.cache.keys():
            template_lower = template_name.lower()
            
            # Calculate similarity score
            similarity_score = 0
            
            # Exact substring match gets high score
            if name_lower in template_lower or template_lower in name_lower:
                similarity_score += 10
            
            # Common words get medium score
            name_words = set(name_lower.split('_'))
            template_words = set(template_lower.split('_'))
            common_words = name_words.intersection(template_words)
            similarity_score += len(common_words) * 3
            
            # Similar length gets small bonus
            length_diff = abs(len(name) - len(template_name))
            if length_diff < 5:
                similarity_score += 1
            
            if similarity_score > 0:
                similar_templates.append((template_name, similarity_score))
        
        # Sort by similarity score (descending)
        similar_templates.sort(key=lambda x: x[1], reverse=True)
        
        # Return just the template names
        return [template[0] for template in similar_templates[:3]]

    def _generate_generic_template(self, name: str, params: Dict[str, Any]) -> str:
        """
        Generate a generic template as a last resort fallback
        
        Args:
            name: Name of the missing template
            params: Parameters that would be used with the template
            
        Returns:
            Generic template content
        """
        logger.warning(f"Generating generic template for missing template '{name}'")
        
        # Determine template type from name
        template_type = self._determine_template_type(name)
        
        # Generate appropriate generic template
        if template_type == "analysis":
            return self._generate_generic_analysis_template(name, params)
        elif template_type == "step":
            return self._generate_generic_step_template(name, params)
        elif template_type == "evaluation":
            return self._generate_generic_evaluation_template(name, params)
        else:
            return self._generate_basic_generic_template(name, params)

    def _determine_template_type(self, name: str) -> str:
        """Determine the type of template based on its name"""
        name_lower = name.lower()
        
        if any(word in name_lower for word in ["evaluat", "assess", "review"]):
            return "evaluation"
        elif any(word in name_lower for word in ["step", "instruct", "guid", "direct"]):
            return "step"
        elif any(word in name_lower for word in ["decompos", "evidence", "debate", "bias", "innovat", "reflect", "analyz", "analysis"]):
            return "analysis"
        else:
            return "generic"

    def _generate_generic_analysis_template(self, name: str, params: Dict[str, Any]) -> str:
        """Generate a generic analysis template"""
        topic = params.get("topic", "the given topic")
        context = params.get("context", "")
        
        return f"""
# 通用分析框架

**注意**: 原始模板 '{name}' 不可用，使用通用分析框架。

## 分析目标
请对 {topic} 进行深入分析。

## 分析步骤

### 1. 问题理解
- 明确分析的核心问题
- 识别关键要素和变量
- 确定分析的范围和边界

### 2. 信息收集
- 收集相关的事实和数据
- 查找权威来源和参考资料
- 整理和组织收集到的信息

### 3. 多角度分析
- 从不同角度审视问题
- 考虑各种可能的解释和观点
- 识别潜在的偏见和局限性

### 4. 逻辑推理
- 基于收集的信息进行推理
- 识别因果关系和关联性
- 评估不同观点的合理性

### 5. 结论总结
- 综合分析结果
- 提出明确的结论和建议
- 指出不确定性和需要进一步研究的领域

## 输出要求
- 结构清晰，逻辑连贯
- 有充分的证据支撑
- 考虑多个角度和观点
- 结论明确，建议可行

请按照以上框架进行分析。
"""

    def _generate_generic_step_template(self, name: str, params: Dict[str, Any]) -> str:
        """Generate a generic step template"""
        step_name = params.get("step_name", name.replace("_", " "))
        
        return f"""
# 步骤指导: {step_name}

**注意**: 原始模板 '{name}' 不可用，使用通用步骤指导。

## 步骤目标
完成 {step_name} 相关的任务。

## 执行指导

### 准备阶段
1. 明确当前步骤的具体目标
2. 回顾之前步骤的结果和发现
3. 确定本步骤需要的资源和信息

### 执行阶段
1. 按照步骤要求进行操作
2. 注意保持逻辑清晰和结构完整
3. 记录重要的发现和洞察

### 验证阶段
1. 检查结果是否符合要求
2. 验证逻辑的一致性和完整性
3. 确保为下一步骤做好准备

## 质量标准
- 完整性: 覆盖所有必要的方面
- 准确性: 信息和分析准确可靠
- 清晰性: 表达清楚，易于理解
- 相关性: 与整体目标保持一致

请按照以上指导完成当前步骤。
"""

    def _generate_generic_evaluation_template(self, name: str, params: Dict[str, Any]) -> str:
        """Generate a generic evaluation template"""
        content = params.get("content", "提供的内容")
        
        return f"""
# 通用评估框架

**注意**: 原始模板 '{name}' 不可用，使用通用评估框架。

## 评估对象
{content}

## 评估维度

### 1. 内容质量 (1-10分)
- 信息的准确性和可靠性
- 内容的完整性和全面性
- 论证的深度和细节
- 评分: ___/10分，理由:

### 2. 逻辑结构 (1-10分)
- 推理过程的逻辑性
- 结构的清晰性和条理性
- 论点之间的连贯性
- 评分: ___/10分，理由:

### 3. 证据支撑 (1-10分)
- 证据的充分性
- 来源的权威性和可信度
- 证据与结论的相关性
- 评分: ___/10分，理由:

### 4. 分析深度 (1-10分)
- 分析的深入程度
- 对复杂性的处理
- 细节的关注度
- 评分: ___/10分，理由:

### 5. 客观性 (1-10分)
- 观点的平衡性
- 偏见的控制
- 多角度的考虑
- 评分: ___/10分，理由:

## 总体评估
- 综合得分: ___/50分
- 主要优势:
- 改进建议:
- 是否需要重新分析: 是/否

请按照以上框架进行详细评估。
"""

    def _generate_basic_generic_template(self, name: str, params: Dict[str, Any]) -> str:
        """Generate a basic generic template"""
        return f"""
# 通用模板

**注意**: 原始模板 '{name}' 不可用，使用基础通用模板。

## 任务说明
请完成与 '{name}' 相关的任务。

## 基本要求
1. 明确任务目标和要求
2. 收集必要的信息和资料
3. 进行系统性的分析和思考
4. 提供清晰的结论和建议

## 输出格式
请按照以下结构组织你的回答：

### 问题分析
- 核心问题是什么？
- 涉及哪些关键要素？

### 信息收集
- 收集了哪些相关信息？
- 信息来源是否可靠？

### 分析过程
- 使用了什么分析方法？
- 考虑了哪些不同角度？

### 结论建议
- 得出了什么结论？
- 有什么具体建议？

请按照以上框架完成任务。
"""

    def detect_missing_templates(self) -> Dict[str, Any]:
        """
        Detect missing templates that are commonly needed
        
        Returns:
            Dictionary with information about missing templates
        """
        expected_templates = {
            # Core thinking templates
            "decomposition": "问题分解模板",
            "evidence_collection": "证据收集模板", 
            "debate": "多角度辩论模板",
            "critical_evaluation": "批判性评估模板",
            "bias_detection": "偏见检测模板",
            "innovation": "创新思维模板",
            "reflection": "反思引导模板",
            
            # Analysis templates
            "generic_analysis": "通用分析模板",
            "analyze_decomposition": "分解分析模板",
            "analyze_evidence": "证据分析模板",
            "analyze_debate": "辩论分析模板",
            "analyze_evaluation": "评估分析模板",
            "analyze_reflection": "反思分析模板",
            
            # Utility templates
            "session_recovery": "会话恢复模板",
            "comprehensive_summary": "综合总结模板",
            "flow_completion": "流程完成模板",
            "generic_step": "通用步骤模板",
        }
        
        missing_templates = []
        available_templates = []
        
        for template_name, description in expected_templates.items():
            if template_name in self.cache:
                available_templates.append({
                    "name": template_name,
                    "description": description,
                    "status": "available"
                })
            else:
                # Check if template file exists but not loaded
                template_path = self.templates_dir / f"{template_name}.tmpl"
                if template_path.exists():
                    available_templates.append({
                        "name": template_name,
                        "description": description,
                        "status": "not_loaded"
                    })
                else:
                    missing_templates.append({
                        "name": template_name,
                        "description": description,
                        "status": "missing",
                        "fallback_available": self._get_fallback_template(template_name, {}) is not None
                    })
        
        return {
            "missing_templates": missing_templates,
            "available_templates": available_templates,
            "total_expected": len(expected_templates),
            "total_missing": len(missing_templates),
            "missing_percentage": (len(missing_templates) / len(expected_templates)) * 100
        }

    def repair_missing_template(self, template_name: str, template_content: Optional[str] = None) -> bool:
        """
        Repair a missing template by creating it or reloading it
        
        Args:
            template_name: Name of the template to repair
            template_content: Optional content to use for the template
            
        Returns:
            True if repair successful, False otherwise
        """
        try:
            template_path = self.templates_dir / f"{template_name}.tmpl"
            
            # If template file exists but not loaded, try to reload
            if template_path.exists() and template_name not in self.cache:
                logger.info(f"Reloading existing template file: {template_name}")
                self._load_template_from_file(template_name)
                return template_name in self.cache
            
            # If template content provided, create the template file
            if template_content:
                logger.info(f"Creating missing template: {template_name}")
                template_path.write_text(template_content, encoding='utf-8')
                self._load_template_from_file(template_name)
                return template_name in self.cache
            
            # Try to generate a generic template
            if template_name not in self.cache:
                logger.info(f"Generating generic template for: {template_name}")
                generic_content = self._generate_generic_template(template_name, {})
                template_path.write_text(generic_content, encoding='utf-8')
                self._load_template_from_file(template_name)
                return template_name in self.cache
            
            return False
            
        except Exception as e:
            logger.error(f"Error repairing template {template_name}: {e}")
            return False

    def auto_repair_missing_templates(self) -> Dict[str, Any]:
        """
        Automatically repair commonly missing templates
        
        Returns:
            Dictionary with repair results
        """
        missing_info = self.detect_missing_templates()
        repair_results = {
            "attempted": [],
            "successful": [],
            "failed": [],
            "total_repaired": 0
        }
        
        for template_info in missing_info["missing_templates"]:
            template_name = template_info["name"]
            repair_results["attempted"].append(template_name)
            
            if self.repair_missing_template(template_name):
                repair_results["successful"].append(template_name)
                repair_results["total_repaired"] += 1
                logger.info(f"Successfully repaired template: {template_name}")
            else:
                repair_results["failed"].append(template_name)
                logger.warning(f"Failed to repair template: {template_name}")
        
        return repair_results

    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive performance metrics
        
        Returns:
            Dictionary with performance metrics
        """
        metrics = {
            "template_manager_stats": {
                "total_templates": len(self.cache),
                "templates_with_versions": len(self.versions),
                "hot_reload_enabled": self.hot_reload_enabled,
                "usage_stats": dict(self.usage_stats)
            }
        }
        
        # Add performance optimizer metrics if available
        if self.performance_optimizer:
            optimizer_metrics = self.performance_optimizer.get_performance_metrics()
            metrics.update(optimizer_metrics)
        
        return metrics
    
    def optimize_performance(self):
        """Optimize template performance"""
        if self.performance_optimizer:
            try:
                # Run cache optimization
                self.performance_optimizer.optimize_cache()
                
                # Preload high-priority templates
                self.performance_optimizer.preload_high_priority_templates()
                
                logger.info("Template performance optimization completed")
            except Exception as e:
                logger.error(f"Error during performance optimization: {e}")
        else:
            logger.warning("Performance optimizer not enabled")
    
    def preload_templates(self, template_names: Optional[List[str]] = None) -> Dict[str, bool]:
        """
        Preload templates for better performance
        
        Args:
            template_names: Specific templates to preload, or None for high-priority templates
            
        Returns:
            Dict mapping template names to success status
        """
        if self.performance_optimizer:
            if template_names is None:
                return self.performance_optimizer.preload_high_priority_templates()
            else:
                return self.performance_optimizer.preloader.preload_templates(template_names)
        else:
            logger.warning("Performance optimizer not enabled")
            return {}
    
    def clear_performance_cache(self):
        """Clear performance cache"""
        if self.performance_optimizer:
            self.performance_optimizer.cache.clear()
            logger.info("Performance cache cleared")
        else:
            logger.warning("Performance optimizer not enabled")
    
    def reset_performance_statistics(self):
        """Reset performance statistics"""
        if self.performance_optimizer:
            self.performance_optimizer.reset_statistics()
            logger.info("Performance statistics reset")
        else:
            logger.warning("Performance optimizer not enabled")
    
    def shutdown(self):
        """Shutdown the template manager and cleanup resources"""
        try:
            # Stop hot reload monitoring
            if self.observer and self.observer.is_alive():
                self.observer.stop()
                self.observer.join(timeout=5.0)
            
            # Shutdown performance optimizer
            if self.performance_optimizer:
                self.performance_optimizer.shutdown()
            
            logger.info("Template manager shutdown complete")
        except Exception as e:
            logger.error(f"Error during template manager shutdown: {e}")