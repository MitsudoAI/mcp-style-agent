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
            "comprehensive_summary": """# 深度思考综合报告

## 📋 会话信息
- **思考主题**: {topic}
- **流程类型**: {flow_type}
- **完成时间**: {completion_timestamp}
- **会话时长**: {session_duration}
- **总步骤数**: {total_steps}
- **整体评估**: {overall_assessment}

## 🔄 思考历程回顾
{step_summary}

## 📊 质量分析报告
{quality_metrics}

## 🎯 请生成详细的综合报告：

### 1. 🔍 核心发现与洞察
请基于整个思考过程，总结出最重要的发现：
- **主要结论**: 基于证据和分析得出的核心结论
- **关键洞察**: 思考过程中产生的重要洞察
- **意外发现**: 超出预期的重要发现
- **深层理解**: 对问题本质的深层理解

### 2. 📚 证据与支撑分析
请评估和总结证据基础：
- **最有力的证据**: 支撑结论的最强证据
- **证据质量评估**: 整体证据的可信度和完整性
- **证据缺口分析**: 识别证据不足的领域
- **不确定性分析**: 结论中存在的不确定性

### 3. 🔄 多角度综合分析
请整合不同视角的分析结果：
- **支持观点汇总**: 支持主要结论的观点和论据
- **反对观点汇总**: 质疑或反对的观点和论据
- **中立分析汇总**: 客观平衡的分析观点
- **观点整合**: 如何整合不同观点形成综合判断

### 4. 🎨 创新思维成果
如果包含创新思维环节，请总结：
- **创新想法**: 产生的新颖想法或解决方案
- **可行性评估**: 创新想法的实施可行性
- **潜在影响**: 创新方案可能带来的影响
- **实施建议**: 具体的实施路径和建议

### 5. 🤔 反思与元认知
请进行深度反思：
- **思维过程评价**: 对整个思考过程的评价
- **方法论反思**: 使用的思维方法的有效性
- **认知盲点识别**: 发现的思维盲点和局限
- **学习收获**: 从这次思考中获得的学习

### 6. 📈 质量改进建议
基于质量分析，提供改进建议：
- **改进优先级**: {improvement_areas}
- **最佳实践**: 本次思考中的最佳实践（最佳步骤: {best_step}）
- **避免陷阱**: 需要避免的思维陷阱
- **持续改进**: 未来思考的改进方向

### 7. 🎯 行动建议与后续思考
请提供具体的行动指导：
- **立即行动**: 基于结论可以立即采取的行动
- **中期规划**: 需要进一步规划的中期行动
- **持续关注**: 需要持续关注和思考的问题
- **知识缺口**: 需要进一步学习和研究的领域

### 8. 💡 最终洞察与总结
{final_insights}

## 📝 思维轨迹记录
{thinking_trace}

---

**报告生成说明**: 请基于以上框架生成详细、结构化的综合报告，确保每个部分都有具体内容，避免空泛的表述。重点突出基于证据的结论和具有实用价值的洞察。""",
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

### 🎯 结果反思 (Outcome Reflection)
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

请选择你希望进行的下一步操作：""",
            # Analysis templates for different step types
            "analyze_decomposition": """# 步骤质量分析：问题分解

请分析以下问题分解结果的质量：

**原始问题**: {original_topic}
**分解结果**: {step_result}
**分析类型**: {analysis_type}

## 分解质量评估标准：

### 1. 完整性 (Completeness) - 权重: 25%
- 是否覆盖了问题的主要方面？
- 子问题数量是否合适（3-7个）？
- 是否遗漏了重要角度？
- 评分：1-10分，理由：

### 2. 独立性 (Independence) - 权重: 20%
- 各子问题是否相对独立？
- 是否存在过度重叠？
- 能否独立分析每个子问题？
- 评分：1-10分，理由：

### 3. 可操作性 (Actionability) - 权重: 20%
- 子问题是否具体可分析？
- 搜索关键词是否合适？
- 是否提供了分析方向？
- 评分：1-10分，理由：

