"""
Reflection Template for Deep Thinking Engine

This module provides templates for metacognitive reflection using Socratic questioning
and self-assessment techniques. The templates are designed to help users reflect on
their thinking process, identify biases, and improve their metacognitive skills.
"""

from typing import Dict, Any


def get_reflection_template(params: Dict[str, Any]) -> str:
    """
    Get the reflection template with the specified parameters.
    
    Args:
        params: Dictionary containing template parameters:
            - topic: The thinking topic being reflected upon
            - thinking_history: Summary of the thinking process so far
            - current_conclusions: Current conclusions or insights
            - complexity: The complexity level (high, medium, low)
    
    Returns:
        str: The formatted template
    """
    # Extract parameters with defaults
    topic = params.get("topic", "[topic]")
    thinking_history = params.get("thinking_history", "[thinking_history]")
    current_conclusions = params.get("current_conclusions", "[current_conclusions]")
    complexity = params.get("complexity", "medium")
    
    # Select the appropriate template based on complexity
    if complexity.lower() in ["high", "高"]:
        return get_high_complexity_template(topic, thinking_history, current_conclusions)
    elif complexity.lower() in ["low", "低"]:
        return get_low_complexity_template(topic, thinking_history, current_conclusions)
    else:  # Default to medium
        return get_medium_complexity_template(topic, thinking_history, current_conclusions)


