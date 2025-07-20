#!/usr/bin/env python3

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from mcps.deep_thinking.templates.template_manager import TemplateManager

# Test template manager
print("Testing template manager...")
tm = TemplateManager()

print("Available templates:", tm.list_templates())
print("Template manager file:", tm.__class__.__module__)

# Check the actual template content in cache
print("Decomposition template in cache:")
print(repr(tm.cache.get('decomposition', 'NOT FOUND')[:100]))

# Test decomposition template
print("\nTesting decomposition template...")
try:
    template = tm.get_template('decomposition', {
        'topic': '如何提高学习效率？',
        'complexity': 'moderate',
        'focus': '学生群体',
        'domain_context': '教育'
    })
    print("Template length:", len(template))
    print("Template content preview:", template[:200] + "..." if len(template) > 200 else template)
    
    # Check for expected strings
    checks = [
        ('如何提高学习效率？' in template, '如何提高学习效率？'),
        ('moderate' in template, 'moderate'),
        ('学生群体' in template, '学生群体'),
        ('JSON格式' in template, 'JSON格式')
    ]
    
    for check, text in checks:
        print(f"Contains '{text}': {check}")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

# Test evidence template
print("\nTesting evidence template...")
try:
    template = tm.get_template('evidence_collection', {
        'sub_question': '什么是有效的学习方法？',
        'keywords': ['学习方法', '效率', '记忆'],
        'context': '学生学习'
    })
    print("Template length:", len(template))
    print("Template content preview:", template[:200] + "..." if len(template) > 200 else template)
    
    # Check for expected strings
    checks = [
        ('什么是有效的学习方法？' in template, '什么是有效的学习方法？'),
        ('Web搜索' in template, 'Web搜索'),
        ('证据收集' in template, '证据收集')
    ]
    
    for check, text in checks:
        print(f"Contains '{text}': {check}")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()