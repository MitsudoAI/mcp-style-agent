"""
Template Manager for Deep Thinking Engine

Provides dynamic loading, caching, and version management for templates.
"""

import json
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

    def __init__(self, templates_dir: str = "templates"):
        self.templates_dir = Path(templates_dir)
        self.cache: Dict[str, str] = {}
        self.metadata: Dict[str, Dict[str, Any]] = {}
        self.versions: Dict[str, List[Dict[str, Any]]] = {}  # Template version history
        self.usage_stats: Dict[str, int] = {}  # Template usage statistics
        self.lock = threading.RLock()
        self.hot_reload_enabled = False
        self.observer = None

        # Create templates directory and versions subdirectory
        self.templates_dir.mkdir(exist_ok=True)
        self.versions_dir = self.templates_dir / "versions"
        self.versions_dir.mkdir(exist_ok=True)
        
        # Initialize built-in templates
        self._create_builtin_templates()

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

        # Save built-in templates to files and add to cache
        for name, content in templates.items():
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

    def get_template(self, name: str, params: Optional[Dict[str, Any]] = None, use_default_if_missing: bool = False) -> str:
        """
        Get a template with parameters substituted
        
        Args:
            name: Template name
            params: Parameters to substitute in the template
            use_default_if_missing: If True, return a default template if the requested one is not found
            
        Returns:
            Template with parameters substituted
        """
        if params is None:
            params = {}

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
                    return f"Template not found: {name}. This is a default placeholder."
                else:
                    raise ConfigurationError(f"Template '{name}' not found")

            template = self.cache[name]
            
            # Update usage statistics
            if name not in self.metadata:
                self.metadata[name] = {"usage_count": 0}
            
            self.metadata[name]["usage_count"] = self.metadata[name].get("usage_count", 0) + 1
            self.metadata[name]["last_used"] = datetime.now()
            self.usage_stats[name] = self.usage_stats.get(name, 0) + 1

        # Replace parameters in the template
        for key, value in params.items():
            placeholder = "{" + key + "}"
            if value is None:
                value = f"[{key}]"  # Use placeholder for None values
            template = template.replace(placeholder, str(value))

        # Replace any remaining {param} with [param]
        template = re.sub(r"{([^{}]+)}", r"[\1]", template)

        return template
    
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