def get_high_complexity_template(topic: str, thinking_history: str, current_conclusions: str) -> str:
    """
    Get the high complexity reflection template.
    
    Args:
        topic: The thinking topic being reflected upon
        thinking_history: Summary of the thinking process so far
        current_conclusions: Current conclusions or insights
    
    Returns:
        str: The formatted template
    """
    template = f"""# 深度思考：高级苏格拉底式反思

现在让我们对整个思考过程进行系统性的元认知反思：

**思考主题**: {topic}
**思考历程**: {thinking_history}
**当前结论**: {current_conclusions}
**反思复杂度**: 高

## 苏格拉底式反思框架

### 1. 认识论反思 (Epistemological Reflection) - 权重: 20%

#### 知识来源与质量
- **我的知识来源是什么？**
  - 我依赖了哪些信息源？
  - 这些信息源的可靠性如何？
  - 我是否过度依赖某些类型的信息？
  - 我是否忽略了重要的信息来源？
- **我如何验证信息的准确性？**
  - 我使用了哪些验证方法？
  - 我是否寻找了反驳证据？
  - 我如何处理相互矛盾的信息？
  - 我的验证过程有何局限性？
- **我的知识有哪些盲点？**
  - 哪些领域我缺乏足够了解？
  - 这些盲点如何影响我的思考？
  - 我如何弥补这些知识缺口？
  - 我是否意识到"未知的未知"？
- **反思与评估**:
  - 知识基础评分 (1-10): 
  - 主要优势:
  - 主要不足:
  - 改进方向:

#### 假设检验
- **我做了哪些关键假设？**
  - 这些假设的基础是什么？
  - 哪些是明确的假设，哪些是隐含的？
  - 这些假设如何影响我的思考路径？
  - 我是否过度依赖某些假设？
- **我如何测试这些假设？**
  - 我使用了什么方法来验证假设？
  - 我是否考虑了反例？
  - 我的测试方法有何局限性？
  - 哪些假设未经充分检验？
- **如果关键假设错误，会怎样？**
  - 哪些结论将不再成立？
  - 替代假设会导致什么不同结论？
  - 我的思考框架有多大弹性？
  - 如何降低错误假设的风险？
- **反思与评估**:
  - 假设检验评分 (1-10): 
  - 最可靠的假设:
  - 最值得质疑的假设:
  - 改进方向:

### 2. 逻辑推理反思 (Logical Reasoning Reflection) - 权重: 20%

#### 推理结构分析
- **我的推理路径是什么？**
  - 我使用了哪些推理方法（演绎、归纳、溯因等）？
  - 我的推理链条是否完整？
  - 各步骤之间的逻辑连接是否紧密？
  - 我的推理过程是否透明？
- **我的推理中存在哪些逻辑谬误？**
  - 我是否犯了形式逻辑错误？
  - 我是否有非形式逻辑谬误（如诉诸权威、稻草人等）？
  - 我的论证中有哪些弱点？
  - 我如何加强这些弱点？
- **我的推理有何局限性？**
  - 我的推理框架有何边界条件？
  - 在什么情况下我的推理不再适用？
  - 我的推理模型忽略了哪些复杂性？
  - 如何扩展我的推理边界？
- **反思与评估**:
  - 逻辑推理评分 (1-10): 
  - 推理强项:
  - 推理弱点:
  - 改进方向:

#### 替代解释探索
- **还有哪些替代解释？**
  - 有哪些不同的解释框架？
  - 这些替代解释的优势是什么？
  - 为什么我没有选择这些解释？
  - 哪些证据支持这些替代解释？
- **我如何评估不同解释？**
  - 我使用了什么标准来比较解释？
  - 我是否公正地评估了各种可能性？
  - 我的评估过程有何偏好或偏见？
  - 如何更客观地评估替代解释？
- **整合多种解释的可能性**
  - 不同解释之间有何互补性？
  - 是否可能创建更综合的解释框架？
  - 多元解释如何共存？
  - 如何处理解释间的张力？
- **反思与评估**:
  - 替代解释评分 (1-10): 
  - 最有力的替代解释:
  - 我的解释相对优势:
  - 改进方向:

### 3. 认知偏见反思 (Cognitive Bias Reflection) - 权重: 20%

#### 偏见识别
- **我的思考中存在哪些认知偏见？**
  - 我是否有确认偏误（只寻找支持性证据）？
  - 我是否受到锚定效应影响？
  - 我是否有可得性偏误（过度依赖容易想到的例子）？
  - 我是否有后见之明偏误？
  - 我是否有群体思维或从众倾向？
  - 我是否有基本归因错误？
  - 我是否有乐观偏见或悲观偏见？
  - 我是否有自利偏见？
- **这些偏见如何影响我的思考？**
  - 它们如何塑造我的问题定义？
  - 它们如何影响我的信息收集？
  - 它们如何影响我的分析过程？
  - 它们如何影响我的结论形成？
- **我如何减轻这些偏见？**
  - 我采取了哪些策略来减轻偏见？
  - 这些策略的效果如何？
  - 还有哪些偏见缓解策略可以尝试？
  - 如何系统性地减少偏见影响？
- **反思与评估**:
  - 偏见意识评分 (1-10): 
  - 最显著的偏见:
  - 最有效的缓解策略:
  - 改进方向:

#### 情绪影响
- **情绪如何影响我的思考？**
  - 哪些情绪在思考过程中出现？
  - 这些情绪如何影响我的判断？
  - 我是否意识到情绪的影响？
  - 我如何管理情绪对思考的影响？
- **价值观如何塑造我的思考？**
  - 哪些核心价值观影响了我的分析？
  - 我是否意识到这些价值观的作用？
  - 不同价值观会导致什么不同结论？
  - 我如何平衡价值观与客观分析？
- **我的身份认同如何影响思考？**
  - 我的背景和经历如何塑造我的视角？
  - 我的群体归属如何影响我的立场？
  - 我是否能超越身份认同的限制？
  - 如何利用多元身份拓展思考？
- **反思与评估**:
  - 情绪觉察评分 (1-10): 
  - 最具影响力的情绪/价值观:
  - 情绪管理效果:
  - 改进方向:

### 4. 思维广度反思 (Breadth of Thinking Reflection) - 权重: 15%

#### 多角度思考
- **我考虑了哪些不同角度？**
  - 我探索了多少不同视角？
  - 这些视角的多样性如何？
  - 我是否包含了关键利益相关者的视角？
  - 我是否考虑了非主流观点？
- **我忽略了哪些重要视角？**
  - 哪些群体或立场的视角被忽略？
  - 这些缺失视角会带来什么洞见？
  - 为什么这些视角被忽略？
  - 如何更好地整合多元视角？
- **我如何整合不同视角？**
  - 我如何处理视角间的冲突？
  - 我是否公平权衡了不同视角？
  - 我的整合过程有何局限性？
  - 如何创造更综合的理解？
- **反思与评估**:
  - 多角度思考评分 (1-10): 
  - 最有价值的视角:
  - 最缺失的视角:
  - 改进方向:

#### 跨学科整合
- **我整合了哪些学科知识？**
  - 我应用了哪些不同领域的概念？
  - 这些学科如何互补？
  - 学科整合的深度如何？
  - 跨学科思考带来了什么独特洞见？
- **我忽略了哪些相关学科？**
  - 哪些学科可能提供有价值的视角？
  - 这些学科会带来什么新见解？
  - 为什么这些学科被忽略？
  - 如何更好地整合多学科知识？
- **我如何处理学科间的张力？**
  - 不同学科框架如何协调？
  - 我如何处理概念冲突？
  - 我如何创造学科间对话？
  - 如何发展更整合的理论框架？
- **反思与评估**:
  - 跨学科整合评分 (1-10): 
  - 最有效的学科组合:
  - 最需要整合的学科:
  - 改进方向:

### 5. 思维深度反思 (Depth of Thinking Reflection) - 权重: 15%

#### 问题层次分析
- **我探索了多少层次的问题？**
  - 我是否超越了表面现象？
  - 我是否分析了根本原因？
  - 我是否考虑了系统层面？
  - 我的分析深度如何？
- **我的思考在哪些方面过于肤浅？**
  - 哪些方面需要更深入分析？
  - 为什么这些方面分析不足？
  - 深入分析会带来什么新见解？
  - 如何推动更深层次思考？
- **我如何处理复杂性？**
  - 我如何应对问题的复杂性？
  - 我的简化是否合理？
  - 我是否保留了必要的复杂性？
  - 如何更好地平衡简化与复杂性？
- **反思与评估**:
  - 思维深度评分 (1-10): 
  - 分析最深入的方面:
  - 需要深化的方面:
  - 改进方向:

#### 创新与突破
- **我的思考有何创新之处？**
  - 我提出了哪些新颖见解？
  - 我挑战了哪些常规思维？
  - 我创造了哪些新连接？
  - 我的思考如何超越现有框架？
- **我的思考受到哪些限制？**
  - 哪些思维习惯限制了我？
  - 哪些假设阻碍了创新？
  - 我如何突破这些限制？
  - 如何培养更具突破性的思维？
- **如何推动思考的下一步突破？**
  - 哪些方向最有突破潜力？
  - 需要什么新方法或视角？
  - 如何重构问题以激发创新？
  - 如何系统性地推动思维突破？
- **反思与评估**:
  - 创新思维评分 (1-10): 
  - 最具创新性的见解:
  - 创新的主要障碍:
  - 改进方向:

### 6. 实践应用反思 (Practical Application Reflection) - 权重: 10%

#### 实用价值评估
- **我的思考有何实际价值？**
  - 这些见解如何应用于实践？
  - 谁会从这些见解中受益？
  - 实施这些见解的障碍是什么？
  - 如何提高思考的实用性？
- **我如何测试这些见解？**
  - 什么样的实验可以验证这些见解？
  - 如何收集实施反馈？
  - 如何迭代改进这些见解？
  - 验证的标准是什么？
- **这些见解的限制是什么？**
  - 在什么情况下这些见解不适用？
  - 实施过程中的风险是什么？
  - 如何适应不同情境？
  - 如何扩展应用范围？
- **反思与评估**:
  - 实用价值评分 (1-10): 
  - 最具应用价值的见解:
  - 应用的主要挑战:
  - 改进方向:

#### 行动计划
- **基于反思，我应该采取什么行动？**
  - 需要哪些具体行动？
  - 这些行动的优先级是什么？
  - 如何衡量行动的有效性？
  - 如何整合反思到持续行动中？
- **如何改进我的思考过程？**
  - 下次思考类似问题时应该如何改进？
  - 需要培养哪些思维技能？
  - 如何建立更有效的思考习惯？
  - 如何系统性地提升思考质量？
- **如何分享和传播这些见解？**
  - 这些见解应该与谁分享？
  - 如何有效沟通这些见解？
  - 如何促进集体智慧的形成？
  - 如何推动更广泛的对话？
- **反思与评估**:
  - 行动导向评分 (1-10): 
  - 最优先行动:
  - 最重要的思维改进:
  - 具体实施计划:

## 元认知综合评估

### 思维过程整体评估
- **思维过程的主要优势**:
  1. 
  2. 
  3. 

- **思维过程的主要不足**:
  1. 
  2. 
  3. 

- **关键学习与洞见**:
  1. 
  2. 
  3. 

- **思维模式识别**:
  - 我倾向于使用哪些思维模式？
  - 这些模式的优势和局限是什么？
  - 如何拓展我的思维模式库？

### 元认知能力评估
- **元认知觉察能力** (1-10分):
  - 我对自己思维过程的觉察程度
  - 评分理由:

- **元认知调控能力** (1-10分):
  - 我调整思维过程的有效性
  - 评分理由:

- **元认知知识** (1-10分):
  - 我对思维策略的了解和应用
  - 评分理由:

### 持续改进计划
- **短期改进** (1-3个月):
  1. 
  2. 
  3. 

- **中期发展** (3-12个月):
  1. 
  2. 
  3. 

- **长期愿景** (1年以上):
  1. 
  2. 
  3. 

## JSON输出格式
```json
{{
  "reflection_topic": "反思主题",
  "thinking_process_summary": "思考过程摘要",
  "epistemological_reflection": {{
    "knowledge_sources": ["来源1", "来源2", "来源3"],
    "knowledge_quality_score": 7,
    "key_assumptions": ["假设1", "假设2", "假设3"],
    "assumption_testing_score": 6,
    "knowledge_strengths": ["优势1", "优势2"],
    "knowledge_gaps": ["缺口1", "缺口2"],
    "improvement_areas": ["改进1", "改进2"]
  }},
  "logical_reasoning_reflection": {{
    "reasoning_methods": ["方法1", "方法2"],
    "reasoning_score": 8,
    "logical_fallacies": ["谬误1", "谬误2"],
    "alternative_explanations": ["解释1", "解释2"],
    "reasoning_strengths": ["优势1", "优势2"],
    "reasoning_weaknesses": ["弱点1", "弱点2"],
    "improvement_areas": ["改进1", "改进2"]
  }},
  "cognitive_bias_reflection": {{
    "identified_biases": ["偏见1", "偏见2", "偏见3"],
    "bias_awareness_score": 7,
    "emotional_influences": ["情绪1", "情绪2"],
    "value_influences": ["价值观1", "价值观2"],
    "bias_mitigation_strategies": ["策略1", "策略2"],
    "improvement_areas": ["改进1", "改进2"]
  }},
  "thinking_breadth_reflection": {{
    "perspectives_considered": ["视角1", "视角2", "视角3"],
    "perspectives_score": 8,
    "missing_perspectives": ["缺失视角1", "缺失视角2"],
    "disciplines_integrated": ["学科1", "学科2"],
    "interdisciplinary_score": 7,
    "improvement_areas": ["改进1", "改进2"]
  }},
  "thinking_depth_reflection": {{
    "depth_score": 8,
    "deepest_insights": ["洞见1", "洞见2"],
    "innovative_ideas": ["创新1", "创新2"],
    "innovation_score": 7,
    "complexity_handling": "复杂性处理描述",
    "improvement_areas": ["改进1", "改进2"]
  }},
  "practical_application_reflection": {{
    "practical_value_score": 8,
    "key_applications": ["应用1", "应用2"],
    "implementation_challenges": ["挑战1", "挑战2"],
    "action_items": ["行动1", "行动2", "行动3"],
    "action_orientation_score": 7
  }},
  "metacognitive_assessment": {{
    "overall_strengths": ["优势1", "优势2", "优势3"],
    "overall_weaknesses": ["弱点1", "弱点2", "弱点3"],
    "key_learnings": ["学习1", "学习2", "学习3"],
    "metacognitive_awareness_score": 8,
    "metacognitive_regulation_score": 7,
    "improvement_plan": ["计划1", "计划2", "计划3"]
  }}
}}
```

请开始深度反思："""
    return template


