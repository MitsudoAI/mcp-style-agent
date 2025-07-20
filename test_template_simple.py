#!/usr/bin/env python3

class TemplateManager:
    def __init__(self):
        self.cache = {
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

开始分解："""
        }
    
    def get_template(self, name, params=None):
        template = self.cache.get(name, "")
        if params:
            try:
                return template.format(**params)
            except:
                return template
        return template

if __name__ == "__main__":
    tm = TemplateManager()
    template = tm.get_template('decomposition', {
        'topic': '如何提高学习效率？',
        'complexity': 'moderate',
        'focus': '学生群体',
        'domain_context': '教育'
    })
    print("Template length:", len(template))
    print("Contains JSON格式:", 'JSON格式' in template)
    print("Contains Web搜索:", 'Web搜索' in template)