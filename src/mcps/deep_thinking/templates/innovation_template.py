"""
Innovation Thinking Template for Deep Thinking Engine

This module provides templates for creative thinking and innovation using methods like SCAMPER,
TRIZ, and other creative thinking techniques. The templates are designed to help users
generate innovative ideas, evaluate them, and develop implementation plans.
"""

from typing import Dict, Any


def get_innovation_template(params: Dict[str, Any]) -> str:
    """
    Get the innovation thinking template with the specified parameters.

    Args:
        params: Dictionary containing template parameters:
            - concept: The base concept to innovate upon
            - direction: The desired innovation direction
            - constraints: Any constraints to consider
            - method: The innovation method to use (scamper, triz, etc.)
            - complexity: The complexity level (high, medium, low)

    Returns:
        str: The formatted template
    """
    # Extract parameters with defaults
    concept = params.get("concept", "[concept]")
    direction = params.get("direction", "[direction]")
    constraints = params.get("constraints", "[constraints]")
    method = params.get("method", "scamper").lower()
    complexity = params.get("complexity", "medium")

    # Select the appropriate template based on complexity
    if complexity.lower() in ["high", "高"]:
        return get_high_complexity_template(concept, direction, constraints, method)
    elif complexity.lower() in ["low", "低"]:
        return get_low_complexity_template(concept, direction, constraints, method)
    else:  # Default to medium
        return get_medium_complexity_template(concept, direction, constraints, method)