def get_medium_complexity_template(topic: str, thinking_history: str, current_conclusions: str) -> str:
    """
    Get the medium complexity reflection template.
    
    Args:
        topic: The thinking topic being reflected upon
        thinking_history: Summary of the thinking process so far
        current_conclusions: Current conclusions or insights
    
    Returns:
        str: The formatted template
    """
    template = f"""# 深度思考：苏格拉底式反思

现在让我们对整个思考过程进行深度反思：

**思考主题**: {topic}
**思考历程**: {thinking_history}
**当前结论**: {current_conclusions}
**反思复杂度**: 中等

## 苏格拉底式提问框架

### 🤔 过程反思 (Process Reflection)

#### 1. 思维路径审视
- **我是如何得出这些结论的？**
  - 我使用了哪些思维方法和推理过程？
  - 我的推理过程是否合理和连贯？
  - 我是否跳过了重要的思考步骤？
  - 反思：

#### 2. 视角全面性
- **我考虑了哪些角度？**
  - 我是否考虑了多元视角？
  - 是否遗漏了重要的利益相关者视角？
  - 我如何整合不同的视角？
  - 反思：

#### 3. 证据质量
- **我的证据是否充分？**
  - 我使用了哪些类型的证据？
  - 证据的质量和可靠性如何？
  - 是否存在相互矛盾的证据？
  - 我如何权衡不同证据？
  - 反思：

#### 4. 假设检验
- **我做了哪些关键假设？**
  - 这些假设的基础是什么？
  - 我如何验证这些假设？
  - 哪些假设可能需要重新考虑？
  - 反思：

### 🎯 结果反思 (Outcome Reflection)

#### 5. 结论确定性
- **我的结论有多确定？**
  - 哪些部分我很确信？
  - 哪些部分还存在不确定性？
  - 我如何评估结论的可靠性？
  - 反思：

#### 6. 风险评估
- **如果我错了会怎样？**
  - 错误结论可能带来什么后果？
  - 最坏的情况是什么？
  - 如何降低错误的风险？
  - 反思：

#### 7. 替代解释
- **还有其他可能的解释吗？**
  - 有哪些替代性解释或结论？
  - 为什么我没有选择这些解释？
  - 什么证据可能支持这些替代解释？
  - 反思：

#### 8. 实际应用
- **这些结论如何应用于实践？**
  - 这些见解如何转化为行动？
  - 实施过程中可能遇到的挑战是什么？
  - 如何测试这些结论的有效性？
  - 反思：

### 🧠 元认知反思 (Metacognitive Reflection)

#### 9. 思维模式
- **我的思维模式如何？**
  - 我倾向于使用哪些思维方式？
  - 我有哪些思维习惯和偏好？
  - 我的思维有哪些盲点？
  - 反思：

#### 10. 认知偏见
- **我的思考受到哪些偏见影响？**
  - 我是否有确认偏误、锚定效应等认知偏见？
  - 这些偏见如何影响我的结论？
  - 我如何减轻这些偏见的影响？
  - 反思：

#### 11. 学习收获
- **我学到了什么？**
  - 这次思考让我获得了什么新见解？
  - 我的思维能力有何提升？
  - 这些学习如何影响我未来的思考？
  - 反思：

#### 12. 改进方向
- **下次如何改进？**
  - 我可以在哪些方面做得更好？
  - 需要培养哪些新的思维技能？
  - 如何系统性地提升思考质量？
  - 反思：

## 反思综合评估

### 思维过程评估
- **思维过程优势** (1-10分):
  - 评分:
  - 主要优势:

- **思维过程不足** (1-10分):
  - 评分:
  - 主要不足:

- **思维全面性** (1-10分):
  - 评分:
  - 评估理由:

- **思维深度** (1-10分):
  - 评分:
  - 评估理由:

### 元认知能力评估
- **自我觉察能力** (1-10分):
  - 评分:
  - 评估理由:

- **思维调控能力** (1-10分):
  - 评分:
  - 评估理由:

### 持续改进计划
- **短期改进目标**:
  1. 
  2. 
  3. 

- **长期发展方向**:
  1. 
  2. 
  3. 

## 最终总结
- **核心洞察**:

- **主要收获**:

- **行动计划**:

- **持续思考的问题**:

## JSON输出格式
```json
{{
  "reflection_topic": "反思主题",
  "thinking_process_summary": "思考过程摘要",
  "process_reflection": {{
    "reasoning_path": "推理路径描述",
    "perspectives_considered": ["视角1", "视角2", "视角3"],
    "evidence_quality": {{
      "strengths": ["优势1", "优势2"],
      "limitations": ["局限1", "局限2"]
    }},
    "key_assumptions": ["假设1", "假设2", "假设3"]
  }},
  "outcome_reflection": {{
    "conclusion_certainty": 7,
    "risk_assessment": "风险评估描述",
    "alternative_explanations": ["解释1", "解释2"],
    "practical_applications": ["应用1", "应用2"]
  }},
  "metacognitive_reflection": {{
    "thinking_patterns": ["模式1", "模式2"],
    "cognitive_biases": ["偏见1", "偏见2"],
    "key_learnings": ["学习1", "学习2", "学习3"],
    "improvement_areas": ["改进1", "改进2", "改进3"]
  }},
  "overall_assessment": {{
    "process_strengths_score": 8,
    "process_weaknesses_score": 6,
    "thinking_breadth_score": 7,
    "thinking_depth_score": 8,
    "self_awareness_score": 7,
    "thought_regulation_score": 6
  }},
  "improvement_plan": {{
    "short_term_goals": ["目标1", "目标2", "目标3"],
    "long_term_directions": ["方向1", "方向2", "方向3"]
  }},
  "final_summary": {{
    "core_insights": "核心洞察描述",
    "main_takeaways": "主要收获描述",
    "action_plan": "行动计划描述",
    "ongoing_questions": "持续思考的问题描述"
  }}
}}
```

请开始深度反思："""
    return template