### 4. 逻辑结构 (Logical Structure) - 权重: 15%
- 分解逻辑是否清晰？
- 优先级设置是否合理？
- 依赖关系是否明确？
- 评分：1-10分，理由：

### 5. 格式规范 (Format Compliance) - 权重: 20%
- 是否符合JSON格式要求？
- 必需字段是否完整？
- 数据结构是否正确？
- 评分：1-10分，理由：

## 综合评估：
- **加权总分**: ___/10分 (计算公式: (完整性×0.25 + 独立性×0.2 + 可操作性×0.2 + 逻辑结构×0.15 + 格式规范×0.2))
- **质量等级**: {quality_level}
- **是否通过质量门控**: {quality_gate_passed}

## 改进建议：
{improvement_suggestions}

## 下一步建议：
{next_step_recommendation}

请开始详细分析：""",
            "analyze_evidence": """# 步骤质量分析：证据收集

请分析以下证据收集结果的质量：

**子问题**: {sub_question}
**证据收集结果**: {step_result}
**分析类型**: {analysis_type}

## 证据质量评估标准：

### 1. 来源多样性 (Source Diversity) - 权重: 25%
- 是否包含多种类型的来源？
- 学术、媒体、官方来源是否平衡？
- 是否避免了单一来源依赖？
- 评分：1-10分，理由：

### 2. 可信度评估 (Credibility Assessment) - 权重: 25%
- 来源的权威性如何？
- 是否提供了可信度评分？
- 是否识别了潜在偏见？
- 评分：1-10分，理由：

### 3. 相关性匹配 (Relevance Matching) - 权重: 20%
- 证据是否直接回答子问题？
- 关键词匹配度如何？
- 是否偏离了核心问题？
- 评分：1-10分，理由：

### 4. 信息完整性 (Information Completeness) - 权重: 15%
- 关键事实是否提取完整？
- 是否包含必要的引用信息？
- 摘要质量如何？
- 评分：1-10分，理由：

### 5. 冲突识别 (Conflict Identification) - 权重: 15%
- 是否识别了相互矛盾的信息？
- 对争议点的处理是否得当？
- 是否标记了不确定性？
- 评分：1-10分，理由：

## 综合评估：
- **加权总分**: ___/10分
- **质量等级**: {quality_level}
- **是否通过质量门控**: {quality_gate_passed}

## 改进建议：
{improvement_suggestions}

## 下一步建议：
{next_step_recommendation}

请开始详细分析：""",
            "analyze_debate": """# 步骤质量分析：多角度辩论

请分析以下多角度辩论结果的质量：

**辩论主题**: {debate_topic}
**辩论结果**: {step_result}
**分析类型**: {analysis_type}

## 辩论质量评估标准：

### 1. 角度多样性 (Perspective Diversity) - 权重: 25%
- 是否涵盖了不同立场？
- 角色设定是否清晰？
- 观点是否有实质性差异？
- 评分：1-10分，理由：

### 2. 论证质量 (Argument Quality) - 权重: 25%
- 论据是否有力？
- 逻辑推理是否严密？
- 是否基于证据？
- 评分：1-10分，理由：

### 3. 互动深度 (Interaction Depth) - 权重: 20%
- 是否有效质疑对方观点？
- 回应是否切中要害？
- 辩论是否深入？
- 评分：1-10分，理由：

### 4. 平衡性 (Balance) - 权重: 15%
- 各方观点是否得到充分表达？
- 辩论时间是否合理分配？
- 是否避免了一边倒？
- 评分：1-10分，理由：

### 5. 建设性 (Constructiveness) - 权重: 15%
- 是否产生了新的洞察？
- 争议点是否得到澄清？
- 是否推进了问题理解？
- 评分：1-10分，理由：

## 综合评估：
- **加权总分**: ___/10分
- **质量等级**: {quality_level}
- **是否通过质量门控**: {quality_gate_passed}

## 改进建议：
{improvement_suggestions}

## 下一步建议：
{next_step_recommendation}

请开始详细分析：""",
            "analyze_evaluation": """# 步骤质量分析：批判性评估

请分析以下批判性评估结果的质量：

