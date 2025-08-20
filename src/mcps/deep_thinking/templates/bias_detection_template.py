"""
Bias Detection Template for Deep Thinking Engine

This module provides templates for detecting cognitive biases in thinking processes.
"""

from typing import Dict, Any


def get_bias_detection_template(params: Dict[str, Any]) -> str:
    """
    Get the bias detection template with the specified parameters.

    Args:
        params: Dictionary containing template parameters:
            - content: The content to be analyzed for biases
            - context: The context of the analysis
            - complexity: The complexity level (high, medium, low)

    Returns:
        str: The formatted template
    """
    # Extract parameters with defaults
    content = params.get("content", "[content]")
    context = params.get("context", "[context]")
    complexity = params.get("complexity", "medium")

    # Select the appropriate template based on complexity
    if complexity.lower() in ["high", "高"]:
        return get_high_complexity_template(content, context)
    elif complexity.lower() in ["low", "低"]:
        return get_low_complexity_template(content, context)
    else:  # Default to medium
        return get_medium_complexity_template(content, context)


def get_high_complexity_template(content: str, context: str) -> str:
    """
    Get the high complexity bias detection template.

    Args:
        content: The content to be analyzed
        context: The context of the analysis

    Returns:
        str: The formatted template
    """
    template = f"""# 深度思考：高级认知偏见检测

请对以下内容进行全面、系统的认知偏见分析：

**分析内容**: {content}
**分析背景**: {context}
**分析复杂度**: 高

## 认知偏见全面检测框架

### 1. 信息处理偏见 (Information Processing Biases)

#### 🔍 确认偏误 (Confirmation Bias) - 权重: 15%
- **定义**: 倾向于寻找、解释、偏爱和回忆与已有信念一致的信息，同时给予不一致信息较少的考虑
- **检测问题**:
  - 是否主要寻找支持既有观点的信息？
  - 是否对反驳证据进行了合理的权衡？
  - 是否存在选择性引用或忽略特定来源？
  - 是否考虑了反面假设？
- **检测标准**:
  - 严重: 完全忽视反对证据，只关注支持性信息
  - 中度: 虽然提及反对证据，但明显偏向支持性信息
  - 轻微: 存在轻微的选择性关注，但基本平衡
  - 不存在: 平等对待各种证据，积极寻求反驳自己的信息
- **检测结果**: 严重/中度/轻微/不存在
- **证据**:
- **缓解策略**:

#### ⚓ 锚定效应 (Anchoring Bias) - 权重: 10%
- **定义**: 在决策过程中过度依赖最初获得的信息（"锚点"）
- **检测问题**:
  - 是否过度受到初始数据或观点的影响？
  - 后续判断是否明显围绕初始参考点调整？
  - 是否考虑了远离初始锚点的可能性？
  - 是否尝试使用多个不同的参考点？
- **检测结果**: 严重/中度/轻微/不存在
- **证据**:
- **缓解策略**:

#### 📊 可得性启发 (Availability Heuristic) - 权重: 10%
- **定义**: 基于容易想到的例子来判断事件的概率或频率
- **检测问题**:
  - 是否因为某些例子更生动、更容易想起而认为它们更具代表性？
  - 判断是否受到媒体报道频率或个人经历的不当影响？
  - 是否使用了系统性数据而非轶事证据？
  - 是否考虑了不易获取但可能更相关的信息？
- **检测结果**: 严重/中度/轻微/不存在
- **证据**:
- **缓解策略**:

#### 🎯 代表性启发 (Representativeness Heuristic) - 权重: 10%
- **定义**: 基于事物与原型或刻板印象的相似程度来判断其属于某类的概率
- **检测问题**:
  - 是否基于刻板印象而非实际数据进行判断？
  - 是否忽略了基础概率（先验概率）？
  - 是否过度关注表面特征而忽略统计规律？
  - 是否犯了赌徒谬误（误判随机事件的概率）？
- **检测结果**: 严重/中度/轻微/不存在
- **证据**:
- **缓解策略**:

### 2. 自我认知偏见 (Self-Perception Biases)

#### 💪 过度自信 (Overconfidence Bias) - 权重: 12%
- **定义**: 对自己的知识、能力或判断准确性的过度自信
- **检测问题**:
  - 是否对结论表现出过高的确定性？
  - 是否低估了不确定性和风险？
  - 是否考虑了自己可能错误的概率？
  - 是否提供了足够的证据支持高确信度？
- **检测结果**: 严重/中度/轻微/不存在
- **证据**:
- **缓解策略**:

#### 🔄 后见之明偏误 (Hindsight Bias) - 权重: 8%
- **定义**: 事后认为事件结果是可预见的，尽管事前并无足够信息预测
- **检测问题**:
  - 是否声称"早就知道"某结果会发生？
  - 是否低估了事前的不确定性？
  - 是否重新解释过去的预测以符合已知结果？
  - 是否忽略了当时的决策环境和信息限制？
- **检测结果**: 严重/中度/轻微/不存在
- **证据**:
- **缓解策略**:

#### 🌟 光环效应 (Halo Effect) - 权重: 8%
- **定义**: 因为对某人或事物的一个特性的正面印象而对其他特性也产生积极评价
- **检测问题**:
  - 是否因为一个正面特质而对整体做出过于积极的评价？
  - 是否忽略了与初始印象不一致的证据？
  - 是否能够分别评估不同特质而不受整体印象影响？
- **检测结果**: 严重/中度/轻微/不存在
- **证据**:
- **缓解策略**:

#### 🧠 认知失调 (Cognitive Dissonance) - 权重: 7%
- **定义**: 当持有的信念、态度或行为之间存在矛盾时产生的心理不适，导致寻求减少这种不适的行为
- **检测问题**:
  - 是否存在相互矛盾的观点或行为？
  - 是否通过改变信念或寻找合理化解释来减少矛盾？
  - 是否忽视或淡化与现有信念不一致的信息？
  - 是否能够承认并处理认知上的矛盾？
- **检测结果**: 严重/中度/轻微/不存在
- **证据**:
- **缓解策略**:

### 3. 群体思维偏见 (Group Thinking Biases)

#### 👥 从众效应 (Bandwagon Effect) - 权重: 8%
- **定义**: 因为许多人持有某种信念而倾向于采纳相同信念
- **检测问题**:
  - 是否过度依赖多数人的观点？
  - 是否因为某观点流行或权威而接受？
  - 是否独立思考而非盲从？
  - 是否考虑了少数派但可能正确的观点？
- **检测结果**: 严重/中度/轻微/不存在
- **证据**:
- **缓解策略**:

#### 🧩 内群体偏见 (In-group Bias) - 权重: 7%
- **定义**: 倾向于偏爱自己所属群体的成员，对外群体成员持有偏见
- **检测问题**:
  - 是否对自己群体的观点或行为更为宽容？
  - 是否对外部群体持有刻板印象或偏见？
  - 是否能够客观评估不同群体的观点？
  - 是否考虑了多元视角和跨群体合作的可能性？
- **检测结果**: 严重/中度/轻微/不存在
- **证据**:
- **缓解策略**:

### 4. 决策偏见 (Decision-Making Biases)

#### 💸 沉没成本谬误 (Sunk Cost Fallacy) - 权重: 10%
- **定义**: 因为已经投入资源而继续投资失败项目，而非基于未来收益做决策
- **检测问题**:
  - 是否因为已投入而不愿放弃？
  - 是否忽视了未来收益和成本？
  - 是否能够客观评估当前形势？
- **检测结果**: 严重/中度/轻微/不存在
- **证据**:
- **缓解策略**:

#### 🖼️ 框架效应 (Framing Effect) - 权重: 10%
- **定义**: 因问题呈现方式不同而做出不同决策，即使实质相同
- **检测问题**:
  - 是否受到问题表述方式的过度影响？
  - 是否能从多角度审视同一问题？
  - 是否能识别出不同表述下的相同本质？
- **检测结果**: 严重/中度/轻微/不存在
- **证据**:
- **缓解策略**:

## 综合偏见评估

### 偏见风险评分
- 信息处理偏见: _/10 × 45% = _
- 自我认知偏见: _/10 × 20% = _
- 群体思维偏见: _/10 × 15% = _
- 决策偏见: _/10 × 20% = _

**加权总分**: _/10分

### 偏见风险等级
- 8.0-10.0: 高风险 - 严重偏见，显著影响判断
- 5.0-7.9: 中风险 - 明显偏见，部分影响判断
- 2.0-4.9: 低风险 - 轻微偏见，影响有限
- 0.0-1.9: 微风险 - 几乎无偏见，判断相对客观

**偏见风险等级**: _

## 偏见检测元分析
请对本次偏见分析本身进行元分析，评估分析过程中可能存在的偏见：

### 本次偏见分析本身可能存在的偏见
1. 分析者偏见：您自身可能带有哪些偏见？
2. 方法论偏见：所使用的分析框架是否有局限性？
3. 确认偏误：是否过于关注符合预期的偏见证据？
4. 可得性偏见：是否过于关注容易识别的偏见类型？
5. 专业领域盲点：是否因专业知识局限而忽视某些领域特有的偏见？

### 元分析改进建议
1. 
2. 
3. 

### 主要偏见类型
1. 
2. 
3. 

### 偏见缓解策略
1. 
2. 
3. 
4. 
5. 

### 改进优先级
1. 首要改进: 
2. 次要改进: 
3. 长期关注: 

## JSON输出格式
```json
{{
  "analysis_subject": "分析内容的简要描述",
  "analysis_context": "分析背景的简要描述",
  "bias_detection": {{
    "confirmation_bias": {{
      "detected": true,
      "evidence": "证据描述",
      "mitigation": "缓解策略"
    }},
    "anchoring_bias": {{
      "detected": false,
      "evidence": "证据描述",
      "mitigation": "缓解策略"
    }}
  }},
  "overall_assessment": {{
    "risk_level": "偏见风险等级",
    "main_biases": ["主要偏见1", "主要偏见2"],
    "mitigation_strategies": ["缓解策略1", "缓解策略2"]
  }}
}}
```

请开始详细的认知偏见分析："""
    return template