def get_high_complexity_template(
    concept: str, direction: str, constraints: str, method: str
) -> str:
    """
    Get the high complexity innovation template.

    Args:
        concept: The base concept to innovate upon
        direction: The desired innovation direction
        constraints: Any constraints to consider
        method: The innovation method to use

    Returns:
        str: The formatted template
    """
    template = f"""# 深度思考：高级创新思维激发

使用多种创新方法对以下概念进行系统性创新思考：

**基础概念**: {concept}
**创新方向**: {direction}
**约束条件**: {constraints}
**创新方法**: {method}
**思考复杂度**: 高

## 多维创新思维框架

### 1. SCAMPER创新技法 - 系统性创新

#### S - Substitute (替代) - 权重: 12%
- **核心问题**:
  - 可以用什么来替代现有的元素、材料、人员或流程？
  - 如果移除某个组件，用什么替代能提升价值？
  - 能否引入其他领域的替代方案？
  - 如何通过替代解决现有痛点？
- **思考方向**:
  - 材料替代: 更环保、更高效、更经济的材料选择
  - 流程替代: 简化或优化现有流程的替代方案
  - 功能替代: 实现相同功能的替代机制
  - 角色替代: 重新分配或重构责任和角色
- **创新想法**:
  1. 
  2. 
  3. 

#### C - Combine (结合) - 权重: 12%
- **核心问题**:
  - 可以将哪些元素、功能或概念结合起来？
  - 能否融合不同领域的概念创造新价值？
  - 如何通过组合创造协同效应？
  - 跨学科结合能带来什么突破？
- **思考方向**:
  - 功能整合: 将多个功能整合到单一解决方案
  - 跨领域融合: 结合不同行业或学科的概念
  - 资源组合: 整合多种资源创造新价值
  - 服务捆绑: 创造增值服务组合
- **创新想法**:
  1. 
  2. 
  3. 

#### A - Adapt (适应) - 权重: 12%
- **核心问题**:
  - 可以从其他领域、产品或服务借鉴什么？
  - 历史上的解决方案如何适应当前问题？
  - 自然界中有哪些可借鉴的模式？
  - 如何调整现有方案以适应新环境？
- **思考方向**:
  - 跨领域迁移: 将其他领域的成功模式迁移应用
  - 生物模拟: 借鉴自然界的解决方案(仿生学)
  - 历史借鉴: 重新审视历史上的解决方案
  - 文化适应: 根据不同文化背景调整方案
- **创新想法**:
  1. 
  2. 
  3. 

#### M - Modify/Magnify/Minify (修改/放大/缩小) - 权重: 12%
- **核心问题**:
  - 如何通过改变规模、频率或特性创造价值？
  - 放大哪些方面可以带来突破？
  - 简化或缩小哪些方面可以提升效率？
  - 如何通过调整参数优化性能？
- **思考方向**:
  - 规模调整: 扩大或缩小规模以创造新价值
  - 特性增强: 强化关键特性以提升竞争力
  - 简化设计: 减少复杂性提高可用性
  - 参数优化: 调整关键参数以提升性能
- **创新想法**:
  1. 
  2. 
  3. 

#### P - Put to Other Uses (其他用途) - 权重: 12%
- **核心问题**:
  - 现有产品、服务或概念还有什么其他用途？
  - 如何在新场景中应用现有解决方案？
  - 废弃物或副产品有什么潜在价值？
  - 如何拓展目标用户群体？
- **思考方向**:
  - 场景拓展: 在新场景中应用现有解决方案
  - 用户群体扩展: 为新用户群体提供价值
  - 副产品价值: 发掘废弃物或副产品的潜在价值
  - 功能拓展: 发现现有产品的隐藏功能
- **创新想法**:
  1. 
  2. 
  3. 

#### E - Eliminate (消除) - 权重: 12%
- **核心问题**:
  - 可以去掉哪些不必要的部分或流程？
  - 如何通过简化创造更大价值？
  - 哪些假设可以被质疑或消除？
  - 如何减少资源消耗或环境影响？
- **思考方向**:
  - 精简设计: 去除不必要的组件或功能
  - 流程优化: 消除冗余或低效环节
  - 假设挑战: 质疑并消除限制性假设
  - 资源节约: 减少材料、能源或时间消耗
- **创新想法**:
  1. 
  2. 
  3. 

#### R - Reverse/Rearrange (逆转/重组) - 权重: 12%
- **核心问题**:
  - 能否颠倒顺序、角色或因果关系？
  - 如何重新排列组件或流程？
  - 逆向思考能带来什么突破？
  - 如何通过重组创造新价值？
- **思考方向**:
  - 流程逆转: 改变传统流程顺序
  - 角色互换: 重新定义参与者角色
  - 因果重构: 挑战传统因果关系
  - 布局重组: 重新安排物理或逻辑布局
- **创新想法**:
  1. 
  2. 
  3. 

### 2. TRIZ创新原理应用 - 权重: 16%

TRIZ(发明问题解决理论)提供了40个创新原理，以下是最适用于当前问题的原理：

#### 分割原理 (Segmentation)
- 将对象分割成独立部分
- 增加对象的模块化程度
- 使组件易于拆卸或重组
- 应用思路:

#### 提取原理 (Extraction)
- 提取(分离)对象的干扰部分或属性
- 仅提取必要的部分或属性
- 分离有用的部分或属性
- 应用思路:

#### 局部质量原理 (Local Quality)
- 从均质结构转向非均质结构
- 让每个部分发挥最佳功能
- 为不同功能创建最佳局部条件
- 应用思路:

#### 非对称原理 (Asymmetry)
- 从对称形式转向非对称形式
- 增加现有非对称程度
- 适应非对称环境或需求
- 应用思路:

#### 合并原理 (Merging)
- 在空间上合并相同或相似的对象
- 合并相同或相似的操作
- 创建时间或空间上的并行处理
- 应用思路:

#### 通用性原理 (Universality)
- 使对象执行多种功能
- 减少其他对象的需求
- 创建多用途解决方案
- 应用思路:

#### 嵌套原理 (Nesting)
- 将一个对象放入另一个对象
- 将一个对象穿过另一个对象的空腔
- 创建多层结构
- 应用思路:

#### 预先行动原理 (Preliminary Action)
- 提前执行所需的变更
- 预先安排对象以便立即使用
- 预防而非应对问题
- 应用思路:

### 3. 跨领域启发 - 权重: 12%

从以下不同领域寻找创新灵感：

#### 自然界启发
- **生物模拟 (Biomimicry)**: 
  - 自然界中有哪些解决类似问题的机制？
  - 生物适应性策略如何应用到当前问题？
  - 哪些动植物特性可以启发解决方案？
  - 自然界的材料特性有何启示？
- **生态系统 (Ecosystems)**: 
  - 自然生态系统的平衡机制有何启示？
  - 共生关系如何启发新的合作模式？
  - 资源循环利用模式如何借鉴？
  - 生态系统的弹性机制有何启示？
- **进化策略 (Evolutionary Strategies)**: 
  - 进化过程中的优化机制如何借鉴？
  - 自然选择原理如何应用于设计？
  - 适应性变异如何启发创新？
  - 渐进式改进与突变如何平衡？
- **创新想法**:
  1. 
  2. 
  3. 

#### 艺术与设计启发
- **美学原则 (Aesthetic Principles)**: 
  - 如何应用艺术美学提升体验？
  - 形式与功能的平衡如何优化？
  - 色彩理论如何影响用户感知？
  - 视觉层次如何引导注意力？
- **叙事结构 (Narrative Structures)**: 
  - 故事讲述方式如何应用于问题解决？
  - 情感连接如何增强用户体验？
  - 冲突与解决模式有何启示？
  - 如何创造引人入胜的体验旅程？
- **创作过程 (Creative Processes)**: 
  - 艺术创作的迭代方法有何启示？
  - 约束如何激发创造力？
  - 不同艺术流派的思维方式有何借鉴？
  - 如何平衡传统与创新？
- **创新想法**:
  1. 
  2. 
  3. 

#### 科技前沿启发
- **新兴技术 (Emerging Technologies)**: 
  - 前沿技术如何应用于当前问题？
  - 技术融合能创造什么新可能？
  - 哪些技术趋势可能颠覆现有解决方案？
  - 如何利用技术降低实施门槛？
- **计算模型 (Computational Models)**: 
  - 算法思维如何优化决策过程？
  - 数据驱动方法如何增强解决方案？
  - 人工智能如何辅助或增强功能？
  - 分布式系统原理有何启示？
- **人机交互 (Human-Computer Interaction)**: 
  - 新型交互模式有何启示？
  - 如何降低认知负荷？
  - 无缝体验设计原则如何应用？
  - 如何平衡自动化与用户控制？
- **创新想法**:
  1. 
  2. 
  3. 

#### 社会科学启发
- **行为经济学 (Behavioral Economics)**: 
  - 人类决策偏好如何影响解决方案？
  - 激励机制如何优化？
  - 如何利用行为洞察提高采纳率？
  - 选择架构如何引导更好决策？
- **组织理论 (Organizational Theory)**: 
  - 新型组织结构有何启示？
  - 分布式决策模式如何应用？
  - 团队协作模式有何借鉴？
  - 如何平衡自主性与协调性？
- **文化差异 (Cultural Perspectives)**: 
  - 跨文化视角如何拓展思路？
  - 不同文化的价值观如何影响设计？
  - 如何创造包容性解决方案？
  - 全球化与本地化如何平衡？
- **创新想法**:
  1. 
  2. 
  3. 

## 创新评估与筛选

### 创新想法综合评分
请对生成的创新想法进行多维度评估：

#### 1. 新颖性 (Novelty) - 权重: 25%
- **评分标准**:
  - 10分: 颠覆性创新，市场上前所未见
  - 7-9分: 显著创新，有明显差异化特点
  - 4-6分: 中等创新，有一定改进
  - 1-3分: 微小创新，与现有解决方案相似
- **评分理由**:

#### 2. 可行性 (Feasibility) - 权重: 25%
- **评分标准**:
  - 10分: 立即可实施，无技术障碍
  - 7-9分: 可在短期内实施，技术障碍小
  - 4-6分: 中期可实施，需克服一定技术挑战
  - 1-3分: 长期愿景，存在重大技术障碍
- **评分理由**:

#### 3. 价值潜力 (Value Potential) - 权重: 25%
- **评分标准**:
  - 10分: 革命性价值，可创造新市场
  - 7-9分: 高价值，显著优于现有解决方案
  - 4-6分: 中等价值，有明确改进
  - 1-3分: 低价值，改进有限
- **评分理由**:

#### 4. 适应性 (Adaptability) - 权重: 15%
- **评分标准**:
  - 10分: 高度适应性，可应用于多种场景
  - 7-9分: 良好适应性，可扩展到相关领域
  - 4-6分: 中等适应性，适用于特定场景
  - 1-3分: 低适应性，应用场景有限
- **评分理由**:

#### 5. 可持续性 (Sustainability) - 权重: 10%
- **评分标准**:
  - 10分: 显著正面环境社会影响
  - 7-9分: 良好可持续性表现
  - 4-6分: 中性影响
  - 1-3分: 存在可持续性挑战
- **评分理由**:

### 创新组合策略
如何将多个创新想法组合形成整体解决方案：

1. 核心创新组合:
2. 互补创新组合:
3. 阶段性实施策略:

### 实施路径与风险分析

#### 实施路径
1. 短期行动 (0-6个月):
2. 中期发展 (6-18个月):
3. 长期愿景 (18+个月):

#### 风险分析
1. 技术风险:
   - 风险描述:
   - 缓解策略:
2. 市场风险:
   - 风险描述:
   - 缓解策略:
3. 执行风险:
   - 风险描述:
   - 缓解策略:

## 创新思维元分析
请对本次创新思考过程进行元分析：

1. 思维多样性:
   - 是否充分探索了不同思维路径？
   - 是否存在思维定势？

2. 创新深度:
   - 是否超越了表面改进？
   - 是否触及核心问题？

3. 约束处理:
   - 是否将约束视为创新机会？
   - 是否过度受限于现有条件？

4. 改进方向:
   - 下次创新思考如何改进？
   - 哪些思维工具效果最佳？

## JSON输出格式
```json
{{
  "innovation_subject": "创新主题",
  "innovation_direction": "创新方向",
  "constraints": "约束条件",
  "scamper_ideas": [
    {{
      "category": "Substitute",
      "idea": "创新想法描述",
      "novelty_score": 8,
      "feasibility_score": 7,
      "value_score": 9
    }},
    {{
      "category": "Combine",
      "idea": "创新想法描述",
      "novelty_score": 9,
      "feasibility_score": 6,
      "value_score": 8
    }}
  ],
  "cross_domain_ideas": [
    {{
      "domain": "自然界启发",
      "idea": "创新想法描述",
      "novelty_score": 9,
      "feasibility_score": 5,
      "value_score": 8
    }}
  ],
  "top_innovations": [
    {{
      "idea": "最佳创新想法1",
      "combined_score": 8.5,
      "implementation_path": "实施路径"
    }},
    {{
      "idea": "最佳创新想法2",
      "combined_score": 8.2,
      "implementation_path": "实施路径"
    }}
  ]
}}
```

请开始系统性创新思考："""
    return template


