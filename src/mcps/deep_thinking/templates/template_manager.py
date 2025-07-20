"""
Template Manager for Deep Thinking Engine
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
import threading
from datetime import datetime
import re


class ConfigurationError(Exception):
    """Configuration error"""
    pass


class TemplateManager:
    """Simple template manager with caching"""
    
    def __init__(self, templates_dir: str = "templates"):
        self.templates_dir = Path(templates_dir)
        self.cache: Dict[str, str] = {}
        self.metadata: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.RLock()
        
        self.templates_dir.mkdir(exist_ok=True)
        self._create_builtin_templates()
    
    def _create_builtin_templates(self):
        """Create built-in templates"""
        templates = {
            "decomposition": """# 深度思考：问题分解

你是一位专业的问题分析专家。请将以下复杂问题分解为可管理的子问题：

**主要问题**: {topic}
**复杂度**: {complexity}
**关注重点**: {focus}
**领域背景**: {domain_context}

## 分解要求：
1. 将主问题分解为3-7个核心子问题
2. 每个子问题应该相对独立且可深入分析
3. 确保覆盖问题的不同角度和层面
4. 识别子问题之间的依赖关系

## 输出格式：
请以JSON格式输出，包含：
- main_question: 主要问题
- sub_questions: 子问题列表，每个包含：
  - id: 唯一标识
  - question: 子问题描述
  - priority: high/medium/low
  - search_keywords: 搜索关键词列表
  - expected_perspectives: 预期分析角度
- relationships: 子问题间的依赖关系

开始分解：""",
            "evidence_collection": """# 深度思考：证据收集

你现在需要为以下子问题收集全面、可靠的证据：

**子问题**: {sub_question}
**搜索关键词**: {keywords}
**证据要求**: 多样化来源，高可信度

## 搜索策略：
1. **学术来源**: 搜索学术论文、研究报告
2. **权威机构**: 政府报告、国际组织数据
3. **新闻媒体**: 最新发展和案例分析
4. **专家观点**: 行业专家的分析和评论

## 请执行以下步骤：
1. 使用你的Web搜索能力查找相关信息
2. 评估每个来源的可信度
3. 提取关键事实和数据
4. 识别相互冲突的信息

## 输出格式：
请整理为结构化的证据集合，包含来源、可信度评分、关键发现等。

开始搜索和分析：""",
            "critical_evaluation": """# 深度思考：批判性评估

请基于Paul-Elder批判性思维标准评估以下内容：

**评估内容**: {content}
**评估背景**: {context}

## Paul-Elder九大标准评估：

### 1. 准确性 (Accuracy)
- 信息是否准确无误？
- 有无事实错误？
- 评分：1-10分，理由：

### 2. 精确性 (Precision)  
- 表述是否具体明确？
- 有无模糊不清之处？
- 评分：1-10分，理由：

### 3. 相关性 (Relevance)
- 内容是否与主题相关？
- 有无偏离核心问题？
- 评分：1-10分，理由：

### 4. 逻辑性 (Logic)
- 推理是否合乎逻辑？
- 有无逻辑谬误？
- 评分：1-10分，理由：

### 5. 广度 (Breadth)
- 是否考虑了多个角度？
- 视野是否足够宽广？
- 评分：1-10分，理由：

### 6. 深度 (Depth)
- 分析是否深入透彻？
- 是否触及根本问题？
- 评分：1-10分，理由：

### 7. 重要性 (Significance)
- 关注的是否为核心问题？
- 优先级是否合理？
- 评分：1-10分，理由：

### 8. 公正性 (Fairness)
- 是否存在偏见？
- 对不同观点是否公平？
- 评分：1-10分，理由：

### 9. 清晰性 (Clarity)
- 表达是否清晰易懂？
- 结构是否条理清楚？
- 评分：1-10分，理由：

## 总体评估：
- 综合得分：___/90分
- 主要优势：
- 改进建议：
- 是否需要重新分析：是/否

请开始详细评估：""",
            "session_recovery": """# 会话恢复

抱歉，之前的思考会话似乎中断了。让我们重新开始：

**会话ID**: {session_id}

请选择以下选项之一：
1. 重新开始完整的深度思考流程
2. 从特定步骤继续（如果你记得之前的进展）
3. 进行快速分析

请告诉我你希望如何继续：""",
            "error_recovery": """# 错误恢复

在执行 {tool_name} 工具时发生了错误：

**错误信息**: {error_message}
**会话ID**: {session_id}

请选择以下恢复选项：
1. 重新尝试当前操作
2. 跳过当前步骤继续
3. 重新开始思考流程
4. 结束当前会话

请告诉我你希望如何处理：""",
            "comprehensive_summary": """# 深度思考总结报告

## 思考主题
{topic}

## 思考历程
{step_summary}

## 请生成综合报告：

### 1. 核心发现
- 主要结论：
- 关键洞察：
- 重要发现：