def get_medium_complexity_template(content: str, context: str) -> str:
    """
    Get the medium complexity bias detection template.

    Args:
        content: The content to be analyzed
        context: The context of the analysis

    Returns:
        str: The formatted template
    """
    template = f"""# 深度思考：认知偏见检测

请仔细分析以下内容中可能存在的认知偏见：

**分析内容**: {content}
**分析背景**: {context}
**分析复杂度**: 中等

## 常见认知偏见检查清单

### 1. 信息处理偏见

#### 🔍 确认偏误 (Confirmation Bias) - 权重: 15%
- **定义**: 倾向于寻找、解释、偏爱和回忆与已有信念一致的信息
- **检测问题**:
  - 是否只寻找支持既有观点的信息？
  - 是否忽略了相反的证据？
  - 是否平等对待支持和反对的证据？
- **检测结果**: 严重/中度/轻微/不存在
- **证据**:
- **缓解策略**:

#### ⚓ 锚定效应 (Anchoring Bias) - 权重: 10%
- **定义**: 过度依赖最初获得的信息（"锚点"）
- **检测问题**:
  - 是否过度依赖最初获得的信息？
  - 后续判断是否受到初始印象影响？
  - 是否考虑了多个不同的参考点？
- **检测结果**: 严重/中度/轻微/不存在
- **证据**:
- **缓解策略**:

#### 📊 可得性启发 (Availability Heuristic) - 权重: 10%
- **定义**: 基于容易想到的例子来判断事件的概率
- **检测问题**:
  - 是否因为某些例子容易想起就认为更常见？
  - 判断是否受到媒体报道频率影响？
  - 是否使用了系统性数据而非轶事证据？
- **检测结果**: 严重/中度/轻微/不存在
- **证据**:
- **缓解策略**:

#### 🎯 代表性启发 (Representativeness Heuristic) - 权重: 10%
- **定义**: 基于事物与原型的相似程度来判断其属于某类的概率
- **检测问题**:
  - 是否基于刻板印象进行判断？
  - 是否忽略了基础概率？
  - 是否过度关注表面特征？
- **检测结果**: 严重/中度/轻微/不存在
- **证据**:
- **缓解策略**:

### 2. 自我认知偏见

#### 💪 过度自信 (Overconfidence Bias) - 权重: 15%
- **定义**: 对自己的知识、能力或判断准确性的过度自信
- **检测问题**:
  - 对自己的判断是否过于确信？
  - 是否低估了不确定性？
  - 是否考虑了自己可能错误的概率？
- **检测结果**: 严重/中度/轻微/不存在
- **证据**:
- **缓解策略**:

#### 🔄 后见之明偏误 (Hindsight Bias) - 权重: 10%
- **定义**: 事后认为事件结果是可预见的
- **检测问题**:
  - 是否认为结果"早就可以预见"？
  - 是否重新解释了历史？
  - 是否低估了事前的不确定性？
- **检测结果**: 严重/中度/轻微/不存在
- **证据**:
- **缓解策略**:

### 3. 群体思维偏见

#### 👥 从众效应 (Bandwagon Effect) - 权重: 10%
- **定义**: 因为许多人持有某种信念而倾向于采纳相同信念
- **检测问题**:
  - 是否过度依赖多数人的观点？
  - 是否因为某观点流行或权威而接受？
  - 是否独立思考而非盲从？
- **检测结果**: 严重/中度/轻微/不存在
- **证据**:
- **缓解策略**:

#### 🧩 内群体偏见 (In-group Bias) - 权重: 10%
- **定义**: 倾向于偏爱自己所属群体的成员，对外群体成员持有偏见
- **检测问题**:
  - 是否对自己群体的观点或行为更为宽容？
  - 是否对外部群体持有刻板印象或偏见？
  - 是否能够客观评估不同群体的观点？
- **检测结果**: 严重/中度/轻微/不存在
- **证据**:
- **缓解策略**:

### 4. 决策偏见

#### 💸 沉没成本谬误 (Sunk Cost Fallacy) - 权重: 5%
- **定义**: 因为已经投入资源而继续投资失败项目
- **检测问题**:
  - 是否因为已投入而不愿放弃？
  - 是否忽视了未来收益和成本？
- **检测结果**: 严重/中度/轻微/不存在
- **证据**:
- **缓解策略**:

#### 🖼️ 框架效应 (Framing Effect) - 权重: 5%
- **定义**: 因问题呈现方式不同而做出不同决策
- **检测问题**:
  - 是否受到问题表述方式的过度影响？
  - 是否能从多角度审视同一问题？
- **检测结果**: 严重/中度/轻微/不存在
- **证据**:
- **缓解策略**:

## 综合偏见评估

### 偏见风险评分
- 信息处理偏见: _/10 × 45% = _
- 自我认知偏见: _/10 × 25% = _
- 群体思维偏见: _/10 × 20% = _
- 决策偏见: _/10 × 10% = _

**加权总分**: _/10分

### 偏见风险等级
- 8.0-10.0: 高风险 - 严重偏见，显著影响判断
- 5.0-7.9: 中风险 - 明显偏见，部分影响判断
- 2.0-4.9: 低风险 - 轻微偏见，影响有限
- 0.0-1.9: 微风险 - 几乎无偏见，判断相对客观

**偏见风险等级**: _

### 主要偏见类型
1. 
2. 
3. 

### 偏见缓解策略
1. 
2. 
3. 

### 改进优先级
1. 首要改进: 
2. 次要改进: 
3. 长期关注: 

## JSON输出格式
```json
{{
  "analysis_subject": "分析内容的简要描述",
  "analysis_context": "分析背景的简要描述",
  "bias_detection": {{
    "confirmation_bias": {{
      "detected": true,
      "evidence": "证据描述",
      "mitigation": "缓解策略"
    }},
    "anchoring_bias": {{
      "detected": false,
      "evidence": "证据描述",
      "mitigation": "缓解策略"
    }}
  }},
  "overall_assessment": {{
    "risk_level": "偏见风险等级",
    "main_biases": ["主要偏见1", "主要偏见2"],
    "mitigation_strategies": ["缓解策略1", "缓解策略2"]
  }}
}}
```

请开始认知偏见分析："""
    return template