**评估内容**: {evaluated_content}
**评估结果**: {step_result}
**分析类型**: {analysis_type}

## 评估质量分析标准：

### 1. 标准应用 (Standards Application) - 权重: 30%
- 是否正确应用了Paul-Elder九大标准？
- 每个标准的评分是否合理？
- 评估理由是否充分？
- 评分：1-10分，理由：

### 2. 评分准确性 (Scoring Accuracy) - 权重: 25%
- 评分是否与分析内容匹配？
- 是否避免了过于宽松或严格？
- 综合得分计算是否正确？
- 评分：1-10分，理由：

### 3. 改进建议 (Improvement Suggestions) - 权重: 20%
- 改进建议是否具体可行？
- 是否针对了主要问题？
- 建议的优先级是否合理？
- 评分：1-10分，理由：

### 4. 客观性 (Objectivity) - 权重: 15%
- 评估是否客观公正？
- 是否避免了主观偏见？
- 证据引用是否充分？
- 评分：1-10分，理由：

### 5. 决策支持 (Decision Support) - 权重: 10%
- 是否明确了下一步行动？
- 质量门控判断是否合理？
- 是否提供了清晰的指导？
- 评分：1-10分，理由：

## 综合评估：
- **加权总分**: ___/10分
- **质量等级**: {quality_level}
- **是否通过质量门控**: {quality_gate_passed}

## 改进建议：
{improvement_suggestions}

## 下一步建议：
{next_step_recommendation}

请开始详细分析：""",
            "analyze_reflection": """# 步骤质量分析：反思过程

请分析以下反思结果的质量：

**反思主题**: {reflection_topic}
**反思结果**: {step_result}
**分析类型**: {analysis_type}

## 反思质量评估标准：

### 1. 深度反思 (Reflection Depth) - 权重: 30%
- 是否深入思考了思维过程？
- 元认知意识是否充分？
- 自我评估是否诚实？
- 评分：1-10分，理由：

### 2. 洞察质量 (Insight Quality) - 权重: 25%
- 是否产生了有价值的洞察？
- 发现的问题是否重要？
- 学习收获是否具体？
- 评分：1-10分，理由：

### 3. 改进方向 (Improvement Direction) - 权重: 20%
- 改进建议是否可行？
- 是否识别了关键改进点？
- 行动计划是否具体？
- 评分：1-10分，理由：

### 4. 思维监控 (Metacognitive Monitoring) - 权重: 15%
- 是否识别了思维模式？
- 对思维盲点的认识如何？
- 自我监控能力如何？
- 评分：1-10分，理由：

### 5. 持续学习 (Continuous Learning) - 权重: 10%
- 是否体现了学习态度？
- 对未来思考的规划如何？
- 知识迁移能力如何？
- 评分：1-10分，理由：

## 综合评估：
- **加权总分**: ___/10分
- **质量等级**: {quality_level}
- **是否通过质量门控**: {quality_gate_passed}

## 改进建议：
{improvement_suggestions}

## 下一步建议：
{next_step_recommendation}

请开始详细分析：""",
            "quality_gate_failed": """# 质量门控未通过

当前步骤的质量评估未达到要求标准。

**步骤名称**: {step_name}
**质量得分**: {quality_score}/10
**要求标准**: {quality_threshold}/10
**主要问题**: {main_issues}

## 改进要求：

### 🔴 必须改进的问题：
{critical_issues}

### 🟡 建议改进的方面：
{improvement_suggestions}

### 📋 改进检查清单：
{improvement_checklist}

## 改进指导：
{improvement_guidance}

## 下一步行动：
1. 根据以上建议重新完成当前步骤
2. 确保解决所有标记的关键问题
3. 完成后再次调用analyze_step进行质量检查

请按照改进要求重新执行当前步骤：""",
            "format_validation_failed": """# 格式验证失败

步骤结果的格式不符合要求，需要重新格式化。

**步骤名称**: {step_name}
**期望格式**: {expected_format}
**检测到的问题**: {format_issues}

## 格式要求：
{format_requirements}

## 示例格式：
{format_example}