def get_medium_complexity_template(
    concept: str, direction: str, constraints: str, method: str
) -> str:
    """
    Get the medium complexity innovation template.

    Args:
        concept: The base concept to innovate upon
        direction: The desired innovation direction
        constraints: Any constraints to consider
        method: The innovation method to use

    Returns:
        str: The formatted template
    """
    template = f"""# 深度思考：创新思维激发

使用{method}方法对以下概念进行创新思考：

**基础概念**: {concept}
**创新方向**: {direction}
**约束条件**: {constraints}
**思考复杂度**: 中等

## SCAMPER创新技法

### S - Substitute (替代)
- **核心问题**:
  - 可以用什么来替代现有的元素？
  - 有哪些材料、流程、人员可以替换？
  - 如何通过替代解决现有痛点？
- **思考方向**:
  - 材料替代
  - 流程替代
  - 功能替代
- **创新想法**:
  1. 
  2. 
  3. 

### C - Combine (结合)
- **核心问题**:
  - 可以将哪些元素结合起来？
  - 能否融合不同领域的概念？
  - 如何通过组合创造协同效应？
- **思考方向**:
  - 功能整合
  - 跨领域融合
  - 资源组合
- **创新想法**:
  1. 
  2. 
  3. 

### A - Adapt (适应)
- **核心问题**:
  - 可以从其他领域借鉴什么？
  - 有哪些成功案例可以适应？
  - 自然界中有哪些可借鉴的模式？
- **思考方向**:
  - 跨领域迁移
  - 生物模拟
  - 历史借鉴
- **创新想法**:
  1. 
  2. 
  3. 

### M - Modify (修改)
- **核心问题**:
  - 可以放大或缩小什么？
  - 能否改变形状、颜色、功能？
  - 如何通过调整参数优化性能？
- **思考方向**:
  - 规模调整
  - 特性增强
  - 简化设计
- **创新想法**:
  1. 
  2. 
  3. 

### P - Put to Other Uses (其他用途)
- **核心问题**:
  - 还有什么其他用途？
  - 能否应用到不同场景？
  - 如何拓展目标用户群体？
- **思考方向**:
  - 场景拓展
  - 用户群体扩展
  - 功能拓展
- **创新想法**:
  1. 
  2. 
  3. 

### E - Eliminate (消除)
- **核心问题**:
  - 可以去掉什么不必要的部分？
  - 能否简化流程？
  - 如何减少资源消耗？
- **思考方向**:
  - 精简设计
  - 流程优化
  - 资源节约
- **创新想法**:
  1. 
  2. 
  3. 

### R - Reverse/Rearrange (逆转/重组)
- **核心问题**:
  - 能否颠倒顺序或角色？
  - 可以重新排列哪些元素？
  - 如何通过重组创造新价值？
- **思考方向**:
  - 流程逆转
  - 角色互换
  - 布局重组
- **创新想法**:
  1. 
  2. 
  3. 

## 跨领域启发

从以下领域寻找灵感：

### 自然界
- 生物适应策略:
- 生态系统平衡:
- 进化优化机制:
- **创新想法**:
  1. 
  2. 

### 艺术与设计
- 美学原则:
- 创作方法:
- 表达形式:
- **创新想法**:
  1. 
  2. 

### 科技前沿
- 新兴技术应用:
- 技术融合可能:
- 人机交互模式:
- **创新想法**:
  1. 
  2. 

### 社会科学
- 行为洞察:
- 组织模式:
- 文化视角:
- **创新想法**:
  1. 
  2. 

## 创新评估

对生成的想法进行评估：

### 1. 新颖性 (1-10分)
- 10分: 颠覆性创新，市场上前所未见
- 7-9分: 显著创新，有明显差异化特点
- 4-6分: 中等创新，有一定改进
- 1-3分: 微小创新，与现有解决方案相似

### 2. 可行性 (1-10分)
- 10分: 立即可实施，无技术障碍
- 7-9分: 可在短期内实施，技术障碍小
- 4-6分: 中期可实施，需克服一定技术挑战
- 1-3分: 长期愿景，存在重大技术障碍

### 3. 价值潜力 (1-10分)
- 10分: 革命性价值，可创造新市场
- 7-9分: 高价值，显著优于现有解决方案
- 4-6分: 中等价值，有明确改进
- 1-3分: 低价值，改进有限

### 4. 实施难度 (1-10分，越低越好)
- 1-3分: 容易实施，资源需求低
- 4-6分: 中等难度，需要适量资源
- 7-9分: 较难实施，需要大量资源
- 10分: 极难实施，技术和资源挑战巨大

## 最佳创新方案

### 方案一：[创新名称]
- **描述**:
- **优势**:
- **挑战**:
- **实施步骤**:
  1. 
  2. 
  3. 

### 方案二：[创新名称]
- **描述**:
- **优势**:
- **挑战**:
- **实施步骤**:
  1. 
  2. 
  3. 

### 方案三：[创新名称]
- **描述**:
- **优势**:
- **挑战**:
- **实施步骤**:
  1. 
  2. 
  3. 

## JSON输出格式
```json
{{
  "innovation_subject": "创新主题",
  "innovation_direction": "创新方向",
  "constraints": "约束条件",
  "complexity_level": "medium",
  "scamper_ideas": [
    {{
      "category": "Substitute",
      "idea": "创新想法描述",
      "novelty_score": 8,
      "feasibility_score": 7,
      "value_score": 9,
      "implementation_difficulty": 3,
      "combined_score": 8.0
    }},
    {{
      "category": "Combine",
      "idea": "创新想法描述",
      "novelty_score": 9,
      "feasibility_score": 6,
      "value_score": 8,
      "implementation_difficulty": 5,
      "combined_score": 7.5
    }}
  ],
  "cross_domain_ideas": [
    {{
      "domain": "自然界启发",
      "idea": "创新想法描述",
      "novelty_score": 9,
      "feasibility_score": 5,
      "value_score": 8,
      "combined_score": 7.3
    }}
  ],
  "top_innovations": [
    {{
      "name": "最佳创新方案1",
      "description": "详细描述",
      "advantages": ["优势1", "优势2", "优势3"],
      "challenges": ["挑战1", "挑战2"],
      "implementation_steps": ["步骤1", "步骤2", "步骤3"],
      "combined_score": 8.5
    }},
    {{
      "name": "最佳创新方案2",
      "description": "详细描述",
      "advantages": ["优势1", "优势2"],
      "challenges": ["挑战1", "挑战2"],
      "implementation_steps": ["步骤1", "步骤2", "步骤3"],
      "combined_score": 8.2
    }},
    {{
      "name": "最佳创新方案3",
      "description": "详细描述",
      "advantages": ["优势1", "优势2"],
      "challenges": ["挑战1", "挑战2"],
      "implementation_steps": ["步骤1", "步骤2", "步骤3"],
      "combined_score": 7.8
    }}
  ]
}}
```

请开始创新思考："""
    return template


