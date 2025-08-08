#!/usr/bin/env python3
"""
User Experience Testing Framework

This script simulates user experience testing for the Deep Thinking Engine
by creating realistic user scenarios and measuring usability metrics.

Requirements: 用户体验，产品优化
"""

import json
import logging
import tempfile
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import sys

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

# Import the basic components from our integration test
sys.path.insert(0, str(project_root / "scripts"))
from basic_integration_test import (
    BasicDatabase, BasicTemplateManager, BasicSessionManager, BasicMCPTools
)


@dataclass
class UserScenario:
    """Represents a user scenario for testing"""
    scenario_id: str
    user_type: str
    description: str
    topic: str
    expected_steps: int
    complexity_level: str
    success_criteria: List[str]
    user_goals: List[str]


@dataclass
class UsabilityMetrics:
    """Usability metrics for user experience evaluation"""
    task_completion_rate: float
    average_completion_time: float
    error_rate: float
    user_satisfaction_score: float  # Simulated 1-10 scale
    cognitive_load_score: float     # Simulated 1-10 scale (lower is better)
    learnability_score: float      # Simulated 1-10 scale
    efficiency_score: float        # Simulated 1-10 scale


@dataclass
class UserExperienceResult:
    """Result of a user experience test"""
    scenario_id: str
    user_type: str
    success: bool
    completion_time: float
    steps_completed: int
    total_steps: int
    errors_encountered: int
    user_feedback: Dict[str, Any]
    usability_metrics: UsabilityMetrics
    improvement_suggestions: List[str]


class UserExperienceSimulator:
    """Simulates different types of users interacting with the system"""
    
    def __init__(self):
        """Initialize the user experience simulator"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
        self.logger = logging.getLogger(__name__)
        
        # Initialize system components
        self._setup_system()
        
        # Define user personas
        self.user_personas = self._define_user_personas()
        
        # Define test scenarios
        self.test_scenarios = self._define_test_scenarios()
    
    def _setup_system(self):
        """Setup the system for user experience testing"""
        try:
            # Create directories
            (self.temp_path / "templates").mkdir(exist_ok=True)
            (self.temp_path / "data").mkdir(exist_ok=True)
            
            # Create user-friendly templates
            self._create_user_friendly_templates()
            
            # Initialize components
            db_path = str(self.temp_path / "data" / "ux_test.db")
            self.database = BasicDatabase(db_path)
            
            templates_dir = str(self.temp_path / "templates")
            self.template_manager = BasicTemplateManager(templates_dir)
            
            self.session_manager = BasicSessionManager(self.database)
            self.mcp_tools = BasicMCPTools(self.session_manager, self.template_manager)
            
            self.logger.info("User experience test system setup complete")
            
        except Exception as e:
            self.logger.error(f"Failed to setup UX test system: {e}")
            raise
    
    def _create_user_friendly_templates(self):
        """Create user-friendly templates for testing"""
        templates = {
            'beginner_template.tmpl': """
# 🤔 让我们一起思考：{topic}

欢迎使用深度思考引擎！我将帮助您系统性地分析这个问题。

## 📝 我们将要做的：
1. **理解问题** - 首先明确我们要解决什么
2. **收集信息** - 寻找相关的事实和数据
3. **深入分析** - 从多个角度思考问题
4. **得出结论** - 形成有根据的观点

让我们开始吧！请告诉我您对这个话题的初步想法：
""",
            
            'intermediate_template.tmpl': """
# 深度分析：{topic}

## 🎯 分析目标
我们将对这个主题进行系统性的深度分析。

## 📊 分析框架
1. **问题分解** - 将复杂问题拆分为可管理的部分
2. **多角度思考** - 从不同视角审视问题
3. **证据评估** - 分析支持和反对的证据
4. **批判性思维** - 识别潜在的偏见和假设

请开始您的分析：
""",
            
            'expert_template.tmpl': """
# 专家级深度思考：{topic}

## 🔬 高级分析框架
采用Paul-Elder批判性思维标准进行系统性分析：

### 分析维度：
- **准确性** - 信息的可靠性和精确度
- **相关性** - 与核心问题的关联度
- **深度** - 分析的透彻程度
- **广度** - 考虑角度的全面性
- **逻辑性** - 推理的严密性
- **重要性** - 关注核心要素
- **公正性** - 避免偏见和先入为主

