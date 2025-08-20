"""
Critical Evaluation Template for Deep Thinking Engine

This module provides templates for critical evaluation based on Paul-Elder standards.
"""

from typing import Dict, Any


def get_critical_evaluation_template(params: Dict[str, Any]) -> str:
    """
    Get the critical evaluation template with the specified parameters.

    Args:
        params: Dictionary containing template parameters:
            - content: The content to be evaluated
            - context: The context of the evaluation
            - complexity: The complexity level (high, medium, low)

    Returns:
        str: The formatted template
    """
    # Extract parameters with defaults
    content = params.get("content", "[content]")
    context = params.get("context", "[context]")
    complexity = params.get("complexity", "medium")

    # Select the appropriate template based on complexity
    if complexity == "high":
        return get_high_complexity_template(content, context)
    elif complexity == "low":
        return get_low_complexity_template(content, context)
    else:  # Default to medium
        return get_medium_complexity_template(content, context)


def get_high_complexity_template(content: str, context: str) -> str:
    """
    Get the high complexity critical evaluation template.

    Args:
        content: The content to be evaluated
        context: The context of the evaluation

    Returns:
        str: The formatted template
    """
    return f"""# 深度思考：高级批判性评估

请基于Paul-Elder批判性思维标准对以下内容进行全面、深入的评估：

**评估内容**: {content}
**评估背景**: {context}
**评估复杂度**: 高

## Paul-Elder九大标准评估框架

### 1. 准确性 (Accuracy) - 权重: 12%
- **定义**: 信息是否符合事实，没有错误或失真
- **评估问题**:
  - 陈述的事实是否有可验证的证据支持？
  - 引用的数据和统计是否来自可靠来源？
  - 是否存在事实错误或误导性表述？
  - 是否混淆了事实和观点？
- **评分标准**:
  - 10分: 所有信息完全准确，有充分可靠证据支持
  - 7-9分: 大部分信息准确，偶有小错误但不影响核心论点
  - 4-6分: 信息部分准确，存在一些重要错误
  - 1-3分: 信息大多不准确，存在严重错误或误导
- **评分**: _/10分
- **详细理由**:
- **改进建议**:

### 2. 精确性 (Precision) - 权重: 12%
- **定义**: 表述是否具体、明确、详细，避免模糊和歧义
- **评估问题**:
  - 使用的术语和概念是否明确定义？
  - 表述是否足够具体而非笼统？
  - 是否提供了足够的细节和具体例子？
  - 数据表示是否精确（如使用确切数字而非模糊范围）？
- **评分标准**:
  - 10分: 表述极其精确，所有术语清晰定义，细节丰富
  - 7-9分: 表述相当精确，大多数概念明确，细节充分
  - 4-6分: 表述部分精确，一些概念模糊，细节不足
  - 1-3分: 表述极不精确，概念混乱，几乎没有具体细节
- **评分**: _/10分
- **详细理由**:
- **改进建议**:

### 3. 相关性 (Relevance) - 权重: 10%
- **定义**: 内容是否与主题直接相关，避免离题和不必要的信息
- **评估问题**:
  - 所提供的信息是否直接支持核心论点？
  - 是否包含与主题无关的内容？
  - 论据与结论之间的关联是否清晰？
  - 是否优先处理了最相关的方面？
- **评分标准**:
  - 10分: 所有内容高度相关，紧密围绕核心主题
  - 7-9分: 大部分内容相关，偶有不直接相关的内容
  - 4-6分: 部分内容相关，存在明显离题内容
  - 1-3分: 大部分内容不相关，严重偏离主题
- **评分**: _/10分
- **详细理由**:
- **改进建议**:

### 4. 逻辑性 (Logic) - 权重: 12%
- **定义**: 推理过程是否合乎逻辑，避免谬误和矛盾
- **评估问题**:
  - 论证结构是否清晰合理？
  - 前提是否支持结论？
  - 是否存在逻辑谬误（如循环论证、稻草人谬误、诉诸权威等）？
  - 是否存在内部矛盾？
- **评分标准**:
  - 10分: 推理完全合乎逻辑，论证严密，没有谬误
  - 7-9分: 推理大体合乎逻辑，论证较为严密，极少谬误
  - 4-6分: 推理部分合乎逻辑，论证松散，存在明显谬误
  - 1-3分: 推理严重不合逻辑，充满谬误和矛盾
- **评分**: _/10分
- **详细理由**:
- **改进建议**:

### 5. 广度 (Breadth) - 权重: 10%
- **定义**: 是否考虑了多种观点和角度，避免狭隘视角
- **评估问题**:
  - 是否考虑了不同的观点和立场？
  - 是否涵盖了问题的多个方面？
  - 是否考虑了反对意见和替代解释？
  - 是否跨学科地分析了问题？
- **评分标准**:
  - 10分: 全面考虑多种观点，包括反对意见，视野极为开阔
  - 7-9分: 考虑了多种主要观点，视野较为开阔
  - 4-6分: 仅考虑了有限几种观点，视野较为狭窄
  - 1-3分: 几乎只考虑单一观点，视野极为狭隘
- **评分**: _/10分
- **详细理由**:
- **改进建议**:

### 6. 深度 (Depth) - 权重: 12%
- **定义**: 分析是否深入探讨了复杂性和根本问题，避免肤浅
- **评估问题**:
  - 是否深入探讨了问题的根本原因？
  - 是否处理了问题的复杂性和微妙之处？
  - 是否超越了表面现象探究深层结构？
  - 是否考虑了长期影响和系统性因素？
- **评分标准**:
  - 10分: 分析极其深入，探讨根本问题，处理复杂性
  - 7-9分: 分析相当深入，探讨主要根本问题
  - 4-6分: 分析深度一般，主要停留在表面层次
  - 1-3分: 分析极其肤浅，完全未触及根本问题
- **评分**: _/10分
- **详细理由**:
- **改进建议**:

### 7. 重要性 (Significance) - 权重: 10%
- **定义**: 是否关注了最重要的问题和因素，正确设置优先级
- **评估问题**:
  - 是否识别并关注了最重要的问题？
  - 是否区分了核心问题和次要问题？
  - 是否正确评估了不同因素的相对重要性？
  - 是否避免了过分关注琐碎细节？
- **评分标准**:
  - 10分: 完美把握重点，优先处理最重要问题
  - 7-9分: 大体把握重点，主要关注重要问题
  - 4-6分: 部分把握重点，同时关注一些次要问题
  - 1-3分: 完全未把握重点，主要关注琐碎问题
- **评分**: _/10分
- **详细理由**:
- **改进建议**:

### 8. 公正性 (Fairness) - 权重: 12%
- **定义**: 是否客观公正地处理不同观点，避免偏见和预设立场
- **评估问题**:
  - 是否公平呈现不同立场和观点？
  - 是否避免了情绪化语言和偏见表达？
  - 是否考虑了自身可能的认知偏误？
  - 是否基于证据而非个人偏好做出判断？
- **评分标准**:
  - 10分: 极其公正客观，完全避免偏见，平等对待所有观点
  - 7-9分: 相当公正，基本避免偏见，较为平等地对待主要观点
  - 4-6分: 部分公正，存在一些偏见，对某些观点明显偏向
  - 1-3分: 极不公正，充满偏见，完全偏向特定观点
- **评分**: _/10分
- **详细理由**:
- **改进建议**:

### 9. 清晰性 (Clarity) - 权重: 10%
- **定义**: 表达是否清晰易懂，结构是否条理分明
- **评估问题**:
  - 语言表达是否清晰简洁？
  - 结构组织是否条理分明？
  - 是否使用了适当的例子和说明？
  - 是否避免了不必要的复杂术语和晦涩表达？
- **评分标准**:
  - 10分: 表达极其清晰，结构完美，易于理解
  - 7-9分: 表达相当清晰，结构良好，较易理解
  - 4-6分: 表达部分清晰，结构一般，理解有难度
  - 1-3分: 表达极不清晰，结构混乱，难以理解
- **评分**: _/10分
- **详细理由**:
- **改进建议**:

## 综合评估

### 加权总分计算
- 准确性: _/10 × 12% = _
- 精确性: _/10 × 12% = _
- 相关性: _/10 × 10% = _
- 逻辑性: _/10 × 12% = _
- 广度: _/10 × 10% = _
- 深度: _/10 × 12% = _
- 重要性: _/10 × 10% = _
- 公正性: _/10 × 12% = _
- 清晰性: _/10 × 10% = _

**加权总分**: _/10分

### 质量等级
- 9.0-10.0: 卓越 (Outstanding)
- 8.0-8.9: 优秀 (Excellent)
- 7.0-7.9: 良好 (Good)
- 6.0-6.9: 合格 (Satisfactory)
- 5.0-5.9: 需改进 (Needs Improvement)
- <5.0: 不合格 (Unsatisfactory)

**质量等级**: _

### 主要优势
1. 
2. 
3. 

### 主要不足
1. 
2. 
3. 

### 改进建议
1. 
2. 
3. 
4. 
5. 

### 是否需要重新分析
- [ ] 是，需要全面重新分析
- [ ] 是，需要部分修改和改进
- [ ] 否，质量已达到要求标准

## 输出验证检查清单
1. 是否对所有九个标准都进行了评分？
2. 评分理由是否具体且基于证据？
3. 改进建议是否具体可行？
4. 加权总分计算是否准确？
5. 是否提供了明确的质量等级判断？

## JSON输出格式
```json
{
  "evaluation_subject": "评估内容的简要描述",
  "evaluation_context": "评估背景的简要描述",
  "standards_evaluation": {
    "accuracy": {
      "score": 0,
      "reasoning": "评分理由",
      "suggestions": "改进建议"
    },
    "precision": {
      "score": 0,
      "reasoning": "评分理由",
      "suggestions": "改进建议"
    },
    "relevance": {
      "score": 0,
      "reasoning": "评分理由",
      "suggestions": "改进建议"
    },
    "logic": {
      "score": 0,
      "reasoning": "评分理由",
      "suggestions": "改进建议"
    },
    "breadth": {
      "score": 0,
      "reasoning": "评分理由",
      "suggestions": "改进建议"
    },
    "depth": {
      "score": 0,
      "reasoning": "评分理由",
      "suggestions": "改进建议"
    },
    "significance": {
      "score": 0,
      "reasoning": "评分理由",
      "suggestions": "改进建议"
    },
    "fairness": {
      "score": 0,
      "reasoning": "评分理由",
      "suggestions": "改进建议"
    },
    "clarity": {
      "score": 0,
      "reasoning": "评分理由",
      "suggestions": "改进建议"
    }
  },
  "overall_assessment": {
    "weighted_score": 0,
    "quality_level": "质量等级",
    "strengths": [
      "优势1",
      "优势2",
      "优势3"
    ],
    "weaknesses": [
      "不足1",
      "不足2",
      "不足3"
    ],
    "improvement_suggestions": [
      "建议1",
      "建议2",
      "建议3",
      "建议4",
      "建议5"
    ],
    "requires_reanalysis": true/false
  }
}
```

请开始详细评估："""