def get_low_complexity_template(topic: str, thinking_history: str, current_conclusions: str) -> str:
    """
    Get the low complexity reflection template.
    
    Args:
        topic: The thinking topic being reflected upon
        thinking_history: Summary of the thinking process so far
        current_conclusions: Current conclusions or insights
    
    Returns:
        str: The formatted template
    """
    template = f"""# 深度思考：基础反思引导

让我们对思考过程进行简单反思：

**思考主题**: {topic}
**思考历程**: {thinking_history}
**当前结论**: {current_conclusions}
**反思复杂度**: 低

## 苏格拉底式基础提问

### 思考过程反思

#### 1. 思维路径
- 我是如何得出这些结论的？
- 我的推理过程是否合理？
- 反思：

#### 2. 证据评估
- 我使用了哪些证据？
- 这些证据的质量如何？
- 反思：

#### 3. 多角度思考
- 我考虑了哪些不同角度？
- 是否遗漏了重要视角？
- 反思：

### 结论质量反思

#### 4. 结论可靠性
- 我对结论的确信程度如何？
- 哪些部分还不确定？
- 反思：

#### 5. 替代可能性
- 还有其他可能的解释吗？
- 为什么我选择了当前结论？
- 反思：

#### 6. 应用价值
- 这些结论有什么实际用途？
- 如何将其应用到实践中？
- 反思：

### 自我认知反思

#### 7. 思维习惯
- 我注意到自己有哪些思维习惯？
- 这些习惯如何影响我的结论？
- 反思：

#### 8. 学习收获
- 通过这次思考，我学到了什么？
- 这对我未来的思考有何启示？
- 反思：

#### 9. 改进方向
- 下次思考类似问题时，我可以如何改进？
- 我需要培养哪些思维能力？
- 反思：

## 总体评估

### 思维质量评分
- 思维全面性 (1-10分)：
- 思维深度 (1-10分)：
- 证据使用 (1-10分)：
- 逻辑推理 (1-10分)：
- 总体评分：

### 最终总结
- **主要收获**：

- **改进方向**：

- **行动计划**：

## JSON输出格式
```json
{{
  "reflection_topic": "反思主题",
  "thinking_summary": "思考过程摘要",
  "process_reflection": {{
    "reasoning_path": "推理路径描述",
    "evidence_quality": "证据质量评估",
    "perspectives": ["视角1", "视角2"]
  }},
  "conclusion_reflection": {{
    "reliability": 7,
    "alternatives": ["替代解释1", "替代解释2"],
    "practical_value": "实际应用价值描述"
  }},
  "self_reflection": {{
    "thinking_habits": ["习惯1", "习惯2"],
    "key_learnings": ["学习1", "学习2"],
    "improvement_areas": ["改进1", "改进2"]
  }},
  "overall_assessment": {{
    "breadth_score": 7,
    "depth_score": 6,
    "evidence_score": 8,
    "logic_score": 7,
    "overall_score": 7
  }},
  "final_summary": {{
    "main_takeaways": "主要收获描述",
    "improvement_directions": "改进方向描述",
    "action_plan": "行动计划描述"
  }}
}}
```

请开始反思："""
    return template