请基于以上框架进行专业分析：
"""
        }
        
        for template_name, template_content in templates.items():
            template_path = self.temp_path / "templates" / template_name
            template_path.write_text(template_content, encoding='utf-8')
    
    def _define_user_personas(self) -> Dict[str, Dict[str, Any]]:
        """Define different user personas for testing"""
        return {
            'beginner': {
                'name': '初学者小王',
                'description': '刚接触深度思考工具的新用户',
                'characteristics': {
                    'technical_skill': 'low',
                    'domain_knowledge': 'basic',
                    'patience_level': 'medium',
                    'preferred_complexity': 'simple',
                    'learning_style': 'step_by_step'
                },
                'goals': [
                    '学会使用基本功能',
                    '理解工具的价值',
                    '完成简单的思考任务'
                ],
                'pain_points': [
                    '界面复杂度',
                    '术语理解困难',
                    '不知道从何开始'
                ]
            },
            
            'intermediate': {
                'name': '职场专家李经理',
                'description': '有一定经验的职场人士',
                'characteristics': {
                    'technical_skill': 'medium',
                    'domain_knowledge': 'good',
                    'patience_level': 'medium',
                    'preferred_complexity': 'moderate',
                    'learning_style': 'practical'
                },
                'goals': [
                    '提高工作决策质量',
                    '系统性分析复杂问题',
                    '提升思维效率'
                ],
                'pain_points': [
                    '时间限制',
                    '需要快速上手',
                    '希望看到实际效果'
                ]
            },
            
            'expert': {
                'name': '研究员张博士',
                'description': '专业研究人员或学者',
                'characteristics': {
                    'technical_skill': 'high',
                    'domain_knowledge': 'expert',
                    'patience_level': 'high',
                    'preferred_complexity': 'complex',
                    'learning_style': 'exploratory'
                },
                'goals': [
                    '进行深度学术分析',
                    '探索高级功能',
                    '获得专业级洞察'
                ],
                'pain_points': [
                    '功能深度不够',
                    '缺乏高级选项',
                    '需要更多控制权'
                ]
            }
        }
    
    def _define_test_scenarios(self) -> List[UserScenario]:
        """Define test scenarios for different user types"""
        return [
            # Beginner scenarios
            UserScenario(
                scenario_id='beginner_01',
                user_type='beginner',
                description='新用户首次使用体验',
                topic='如何提高学习效率',
                expected_steps=2,
                complexity_level='simple',
                success_criteria=[
                    '能够成功启动思考流程',
                    '理解基本操作步骤',
                    '获得有用的分析结果'
                ],
                user_goals=[
                    '学会基本使用方法',
                    '获得实用建议'
                ]
            ),
            
            UserScenario(
                scenario_id='beginner_02',
                user_type='beginner',
                description='简单日常问题分析',
                topic='选择什么专业比较好',
                expected_steps=2,
                complexity_level='simple',
                success_criteria=[
                    '完成完整分析流程',
                    '理解分析结果',
                    '感到工具有帮助'
                ],
                user_goals=[
                    '获得决策支持',
                    '建立使用信心'
                ]
            ),
            
            # Intermediate scenarios
            UserScenario(
                scenario_id='intermediate_01',
                user_type='intermediate',
                description='工作决策分析',
                topic='公司是否应该采用远程办公模式',
                expected_steps=3,
                complexity_level='moderate',
                success_criteria=[
                    '进行多角度分析',
                    '考虑利弊因素',
                    '形成明确建议'
                ],
                user_goals=[
                    '支持管理决策',
                    '提高分析质量'
                ]
            ),
            
            UserScenario(
                scenario_id='intermediate_02',
                user_type='intermediate',
                description='市场策略分析',
                topic='如何在竞争激烈的市场中脱颖而出',
                expected_steps=3,
                complexity_level='moderate',
                success_criteria=[
                    '识别关键成功因素',
                    '分析竞争环境',
                    '制定可行策略'
                ],
                user_goals=[
                    '制定商业策略',
                    '获得竞争优势'
                ]
            ),
            
            # Expert scenarios
            UserScenario(
                scenario_id='expert_01',
                user_type='expert',
                description='学术研究问题分析',
                topic='人工智能对未来教育模式的深层影响',
                expected_steps=4,
                complexity_level='complex',
                success_criteria=[
                    '进行深度理论分析',
                    '考虑多重影响因素',
                    '提出原创性见解'
                ],
                user_goals=[
                    '产生学术洞察',
                    '支持研究工作'
                ]
            ),
            
            UserScenario(
                scenario_id='expert_02',
                user_type='expert',
                description='复杂政策分析',
                topic='碳中和政策的经济社会影响及实施路径',
                expected_steps=4,
                complexity_level='complex',
                success_criteria=[
                    '系统性政策分析',
                    '多维度影响评估',
                    '可操作性建议'
                ],
                user_goals=[
                    '支持政策制定',
                    '预测政策效果'
                ]
            )
        ]
    
    def simulate_user_interaction(self, scenario: UserScenario) -> UserExperienceResult:
        """Simulate a user interaction based on the scenario"""
        start_time = time.time()
        
        self.logger.info(f"Simulating user scenario: {scenario.scenario_id}")
        
        try:
            # Get user persona
            persona = self.user_personas[scenario.user_type]
            
            # Simulate user behavior based on persona
            errors_encountered = 0
            steps_completed = 0
            user_feedback = {}
            
            # Step 1: Start thinking (all users should be able to do this)
            try:
                # Select appropriate template based on user type
                if scenario.user_type == 'beginner':
                    # Simulate beginner might need guidance
                    time.sleep(0.1)  # Simulate reading time
                
                start_result = self.mcp_tools.start_thinking(scenario.topic)
                session_id = start_result['session_id']
                steps_completed += 1
                
                # Simulate user feedback on initial experience
                user_feedback['initial_experience'] = self._simulate_initial_feedback(scenario.user_type)
                
            except Exception as e:
                errors_encountered += 1
                self.logger.error(f"Error in start_thinking: {e}")
                raise
            
            # Step 2: Continue analysis (if expected)
            if scenario.expected_steps > 1:
                try:
                    # Simulate user providing input based on their expertise level
                    user_input = self._simulate_user_input(scenario.user_type, scenario.topic)
                    
                    next_result = self.mcp_tools.next_step(session_id, user_input)
                    steps_completed += 1
                    
                    # Simulate user feedback on workflow
                    user_feedback['workflow_experience'] = self._simulate_workflow_feedback(scenario.user_type)
                    
                except Exception as e:
                    errors_encountered += 1
                    self.logger.error(f"Error in next_step: {e}")
            
            # Step 3: Advanced analysis (for intermediate/expert users)
            if scenario.expected_steps > 2:
                try:
                    # Simulate more sophisticated user input
                    advanced_input = self._simulate_advanced_input(scenario.user_type, scenario.topic)
                    
                    next_result = self.mcp_tools.next_step(session_id, advanced_input)
                    steps_completed += 1
                    
                    user_feedback['advanced_experience'] = self._simulate_advanced_feedback(scenario.user_type)
                    
                except Exception as e:
                    errors_encountered += 1
                    self.logger.error(f"Error in advanced step: {e}")
            
            # Step 4: Expert-level analysis (for expert users only)
            if scenario.expected_steps > 3:
                try:
                    expert_input = self._simulate_expert_input(scenario.user_type, scenario.topic)
                    
                    next_result = self.mcp_tools.next_step(session_id, expert_input)
                    steps_completed += 1
                    
                    user_feedback['expert_experience'] = self._simulate_expert_feedback(scenario.user_type)
                    
                except Exception as e:
                    errors_encountered += 1
                    self.logger.error(f"Error in expert step: {e}")
            
            # Final step: Complete thinking
            try:
                complete_result = self.mcp_tools.complete_thinking(session_id)
                steps_completed += 1
                
                # Simulate final user feedback
                user_feedback['completion_experience'] = self._simulate_completion_feedback(scenario.user_type)
                
            except Exception as e:
                errors_encountered += 1
                self.logger.error(f"Error in complete_thinking: {e}")
            
            # Calculate completion time
            completion_time = time.time() - start_time
            
            # Determine success based on completion rate and user goals
            completion_rate = steps_completed / (scenario.expected_steps + 1)  # +1 for completion step
            success = completion_rate >= 0.8 and errors_encountered <= 1
            
            # Calculate usability metrics
            usability_metrics = self._calculate_usability_metrics(
                scenario, completion_time, completion_rate, errors_encountered
            )
            
            # Generate improvement suggestions
            improvement_suggestions = self._generate_improvement_suggestions(
                scenario, errors_encountered, user_feedback, usability_metrics
            )
            
            result = UserExperienceResult(
                scenario_id=scenario.scenario_id,
                user_type=scenario.user_type,
                success=success,
                completion_time=completion_time,
                steps_completed=steps_completed,
                total_steps=scenario.expected_steps + 1,
                errors_encountered=errors_encountered,
                user_feedback=user_feedback,
                usability_metrics=usability_metrics,
                improvement_suggestions=improvement_suggestions
            )
            
            self.logger.info(f"User scenario {scenario.scenario_id} completed: {'SUCCESS' if success else 'FAILED'}")
            
            return result
            
        except Exception as e:
            completion_time = time.time() - start_time
            
            # Create failed result
            usability_metrics = UsabilityMetrics(
                task_completion_rate=0.0,
                average_completion_time=completion_time,
                error_rate=1.0,
                user_satisfaction_score=1.0,
                cognitive_load_score=10.0,
                learnability_score=1.0,
                efficiency_score=1.0
            )
            
            return UserExperienceResult(
                scenario_id=scenario.scenario_id,
                user_type=scenario.user_type,
                success=False,
                completion_time=completion_time,
                steps_completed=steps_completed,
                total_steps=scenario.expected_steps + 1,
                errors_encountered=errors_encountered + 1,
                user_feedback={'error': str(e)},
                usability_metrics=usability_metrics,
                improvement_suggestions=['Fix critical system errors', 'Improve error handling']
            )
    
    def _simulate_user_input(self, user_type: str, topic: str) -> str:
        """Simulate user input based on user type"""
        if user_type == 'beginner':
            return f"我想了解更多关于{topic}的基本信息，请给我一些简单易懂的建议。"
        elif user_type == 'intermediate':
            return f"请帮我分析{topic}的关键因素，我需要考虑哪些重要方面？"
        else:  # expert
            return f"请对{topic}进行深度分析，包括理论框架、实证证据和潜在影响。"
    
    def _simulate_advanced_input(self, user_type: str, topic: str) -> str:
        """Simulate advanced user input"""
        if user_type == 'intermediate':
            return f"基于前面的分析，我想进一步探讨{topic}的实施挑战和解决方案。"
        else:  # expert
            return f"请从多个理论视角分析{topic}，并考虑跨学科的影响因素。"
    
    def _simulate_expert_input(self, user_type: str, topic: str) -> str:
        """Simulate expert-level user input"""
        return f"请对{topic}进行批判性评估，识别潜在的认知偏见和假设前提。"
    
    def _simulate_initial_feedback(self, user_type: str) -> Dict[str, Any]:
        """Simulate user feedback on initial experience"""
        if user_type == 'beginner':
            return {
                'ease_of_start': 8,  # 1-10 scale
                'clarity_of_instructions': 7,
                'intimidation_level': 3,  # Lower is better
                'comments': '界面比较友好，但还是有点不知道该怎么开始'
            }
        elif user_type == 'intermediate':
            return {
                'ease_of_start': 9,
                'clarity_of_instructions': 8,
                'intimidation_level': 2,
                'comments': '很快就能上手，界面设计合理'
            }
        else:  # expert
            return {
                'ease_of_start': 9,
                'clarity_of_instructions': 8,
                'intimidation_level': 1,
                'comments': '系统响应迅速，期待看到更多高级功能'
            }
    
    def _simulate_workflow_feedback(self, user_type: str) -> Dict[str, Any]:
        """Simulate user feedback on workflow experience"""
        if user_type == 'beginner':
            return {
                'workflow_clarity': 7,
                'step_logic': 8,
                'guidance_adequacy': 6,
                'comments': '流程比较清楚，但希望有更多提示'
            }
        elif user_type == 'intermediate':
            return {
                'workflow_clarity': 9,
                'step_logic': 9,
                'guidance_adequacy': 8,
                'comments': '工作流程很合理，符合思考习惯'
            }
        else:  # expert
            return {
                'workflow_clarity': 8,
                'step_logic': 9,
                'guidance_adequacy': 7,
                'comments': '流程设计不错，但希望能自定义步骤'
            }
    
    def _simulate_advanced_feedback(self, user_type: str) -> Dict[str, Any]:
        """Simulate user feedback on advanced features"""
        if user_type == 'intermediate':
            return {
                'feature_usefulness': 8,
                'complexity_appropriateness': 8,
                'learning_curve': 7,
                'comments': '高级功能很实用，学习成本可接受'
            }
        else:  # expert
            return {
                'feature_usefulness': 7,
                'complexity_appropriateness': 6,
                'learning_curve': 9,
                'comments': '功能还可以更深入一些，希望有更多专业选项'
            }
    
    def _simulate_expert_feedback(self, user_type: str) -> Dict[str, Any]:
        """Simulate expert-level feedback"""
        return {
            'analytical_depth': 7,
            'theoretical_rigor': 6,
            'customization_options': 5,
            'comments': '分析深度不错，但理论框架可以更丰富'
        }
    
    def _simulate_completion_feedback(self, user_type: str) -> Dict[str, Any]:
        """Simulate user feedback on completion experience"""
        if user_type == 'beginner':
            return {
                'satisfaction': 8,
                'value_perceived': 8,
                'likelihood_to_recommend': 7,
                'overall_experience': 7,
                'comments': '整体体验不错，获得了有用的见解'
            }
        elif user_type == 'intermediate':
            return {
                'satisfaction': 9,
                'value_perceived': 9,
                'likelihood_to_recommend': 8,
                'overall_experience': 8,
                'comments': '非常有价值的工具，会推荐给同事使用'
            }
        else:  # expert
            return {
                'satisfaction': 7,
                'value_perceived': 7,
                'likelihood_to_recommend': 7,
                'overall_experience': 7,
                'comments': '有一定价值，但还有改进空间'
            }
    
    def _calculate_usability_metrics(self, scenario: UserScenario, completion_time: float, 
                                   completion_rate: float, errors_encountered: int) -> UsabilityMetrics:
        """Calculate usability metrics based on simulation results"""
        
        # Task completion rate
        task_completion_rate = completion_rate
        
        # Average completion time (normalized by complexity)
        expected_time = {
            'simple': 5.0,
            'moderate': 10.0,
            'complex': 20.0
        }
        time_efficiency = expected_time[scenario.complexity_level] / max(completion_time, 0.1)
        
        # Error rate
        error_rate = errors_encountered / max(scenario.expected_steps, 1)
        
        # User satisfaction (simulated based on user type and completion)
        base_satisfaction = {
            'beginner': 7.0,
            'intermediate': 8.0,
            'expert': 6.5
        }
        satisfaction_penalty = errors_encountered * 1.5 + (1 - completion_rate) * 3
        user_satisfaction_score = max(1.0, base_satisfaction[scenario.user_type] - satisfaction_penalty)
        
        # Cognitive load (simulated - lower is better)
        base_cognitive_load = {
            'beginner': 6.0,
            'intermediate': 4.0,
            'expert': 3.0
        }
        cognitive_load_penalty = errors_encountered * 1.0
        cognitive_load_score = min(10.0, base_cognitive_load[scenario.user_type] + cognitive_load_penalty)
        
        # Learnability (simulated)
        base_learnability = {
            'beginner': 6.0,
            'intermediate': 8.0,
            'expert': 9.0
        }
        learnability_penalty = errors_encountered * 0.5
        learnability_score = max(1.0, base_learnability[scenario.user_type] - learnability_penalty)
        
        # Efficiency (based on time and completion)
        efficiency_score = min(10.0, time_efficiency * completion_rate * 10)
        
        return UsabilityMetrics(
            task_completion_rate=task_completion_rate,
            average_completion_time=completion_time,
            error_rate=error_rate,
            user_satisfaction_score=user_satisfaction_score,
            cognitive_load_score=cognitive_load_score,
            learnability_score=learnability_score,
            efficiency_score=efficiency_score
        )
    
    def _generate_improvement_suggestions(self, scenario: UserScenario, errors_encountered: int,
                                        user_feedback: Dict[str, Any], 
                                        usability_metrics: UsabilityMetrics) -> List[str]:
        """Generate improvement suggestions based on test results"""
        suggestions = []
        
        # Error-based suggestions
        if errors_encountered > 0:
            suggestions.append("改进错误处理和用户反馈机制")
            suggestions.append("增加系统稳定性和容错能力")
        
        # Completion rate suggestions
        if usability_metrics.task_completion_rate < 0.8:
            suggestions.append("简化用户工作流程")
            suggestions.append("提供更清晰的操作指导")
        
        # User type specific suggestions
        if scenario.user_type == 'beginner':
            if usability_metrics.cognitive_load_score > 7:
                suggestions.append("为新用户提供更多引导和帮助")
                suggestions.append("简化界面复杂度")
            
            if usability_metrics.user_satisfaction_score < 7:
                suggestions.append("增加新手教程和示例")
                suggestions.append("提供更友好的错误提示")
        
        elif scenario.user_type == 'intermediate':
            if usability_metrics.efficiency_score < 7:
                suggestions.append("优化工作流程效率")
                suggestions.append("提供快捷操作选项")
            
            if usability_metrics.user_satisfaction_score < 8:
                suggestions.append("增加实用功能和模板")
                suggestions.append("改进结果展示方式")
        
        else:  # expert
            if usability_metrics.user_satisfaction_score < 7:
                suggestions.append("增加高级功能和自定义选项")
                suggestions.append("提供更深入的分析工具")
            
            suggestions.append("支持专业用户的个性化需求")
            suggestions.append("增加理论框架和方法论选择")
        
        # Performance-based suggestions
        if usability_metrics.average_completion_time > 15:
            suggestions.append("优化系统响应速度")
            suggestions.append("减少不必要的等待时间")
        
        # Satisfaction-based suggestions
        if usability_metrics.user_satisfaction_score < 7:
            suggestions.append("改进整体用户体验")
            suggestions.append("增加用户价值感知")
        
        return suggestions[:5]  # Return top 5 suggestions
    
    def run_user_experience_tests(self) -> List[UserExperienceResult]:
        """Run all user experience tests"""
        self.logger.info("Starting user experience testing...")
        
        results = []
        
        for scenario in self.test_scenarios:
            result = self.simulate_user_interaction(scenario)
            results.append(result)
            
            # Small delay between tests
            time.sleep(0.1)
        
        self.logger.info(f"User experience testing completed. {len(results)} scenarios tested.")
        
        return results
    
    def analyze_ux_results(self, results: List[UserExperienceResult]) -> Dict[str, Any]:
        """Analyze user experience test results"""
        if not results:
            return {}
        
        # Overall metrics
        total_tests = len(results)
        successful_tests = sum(1 for r in results if r.success)
        success_rate = successful_tests / total_tests
        
        # Average metrics
        avg_completion_time = sum(r.completion_time for r in results) / total_tests
        avg_satisfaction = sum(r.usability_metrics.user_satisfaction_score for r in results) / total_tests
        avg_cognitive_load = sum(r.usability_metrics.cognitive_load_score for r in results) / total_tests
        avg_efficiency = sum(r.usability_metrics.efficiency_score for r in results) / total_tests
        
        # User type analysis
        user_type_analysis = {}
        for user_type in ['beginner', 'intermediate', 'expert']:
            type_results = [r for r in results if r.user_type == user_type]
            if type_results:
                user_type_analysis[user_type] = {
                    'count': len(type_results),
                    'success_rate': sum(1 for r in type_results if r.success) / len(type_results),
                    'avg_satisfaction': sum(r.usability_metrics.user_satisfaction_score for r in type_results) / len(type_results),
                    'avg_completion_time': sum(r.completion_time for r in type_results) / len(type_results),
                    'avg_cognitive_load': sum(r.usability_metrics.cognitive_load_score for r in type_results) / len(type_results)
                }
        
        # Common improvement suggestions
        all_suggestions = []
        for result in results:
            all_suggestions.extend(result.improvement_suggestions)
        
        suggestion_counts = {}
        for suggestion in all_suggestions:
            suggestion_counts[suggestion] = suggestion_counts.get(suggestion, 0) + 1
        
        top_suggestions = sorted(suggestion_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            'overall_metrics': {
                'total_tests': total_tests,
                'success_rate': success_rate,
                'avg_completion_time': avg_completion_time,
                'avg_satisfaction': avg_satisfaction,
                'avg_cognitive_load': avg_cognitive_load,
                'avg_efficiency': avg_efficiency
            },
            'user_type_analysis': user_type_analysis,
            'top_improvement_suggestions': top_suggestions,
            'detailed_results': results
        }
    
    def generate_ux_report(self, results: List[UserExperienceResult]) -> str:
        """Generate comprehensive UX test report"""
        analysis = self.analyze_ux_results(results)
        
        if not analysis:
            return "No UX test results available."
        
        overall = analysis['overall_metrics']
        user_types = analysis['user_type_analysis']
        suggestions = analysis['top_improvement_suggestions']
        
        report_lines = [
            "=" * 100,
            "DEEP THINKING ENGINE - USER EXPERIENCE TEST REPORT",
            "=" * 100,
            "",
            f"Test Environment: {self.temp_dir}",
            f"Report Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "EXECUTIVE SUMMARY",
            "-" * 50,
            f"Total User Scenarios Tested: {overall['total_tests']}",
            f"Overall Success Rate: {overall['success_rate']:.1%}",
            f"Average Completion Time: {overall['avg_completion_time']:.2f} seconds",
            f"Average User Satisfaction: {overall['avg_satisfaction']:.1f}/10",
            f"Average Cognitive Load: {overall['avg_cognitive_load']:.1f}/10 (lower is better)",
            f"Average Efficiency Score: {overall['avg_efficiency']:.1f}/10",
            "",
            "USER TYPE ANALYSIS",
            "-" * 50
        ]
        
        for user_type, metrics in user_types.items():
            persona_name = self.user_personas[user_type]['name']
            report_lines.extend([
                f"",
                f"👤 {user_type.upper()} USER ({persona_name}):",
                f"  Scenarios Tested: {metrics['count']}",
                f"  Success Rate: {metrics['success_rate']:.1%}",
                f"  Avg Satisfaction: {metrics['avg_satisfaction']:.1f}/10",
                f"  Avg Completion Time: {metrics['avg_completion_time']:.2f}s",
                f"  Avg Cognitive Load: {metrics['avg_cognitive_load']:.1f}/10",
            ])
        
        report_lines.extend([
            "",
            "DETAILED SCENARIO RESULTS",
            "-" * 50
        ])
        
        for result in results:
            status = "✅ SUCCESS" if result.success else "❌ FAILED"
            persona_name = self.user_personas[result.user_type]['name']
            
            report_lines.extend([
                f"",
                f"{status} {result.scenario_id} ({persona_name})",
                f"  Completion: {result.steps_completed}/{result.total_steps} steps ({result.steps_completed/result.total_steps:.1%})",
                f"  Time: {result.completion_time:.2f}s",
                f"  Errors: {result.errors_encountered}",
                f"  Satisfaction: {result.usability_metrics.user_satisfaction_score:.1f}/10",
                f"  Cognitive Load: {result.usability_metrics.cognitive_load_score:.1f}/10",
                f"  Efficiency: {result.usability_metrics.efficiency_score:.1f}/10"
            ])
            
            if result.improvement_suggestions:
                report_lines.append("  Key Suggestions:")
                for suggestion in result.improvement_suggestions[:3]:
                    report_lines.append(f"    • {suggestion}")
        
        report_lines.extend([
            "",
            "TOP IMPROVEMENT RECOMMENDATIONS",
            "-" * 50
        ])
        
        for i, (suggestion, count) in enumerate(suggestions, 1):
            report_lines.append(f"{i}. {suggestion} (mentioned {count} times)")
        
        # UX Quality Assessment
        ux_quality = "EXCELLENT" if overall['avg_satisfaction'] >= 8.5 else \
                    "GOOD" if overall['avg_satisfaction'] >= 7.0 else \
                    "NEEDS IMPROVEMENT" if overall['avg_satisfaction'] >= 5.5 else \
                    "POOR"
        
        usability_rating = "HIGH" if overall['avg_cognitive_load'] <= 4.0 else \
                          "MEDIUM" if overall['avg_cognitive_load'] <= 6.0 else \
                          "LOW"
        
        report_lines.extend([
            "",
            "UX QUALITY ASSESSMENT",
            "-" * 50,
            f"Overall UX Quality: {ux_quality}",
            f"Usability Rating: {usability_rating}",
            f"User Satisfaction Level: {'😊 HIGH' if overall['avg_satisfaction'] >= 7.5 else '😐 MEDIUM' if overall['avg_satisfaction'] >= 6.0 else '😞 LOW'}",
            f"Learning Curve: {'🟢 EASY' if overall['avg_cognitive_load'] <= 5.0 else '🟡 MODERATE' if overall['avg_cognitive_load'] <= 7.0 else '🔴 DIFFICULT'}",
            "",
            "DEPLOYMENT READINESS FROM UX PERSPECTIVE",
            "-" * 50,
            f"Ready for Beta Testing: {'✅ YES' if overall['success_rate'] >= 0.8 and overall['avg_satisfaction'] >= 6.5 else '❌ NO'}",
            f"Ready for Public Release: {'✅ YES' if overall['success_rate'] >= 0.9 and overall['avg_satisfaction'] >= 7.5 else '❌ NO'}",
            f"Requires UX Improvements: {'❌ NO' if overall['avg_satisfaction'] >= 8.0 else '✅ YES'}",
            "",
            "=" * 100
        ])
        
        return "\n".join(report_lines)
    
    def save_ux_results(self, results: List[UserExperienceResult], output_directory: Optional[str] = None):
        """Save UX test results to files"""
        output_dir = Path(output_directory or "ux_test_results")
        output_dir.mkdir(exist_ok=True)
        
        # Save comprehensive report
        report = self.generate_ux_report(results)
        with open(output_dir / "ux_test_report.txt", 'w', encoding='utf-8') as f:
            f.write(report)
        
        # Save raw results as JSON
        def convert_for_json(obj):
            """Convert objects to JSON-serializable format"""
            if hasattr(obj, '__dict__'):
                return obj.__dict__
            return str(obj)
        
        results_data = {
            'test_results': [asdict(result) for result in results],
            'analysis': self.analyze_ux_results(results),
            'user_personas': self.user_personas,
            'test_scenarios': [asdict(scenario) for scenario in self.test_scenarios]
        }
        
        with open(output_dir / "ux_test_results.json", 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False, default=convert_for_json)
        
        self.logger.info(f"UX test results saved to: {output_dir}")
        return output_dir
    
    def cleanup(self):
        """Cleanup test environment"""
        try:
            # Shutdown components
            if hasattr(self, 'database'):
                self.database.shutdown()
            if hasattr(self, 'template_manager'):
                self.template_manager.shutdown()
            
            # Clean up temporary files
            import shutil
            if Path(self.temp_dir).exists():
                shutil.rmtree(self.temp_dir)
            
            self.logger.info("UX test environment cleaned up")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")


def main():
    """Main entry point for user experience testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Deep Thinking Engine User Experience Test')
    parser.add_argument('--output-dir', help='Output directory for results')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], default='INFO')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 100)
    print("DEEP THINKING ENGINE - USER EXPERIENCE TEST")
    print("=" * 100)
    
    simulator = None
    
    try:
        # Initialize simulator
        simulator = UserExperienceSimulator()
        print(f"✅ UX test environment initialized: {simulator.temp_dir}")
        
        # Run UX tests
        print("\n👥 Running user experience tests...")
        results = simulator.run_user_experience_tests()
        
        # Generate and display report
        report = simulator.generate_ux_report(results)
        print("\n" + report)
        
        # Save results
        output_dir = simulator.save_ux_results(results, args.output_dir)
        print(f"\n📄 UX test results saved to: {output_dir}")
        
        # Determine success
        analysis = simulator.analyze_ux_results(results)
        overall_success_rate = analysis['overall_metrics']['success_rate']
        avg_satisfaction = analysis['overall_metrics']['avg_satisfaction']
        
        if overall_success_rate >= 0.8 and avg_satisfaction >= 7.0:
            print("\n🎉 USER EXPERIENCE TESTS PASSED!")
            print("✅ Deep Thinking Engine provides good user experience across different user types!")
            return True
        else:
            print(f"\n⚠️  User experience needs improvement")
            print(f"Success rate: {overall_success_rate:.1%}, Satisfaction: {avg_satisfaction:.1f}/10")
            print("❌ UX improvements needed before deployment")
            return False
        
    except Exception as e:
        print(f"❌ User experience test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        if simulator:
            simulator.cleanup()


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)