def get_low_complexity_template(
    concept: str, direction: str, constraints: str, method: str
) -> str:
    """
    Get the low complexity innovation template.

    Args:
        concept: The base concept to innovate upon
        direction: The desired innovation direction
        constraints: Any constraints to consider
        method: The innovation method to use

    Returns:
        str: The formatted template
    """
    template = f"""# 深度思考：基础创新思维

使用简化的SCAMPER方法对以下概念进行创新思考：

**基础概念**: {concept}
**创新方向**: {direction}
**约束条件**: {constraints}
**思考复杂度**: 低

## 简化SCAMPER创新法

### S - 替代 (Substitute)
- 可以用什么来替代现有的元素、材料或方法？
- 如果移除某个部分，用什么替代能更好？
- 创新想法：
  1. 
  2. 

### C - 结合 (Combine)
- 可以将哪些功能或概念结合起来？
- 与其他产品或服务结合会怎样？
- 创新想法：
  1. 
  2. 

### A - 适应 (Adapt)
- 可以从其他地方借鉴什么想法？
- 过去的解决方案如何适应当前问题？
- 创新想法：
  1. 
  2. 

### M - 修改 (Modify)
- 可以如何改变形状、大小或功能？
- 增加或减少什么可以提升价值？
- 创新想法：
  1. 
  2. 

### P - 其他用途 (Put to other uses)
- 这个概念还有什么其他用途？
- 可以服务于哪些不同的用户群体？
- 创新想法：
  1. 
  2. 

### E - 简化 (Eliminate)
- 可以去掉什么不必要的部分？
- 如何简化使其更高效？
- 创新想法：
  1. 
  2. 

### R - 重组 (Rearrange)
- 可以如何重新排列组件或步骤？
- 颠倒顺序会带来什么新价值？
- 创新想法：
  1. 
  2. 

## 跨领域灵感

### 自然界启发
- 自然界中有什么可以借鉴的解决方案？
- 创新想法：
  1. 
  2. 

### 其他行业启发
- 其他行业如何解决类似问题？
- 创新想法：
  1. 
  2. 

## 创新评估

对你的创新想法进行简单评估：

### 想法一：[创新名称]
- 新颖性 (1-10分)：
- 可行性 (1-10分)：
- 价值潜力 (1-10分)：
- 总体评分：

### 想法二：[创新名称]
- 新颖性 (1-10分)：
- 可行性 (1-10分)：
- 价值潜力 (1-10分)：
- 总体评分：

### 想法三：[创新名称]
- 新颖性 (1-10分)：
- 可行性 (1-10分)：
- 价值潜力 (1-10分)：
- 总体评分：

## 最佳创新方案

### 推荐方案：[创新名称]
- **描述**：
- **优势**：
- **实施步骤**：
  1. 
  2. 
  3. 

## JSON输出格式
```json
{{
  "innovation_subject": "创新主题",
  "innovation_direction": "创新方向",
  "constraints": "约束条件",
  "complexity_level": "low",
  "ideas": [
    {{
      "category": "替代",
      "idea": "创新想法描述",
      "novelty_score": 8,
      "feasibility_score": 7,
      "value_score": 9,
      "total_score": 8.0
    }},
    {{
      "category": "结合",
      "idea": "创新想法描述",
      "novelty_score": 9,
      "feasibility_score": 6,
      "value_score": 8,
      "total_score": 7.7
    }}
  ],
  "cross_domain_ideas": [
    {{
      "source": "自然界启发",
      "idea": "创新想法描述",
      "total_score": 7.5
    }},
    {{
      "source": "其他行业启发",
      "idea": "创新想法描述",
      "total_score": 8.0
    }}
  ],
  "best_innovation": {{
    "name": "最佳创新想法",
    "description": "详细描述",
    "advantages": ["优势1", "优势2", "优势3"],
    "total_score": 8.5,
    "implementation_steps": ["步骤1", "步骤2", "步骤3"]
  }}
}}
```

请开始创新思考："""
    return template
