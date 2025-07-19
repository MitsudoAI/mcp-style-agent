# Requirements Document

## Introduction

本项目旨在开发一个基于MCP(Model Context Protocol)架构的本地深度思考引擎，专注于突破认知局限和系统性对抗思维偏见。该系统将最新LLM自带的Web Search能力与经过验证的思维科学方法相结合，通过多Agent辩论、批判性思维评估、苏格拉底式提问等方法，最大化挖掘LLM的推理潜力。

系统采用"LLM负责生成-推理，MCP负责编排-监督"的分工原则，将Paul-Elder批判性思维标准、苏格拉底提问法、六顶思考帽、TRIZ/SCAMPER等策略写成角色Prompt，通过多轮回合强制LLM自我挑战，全过程引用外部Web证据防止幻觉，形成可追溯的"思维足迹"。

## Requirements

### Requirement 1

**User Story:** 作为一个思考者，我希望系统能够将复杂问题分解为多个子问题并制定检索策略，以便进行系统性的深度分析。

#### Acceptance Criteria

1. WHEN 用户输入复杂议题 THEN 系统 SHALL 使用问题分解者角色拆分为3-5个子问题
2. WHEN 生成子问题 THEN 系统 SHALL 为每个子问题设定检索关键词和优先级
3. WHEN 分解完成 THEN 系统 SHALL 标注不同视角和潜在争议点
4. IF 问题过于宽泛 THEN 系统 SHALL 要求用户进一步明确范围和焦点

### Requirement 2

**User Story:** 作为一个研究者，我希望系统能够利用LLM内置的Web搜索功能获取多源证据，确保信息的权威性和多样性。

#### Acceptance Criteria

1. WHEN 执行证据搜索 THEN 系统 SHALL 针对每个子问题检索至少5条独立来源
2. WHEN 获取搜索结果 THEN 系统 SHALL 要求来源领域多样化(学术、媒体、政府等)
3. WHEN 处理搜索结果 THEN 系统 SHALL 提取摘要并保留URL引用链接
4. WHEN 发现信息冲突 THEN 系统 SHALL 标记争议并触发深度挖掘流程

### Requirement 3

**User Story:** 作为一个辩论参与者，我希望系统能够组织多Agent辩论，从不同立场和角度分析问题，避免单一视角的局限。

#### Acceptance Criteria

1. WHEN 开始辩论环节 THEN 系统 SHALL 创建3-5个不同立场的辩手Agent
2. WHEN 进行辩论回合 THEN 每个辩手 SHALL 用200字阐述观点并质疑前一轮要害
3. WHEN 辩论进行中 THEN 系统 SHALL 限制最多3轮以避免过度发散
4. WHEN 辩论结束 THEN 系统 SHALL 总结各方核心论点和分歧点

### Requirement 4

**User Story:** 作为一个批判性思维实践者，我希望系统能够使用Paul-Elder九大标准评估论证质量，识别逻辑谬误和思维偏见。

#### Acceptance Criteria

1. WHEN 评估论证 THEN 系统 SHALL 使用Paul-Elder九大标准逐项评分
2. WHEN 输出评估结果 THEN 系统 SHALL 提供JSON格式的详细评分(clarity, accuracy, depth, breadth, logic等)
3. WHEN 发现逻辑问题 THEN 系统 SHALL 标注具体的谬误类型和改进建议
4. WHEN 任一维度评分低于0.8 THEN 系统 SHALL 要求回到证据搜索或重新辩论

### Requirement 5

**User Story:** 作为一个反偏见实践者，我希望系统能够检测和标注认知偏误，并提供对策建议来提高思考质量。

#### Acceptance Criteria

1. WHEN 分析思维过程 THEN 系统 SHALL 检测确认偏误、锚定效应等常见认知偏误
2. WHEN 发现偏误 THEN 系统 SHALL 引用具体句子并命名偏误类型
3. WHEN 标注偏误 THEN 系统 SHALL 提供具体的对策和改进建议
4. WHEN 偏误严重 THEN 系统 SHALL 建议重新搜索反例或对立观点

### Requirement 6

**User Story:** 作为一个创新思考者，我希望系统能够使用SCAMPER和TRIZ方法激发突破性思维，产生创新解决方案。

#### Acceptance Criteria

1. WHEN 基础分析完成 THEN 系统 SHALL 应用SCAMPER七问技法生成创新思路
2. WHEN 使用TRIZ方法 THEN 系统 SHALL 从40个创新原理中匹配适用的原理
3. WHEN 生成创新想法 THEN 系统 SHALL 评估新颖性和可行性并提供3种改进方案
4. WHEN 创新方案确定 THEN 系统 SHALL 提供具体的实施建议和潜在风险

### Requirement 7

**User Story:** 作为一个元认知实践者，我希望系统能够引导我进行苏格拉底式反思，提升自我认知和思维监控能力。