## 常见格式错误：
{common_format_errors}

请按照正确格式重新提交结果：""",
            # Additional templates for complex analysis
            "comprehensive_evidence_collection": """# 深度思考：全面证据收集

你现在需要为以下子问题进行全面、深入的证据收集：

**子问题**: {sub_question}
**搜索关键词**: {keywords}
**复杂度要求**: 高度全面性和深度分析

## 全面搜索策略：
1. **学术研究**: 搜索同行评议的学术论文和研究报告
2. **权威机构**: 政府部门、国际组织的官方数据和报告
3. **行业分析**: 专业咨询机构和行业协会的分析报告
4. **新闻媒体**: 主流媒体的深度报道和调查
5. **专家观点**: 领域专家的访谈、演讲和专业评论
6. **案例研究**: 相关的成功和失败案例分析

## 证据质量要求：
- 每个子问题至少收集7-10个不同来源的证据
- 确保来源的地理分布多样性（国内外）
- 包含不同时间段的数据（历史趋势分析）
- 涵盖不同利益相关者的观点

## 输出格式：
请整理为详细的证据档案，包含：
- 证据分类和标签
- 来源可信度详细评估
- 证据间的关联性分析
- 潜在偏见和局限性说明

开始全面证据收集：""",
            "advanced_decomposition": """# 深度思考：高级问题分解

你是一位资深的系统分析专家。请对以下复杂问题进行多层次、多维度的深度分解：

**主要问题**: {topic}
**复杂度**: {complexity}
**关注重点**: {focus}
**领域背景**: {domain_context}

## 高级分解策略：
1. **系统性分解**: 从系统论角度识别问题的各个子系统
2. **时间维度分解**: 短期、中期、长期影响和解决方案
3. **利益相关者分解**: 不同角色和群体的视角和需求
4. **因果链分解**: 根本原因、中间因素、直接后果
5. **层次结构分解**: 战略层、战术层、操作层的问题
6. **跨领域分解**: 技术、经济、社会、政治、环境等维度

## 输出要求：
请以JSON格式输出，包含：
- main_question: 主要问题
- sub_questions: 分层子问题列表（至少5-8个）
- question_hierarchy: 问题层次结构
- stakeholder_perspectives: 利益相关者视角
- causal_relationships: 因果关系映射
- complexity_analysis: 复杂度评估
- interdependencies: 相互依赖关系

开始高级分解：""",
            "advanced_critical_evaluation": """# 深度思考：高级批判性评估

请基于扩展的批判性思维标准对以下内容进行深度评估：

**评估内容**: {content}
**评估背景**: {context}

## 扩展评估标准：

### Paul-Elder九大标准 (权重: 60%)
1. 准确性 (Accuracy) - 10%
2. 精确性 (Precision) - 10%
3. 相关性 (Relevance) - 10%
4. 逻辑性 (Logic) - 10%
5. 广度 (Breadth) - 5%
6. 深度 (Depth) - 5%
7. 重要性 (Significance) - 5%
8. 公正性 (Fairness) - 5%
9. 清晰性 (Clarity) - 5%

### 高级评估维度 (权重: 40%)
10. 创新性 (Innovation) - 10%
    - 是否提出了新颖的观点或方法？
    - 创新程度如何？
    - 评分：1-10分，理由：

11. 可操作性 (Actionability) - 10%
    - 建议是否具体可执行？
    - 实施的可行性如何？
    - 评分：1-10分，理由：

12. 系统性 (Systematicity) - 10%
    - 是否采用了系统性思维？
    - 各部分的整合程度如何？
    - 评分：1-10分，理由：

13. 前瞻性 (Foresight) - 10%
    - 是否考虑了未来发展趋势？
    - 预测的合理性如何？
    - 评分：1-10分，理由：

## 综合评估：
- **加权总分**: ___/130分
- **质量等级**: 优秀(110+)/良好(90-109)/合格(70-89)/需改进(<70)
- **是否通过高级质量门控**: {quality_gate_passed}

## 详细改进建议：
{improvement_suggestions}

请开始高级评估："""
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