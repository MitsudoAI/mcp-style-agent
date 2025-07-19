"""
Template Manager for Deep Thinking Engine
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
import time
import threading
from datetime import datetime
from collections import defaultdict
import re

from ..config.exceptions import ConfigurationError


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
            "decomposition": "# 问题分解\n\n**主要问题**: {topic}\n**复杂度**: {complexity}\n**关注重点**: {focus}\n\n开始分解：",
            "evidence_collection": "# 证据收集\n\n**子问题**: {sub_question}\n**关键词**: {keywords}\n\n开始搜索：",
            "critical_evaluation": "# 批判性评估\n\n**评估内容**: {content}\n\n开始评估：",
            "session_recovery": "# 会话恢复\n\n请选择如何继续："
        }
        
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