def get_low_complexity_template(content: str, context: str) -> str:
    """
    Get the low complexity bias detection template.

    Args:
        content: The content to be analyzed
        context: The context of the analysis

    Returns:
        str: The formatted template
    """
    template = f"""# 深度思考：基础认知偏见检测

请分析以下内容中可能存在的认知偏见：

**分析内容**: {content}
**分析背景**: {context}
**分析复杂度**: 低

## 常见认知偏见检查清单

### 🔍 确认偏误 (Confirmation Bias)
- 是否只寻找支持既有观点的信息？
- 是否忽略了相反的证据？
- 检测结果：存在/不存在，证据：
- 缓解建议：

### ⚓ 锚定效应 (Anchoring Bias)
- 是否过度依赖最初获得的信息？
- 后续判断是否受到初始印象影响？
- 检测结果：存在/不存在，证据：
- 缓解建议：

### 📊 可得性启发 (Availability Heuristic)
- 是否因为某些例子容易想起就认为更常见？
- 判断是否受到媒体报道频率影响？
- 检测结果：存在/不存在，证据：
- 缓解建议：

### 🎯 代表性启发 (Representativeness Heuristic)
- 是否基于刻板印象进行判断？
- 是否忽略了基础概率？
- 检测结果：存在/不存在，证据：
- 缓解建议：

### 💪 过度自信 (Overconfidence Bias)
- 对自己的判断是否过于确信？
- 是否低估了不确定性？
- 检测结果：存在/不存在，证据：
- 缓解建议：

### 🔄 后见之明偏误 (Hindsight Bias)
- 是否认为结果"早就可以预见"？
- 是否重新解释了历史？
- 检测结果：存在/不存在，证据：
- 缓解建议：

## 偏见缓解建议
请针对检测到的偏见提供具体的缓解策略：
1. 
2. 
3. 

## 总体评估
- 偏见风险等级：低/中/高
- 主要偏见类型：
- 改进优先级：

## JSON输出格式
```json
{{
  "analysis_subject": "分析内容的简要描述",
  "analysis_context": "分析背景的简要描述",
  "bias_detection": {{
    "confirmation_bias": {{
      "detected": true,
      "evidence": "证据描述",
      "mitigation": "缓解策略"
    }},
    "anchoring_bias": {{
      "detected": false,
      "evidence": "证据描述",
      "mitigation": "缓解策略"
    }}
  }},
  "overall_assessment": {{
    "risk_level": "偏见风险等级",
    "main_biases": ["主要偏见1", "主要偏见2"],
    "mitigation_strategies": ["缓解策略1", "缓解策略2"]
  }}
}}
```

请开始认知偏见分析："""
    return template