### 2. 证据支撑
- 最有力的证据：
- 证据质量评估：
- 不确定性分析：

### 3. 多角度分析
- 支持观点：
- 反对观点：
- 中立分析：

### 4. 质量评估
- 思维过程评价：{quality_metrics}
- 改进建议：

### 5. 最终洞察
{final_insights}

请生成详细的综合报告：""",
            "reflection": """# 深度思考：苏格拉底式反思

现在让我们对整个思考过程进行深度反思：

**思考主题**: {topic}
**思考历程**: {thinking_history}
**当前结论**: {current_conclusions}

## 苏格拉底式提问：

### 🤔 过程反思 (Process Reflection)
1. **我是如何得出这些结论的？**
   - 我使用了哪些思维方法？
   - 我的推理过程是否合理？
   - 反思：

2. **我考虑了哪些角度？**
   - 是否遗漏了重要视角？
   - 不同利益相关者的观点如何？
   - 反思：

3. **我的证据是否充分？**
   - 证据的质量和可信度如何？
   - 是否存在相互矛盾的证据？
   - 反思：

### �� 结果反思 (Outcome Reflection)
4. **我的结论有多确定？**
   - 哪些部分我很确信？
   - 哪些部分还存在不确定性？
   - 反思：

5. **如果我错了会怎样？**
   - 最坏的情况是什么？
   - 如何降低错误的风险？
   - 反思：

6. **还有其他可能的解释吗？**
   - 是否存在我没有考虑的替代方案？
   - 如何验证我的结论？
   - 反思：

### 🧠 元认知反思 (Metacognitive Reflection)
7. **我的思维模式如何？**
   - 我倾向于使用哪些思维方式？
   - 我有哪些思维盲点？
   - 反思：

8. **我学到了什么？**
   - 这次思考让我获得了什么新见解？
   - 我的思维能力有何提升？
   - 反思：

9. **下次如何改进？**
   - 我可以在哪些方面做得更好？
   - 需要培养哪些新的思维技能？
   - 反思：

## 最终总结：
- **核心洞察**：
- **主要收获**：
- **行动计划**：
- **持续思考的问题**：

请开始深度反思：""",
            "improvement_guidance": """# 步骤改进指导

当前步骤的质量需要提升。请根据以下指导进行改进：

**当前步骤**: {step_name}
**质量评分**: {quality_score}
**改进建议**: {improvement_suggestions}

## 改进要点：
1. **内容完整性**: 确保回答涵盖所有要求的方面
2. **逻辑清晰性**: 检查推理过程是否合理连贯
3. **证据支撑**: 加强事实依据和引用来源
4. **深度分析**: 避免表面化，深入探讨核心问题

## 具体改进方向：
{specific_improvements}

请重新完成当前步骤，注意以上改进要点：""",
            "flow_completion": """# 思维流程完成

恭喜！你已经完成了深度思考的主要流程。

**会话ID**: {session_id}
**完成时间**: {completion_time}

现在可以：
1. 调用complete_thinking工具生成最终综合报告
2. 回顾整个思考过程的关键洞察
3. 开始新的深度思考会话

请选择你希望进行的下一步操作："""
        }
        
        # Store templates in cache
        for name, content in templates.items():
            self.cache[name] = content
            self.metadata[name] = {
                'builtin': True,
                'usage_count': 0,
                'last_used': None
            }
    
    def get_template(self, template_name: str, parameters: Optional[Dict[str, Any]] = None) -> str:
        """Get template with parameter substitution"""
        if template_name not in self.cache:
            raise ConfigurationError(f"Template not found: {template_name}")
        
        template_content = self.cache[template_name]
        
        # Update usage stats
        with self.lock:
            if template_name in self.metadata:
                self.metadata[template_name]['usage_count'] += 1
                self.metadata[template_name]['last_used'] = datetime.now()
        
        # Parameter substitution
        if parameters:
            safe_params = {}
            for key, value in parameters.items():
                safe_params[key] = str(value) if value is not None else ""
            
            # Find template variables
            template_vars = re.findall(r'\{(\w+)\}', template_content)
            
            # Provide defaults for missing variables
            for var in template_vars:
                if var not in safe_params:
                    safe_params[var] = f"[{var}]"
            
            try:
                return template_content.format(**safe_params)
            except Exception:
                return template_content
        
        return template_content
    
    def list_templates(self) -> List[str]:
        """List all available templates"""
        return list(self.cache.keys())
    
    def add_template(self, template_name: str, template_content: str) -> None:
        """Add a new template"""
        self.cache[template_name] = template_content
        self.metadata[template_name] = {
            'builtin': False,
            'usage_count': 0,
            'last_used': None
        }
    
    def get_usage_statistics(self) -> Dict[str, Any]:
        """Get usage statistics"""
        total_usage = sum(meta.get('usage_count', 0) for meta in self.metadata.values())
        
        return {
            'total_templates': len(self.cache),
            'total_usage': total_usage
        }