#### Acceptance Criteria

1. WHEN 完成思考过程 THEN 系统 SHALL 使用苏格拉底式提问引导用户反思
2. WHEN 进行反思提问 THEN 系统 SHALL 询问"最令人惊讶之处"和"未考虑的证据"
3. WHEN 用户回答反思问题 THEN 系统 SHALL 要求用户写100字自我反思总结
4. WHEN 反思完成 THEN 系统 SHALL 评估元认知监控质量并提供改进建议

### Requirement 8

**User Story:** 作为一个论证分析者，我希望系统能够生成可视化的论证映射图，降低认知负荷并清晰展示逻辑关系。

#### Acceptance Criteria

1. WHEN 论证分析完成 THEN 系统 SHALL 生成论证树状结构图
2. WHEN 显示论证图 THEN 系统 SHALL 标明前提、结论、支持和反驳关系
3. WHEN 生成可视化 THEN 系统 SHALL 使用Mermaid或ASCII艺术格式
4. WHEN 论证复杂 THEN 系统 SHALL 提供分层展示和交互式探索功能

### Requirement 9

**User Story:** 作为一个质量控制者，我希望系统能够检测论证中的矛盾和不一致，确保思考过程的逻辑严密性。

#### Acceptance Criteria

1. WHEN 处理多个信息源 THEN 系统 SHALL 自动检测相互矛盾的陈述
2. WHEN 发现矛盾 THEN 系统 SHALL 标记冲突点并要求进一步澄清
3. WHEN 矛盾无法解决 THEN 系统 SHALL 保留争议标记并在结论中说明
4. WHEN 检测一致性 THEN 系统 SHALL 验证前提与结论的逻辑连贯性

### Requirement 10

**User Story:** 作为一个学习者，我希望系统能够记录完整的思维过程和评分历史，支持复盘和持续改进。

#### Acceptance Criteria

1. WHEN 执行思考流程 THEN 系统 SHALL 在SQLite数据库中记录每轮思路与评价
2. WHEN 保存记录 THEN 系统 SHALL 存储JSON格式的{role, utterance, score, citation[]}
3. WHEN 用户查询历史 THEN 系统 SHALL 提供思维足迹的可视化展示
4. WHEN 进行复盘 THEN 系统 SHALL 支持思维模式分析和改进建议

### Requirement 11

**User Story:** 作为一个效率追求者，我希望系统能够支持稀疏通信和自适应Agent规模，在保证质量的同时优化计算成本。

#### Acceptance Criteria

1. WHEN 启动多Agent辩论 THEN 系统 SHALL 根据问题复杂度自适应调整Agent数量(3-5个)
2. WHEN 进行Agent通信 THEN 系统 SHALL 使用稀疏通信拓扑减少无效交互
3. WHEN 检测到重复论点 THEN 系统 SHALL 自动终止冗余讨论
4. WHEN 计算资源紧张 THEN 系统 SHALL 动态调整温度参数和模型选择

### Requirement 12

**User Story:** 作为一个安全意识用户，我希望系统能够在本地运行核心功能，仅在必要时进行网络搜索，保护思维隐私。

#### Acceptance Criteria

1. WHEN 处理用户思考内容 THEN 系统 SHALL 在本地进行所有推理和评估
2. WHEN 需要外部信息 THEN 系统 SHALL 仅发送必要的搜索关键词，不传输完整思考内容
3. WHEN 存储思维记录 THEN 系统 SHALL 使用本地SQLite数据库加密存储
4. WHEN 用户要求 THEN 系统 SHALL 支持完全离线模式运行(使用缓存数据)

### Requirement 13

**User Story:** 作为一个系统管理员，我希望系统具有可插拔的架构，支持自定义思维策略和评估标准。

#### Acceptance Criteria

1. WHEN 系统启动 THEN 系统 SHALL 能够从YAML配置文件动态加载思维流程定义
2. WHEN 添加新的思维方法 THEN 系统 SHALL 支持热插拔新的Agent角色和评估器
3. WHEN 自定义评估标准 THEN 系统 SHALL 允许用户定义个性化的批判性思维标准
4. WHEN 流程出错 THEN 系统 SHALL 提供错误恢复和流程回滚机制

### Requirement 14

**User Story:** 作为一个研究者，我希望系统能够支持多种输出格式，便于后续分析和分享。

#### Acceptance Criteria

1. WHEN 完成深度思考 THEN 系统 SHALL 支持输出结构化报告(Markdown/PDF格式)
2. WHEN 生成报告 THEN 系统 SHALL 包含思维流程图、证据引用、评分详情
3. WHEN 导出数据 THEN 系统 SHALL 支持JSON/CSV格式的原始数据导出
4. WHEN 分享结果 THEN 系统 SHALL 提供去敏感化的公开版本选项