def get_medium_complexity_template(content: str, context: str) -> str:
    """
    Get the medium complexity critical evaluation template.

    Args:
        content: The content to be evaluated
        context: The context of the evaluation

    Returns:
        str: The formatted template
    """
    return f"""# 深度思考：批判性评估

请基于Paul-Elder批判性思维标准评估以下内容：

**评估内容**: {content}
**评估背景**: {context}
**评估复杂度**: 中等

## Paul-Elder九大标准评估

### 1. 准确性 (Accuracy) - 权重: 12%
- **定义**: 信息是否符合事实，没有错误或失真
- **评估问题**:
  - 陈述的事实是否有证据支持？
  - 引用的数据和统计是否可靠？
  - 是否存在事实错误？
- **评分**: _/10分
- **理由**:
- **改进建议**:

### 2. 精确性 (Precision) - 权重: 12%  
- **定义**: 表述是否具体、明确、详细
- **评估问题**:
  - 使用的术语是否明确？
  - 表述是否具体而非笼统？
  - 是否提供了足够的细节？
- **评分**: _/10分
- **理由**:
- **改进建议**:

### 3. 相关性 (Relevance) - 权重: 10%
- **定义**: 内容是否与主题直接相关
- **评估问题**:
  - 信息是否支持核心论点？
  - 是否包含无关内容？
  - 论据与结论的关联是否清晰？
- **评分**: _/10分
- **理由**:
- **改进建议**:

### 4. 逻辑性 (Logic) - 权重: 12%
- **定义**: 推理过程是否合乎逻辑
- **评估问题**:
  - 论证结构是否合理？
  - 前提是否支持结论？
  - 是否存在逻辑谬误？
- **评分**: _/10分
- **理由**:
- **改进建议**:

### 5. 广度 (Breadth) - 权重: 10%
- **定义**: 是否考虑了多种观点和角度
- **评估问题**:
  - 是否考虑了不同观点？
  - 是否涵盖了问题的多个方面？
  - 是否考虑了反对意见？
- **评分**: _/10分
- **理由**:
- **改进建议**:

### 6. 深度 (Depth) - 权重: 12%
- **定义**: 分析是否深入探讨了复杂性
- **评估问题**:
  - 是否探讨了问题的根本原因？
  - 是否处理了问题的复杂性？
  - 是否超越了表面现象？
- **评分**: _/10分
- **理由**:
- **改进建议**:

### 7. 重要性 (Significance) - 权重: 10%
- **定义**: 是否关注了最重要的问题
- **评估问题**:
  - 是否识别了最重要的问题？
  - 是否区分了核心和次要问题？
  - 是否正确设置了优先级？
- **评分**: _/10分
- **理由**:
- **改进建议**:

### 8. 公正性 (Fairness) - 权重: 12%
- **定义**: 是否客观公正地处理不同观点
- **评估问题**:
  - 是否公平呈现不同立场？
  - 是否避免了偏见表达？
  - 是否基于证据做出判断？
- **评分**: _/10分
- **理由**:
- **改进建议**:

### 9. 清晰性 (Clarity) - 权重: 10%
- **定义**: 表达是否清晰易懂，结构是否条理
- **评估问题**:
  - 语言表达是否清晰？
  - 结构组织是否条理？
  - 是否易于理解？
- **评分**: _/10分
- **理由**:
- **改进建议**:

## 综合评估

### 加权总分计算
- 准确性: _/10 × 12% = _
- 精确性: _/10 × 12% = _
- 相关性: _/10 × 10% = _
- 逻辑性: _/10 × 12% = _
- 广度: _/10 × 10% = _
- 深度: _/10 × 12% = _
- 重要性: _/10 × 10% = _
- 公正性: _/10 × 12% = _
- 清晰性: _/10 × 10% = _

**加权总分**: _/10分

### 质量等级
- 9.0-10.0: 卓越 (Outstanding)
- 8.0-8.9: 优秀 (Excellent)
- 7.0-7.9: 良好 (Good)
- 6.0-6.9: 合格 (Satisfactory)
- 5.0-5.9: 需改进 (Needs Improvement)
- <5.0: 不合格 (Unsatisfactory)

**质量等级**: _

### 主要优势
1. 
2. 
3. 

### 主要不足
1. 
2. 
3. 

### 改进建议
1. 
2. 
3. 

### 是否需要重新分析
- [ ] 是，需要重新分析
- [ ] 否，质量已达到要求标准

## JSON输出格式
```json
{
  "evaluation_subject": "评估内容的简要描述",
  "evaluation_context": "评估背景的简要描述",
  "standards_evaluation": {
    "accuracy": {
      "score": 0,
      "reasoning": "评分理由",
      "suggestions": "改进建议"
    },
    "precision": {
      "score": 0,
      "reasoning": "评分理由",
      "suggestions": "改进建议"
    },
    "relevance": {
      "score": 0,
      "reasoning": "评分理由",
      "suggestions": "改进建议"
    },
    "logic": {
      "score": 0,
      "reasoning": "评分理由",
      "suggestions": "改进建议"
    },
    "breadth": {
      "score": 0,
      "reasoning": "评分理由",
      "suggestions": "改进建议"
    },
    "depth": {
      "score": 0,
      "reasoning": "评分理由",
      "suggestions": "改进建议"
    },
    "significance": {
      "score": 0,
      "reasoning": "评分理由",
      "suggestions": "改进建议"
    },
    "fairness": {
      "score": 0,
      "reasoning": "评分理由",
      "suggestions": "改进建议"
    },
    "clarity": {
      "score": 0,
      "reasoning": "评分理由",
      "suggestions": "改进建议"
    }
  },
  "overall_assessment": {
    "weighted_score": 0,
    "quality_level": "质量等级",
    "strengths": [
      "优势1",
      "优势2",
      "优势3"
    ],
    "weaknesses": [
      "不足1",
      "不足2",
      "不足3"
    ],
    "improvement_suggestions": [
      "建议1",
      "建议2",
      "建议3"
    ],
    "requires_reanalysis": true/false
  }
}
```

请开始详细评估："""


def get_low_complexity_template(content: str, context: str) -> str:
    """
    Get the low complexity critical evaluation template.

    Args:
        content: The content to be evaluated
        context: The context of the evaluation

    Returns:
        str: The formatted template
    """
    return f"""# 深度思考：基础批判性评估

请基于Paul-Elder批判性思维标准评估以下内容：

**评估内容**: {content}
**评估背景**: {context}
**评估复杂度**: 低

## Paul-Elder九大标准评估

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

## 总体评估
- 综合得分：___/90分
- 主要优势：
- 改进建议：
- 是否需要重新分析：是/否

## JSON输出格式
```json
{
  "evaluation_subject": "评估内容的简要描述",
  "evaluation_context": "评估背景的简要描述",
  "standards_scores": {
    "accuracy": 0,
    "precision": 0,
    "relevance": 0,
    "logic": 0,
    "breadth": 0,
    "depth": 0,
    "significance": 0,
    "fairness": 0,
    "clarity": 0
  },
  "overall_assessment": {
    "total_score": 0,
    "strengths": ["优势1", "优势2"],
    "improvement_suggestions": ["建议1", "建议2"],
    "requires_reanalysis": true/false
  }
}
```

请开始评估："""
