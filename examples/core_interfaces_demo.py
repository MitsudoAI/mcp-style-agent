#!/usr/bin/env python3
"""
Demonstration of the Deep Thinking Engine core interfaces and data models
"""

import asyncio
from datetime import datetime
from mcps.deep_thinking.models.agent_models import (
    AgentInput, AgentOutput, AgentConfig, AgentMetadata, 
    AgentType, AgentStatus, AgentExecutionContext
)
from mcps.deep_thinking.models.thinking_models import (
    ThinkingSession, QuestionDecomposition, SubQuestion, 
    ComplexityLevel, Priority
)
from mcps.deep_thinking.agents.base_agent import BaseAgent, AgentFactory
from mcps.deep_thinking.config.config_manager import ConfigManager


class DemoAgent(BaseAgent):
    """Demo agent for demonstration purposes"""
    
    def get_metadata(self) -> AgentMetadata:
        return AgentMetadata(
            agent_type=AgentType.DECOMPOSER,
            name="Demo Decomposer Agent",
            description="A demonstration agent that breaks down questions",
            version="1.0.0",
            required_inputs=["question"],
            optional_inputs=["context", "complexity_hint"],
            output_schema={
                "type": "object",
                "properties": {
                    "decomposition": {"type": "object"},
                    "sub_questions": {"type": "array"}
                }
            },
            capabilities=["question_analysis", "complexity_assessment", "decomposition"],
            limitations=["requires_clear_questions", "limited_domain_knowledge"]
        )
    
    def get_default_config(self) -> AgentConfig:
        return AgentConfig(
            agent_type=AgentType.DECOMPOSER,
            enabled=True,
            max_retries=3,
            timeout_seconds=60,
            temperature=0.7,
            quality_threshold=0.8,
            specific_config={
                "max_sub_questions": 5,
                "min_complexity_score": 0.3
            }
        )
    
    async def _execute_internal(
        self, 
        input_data: AgentInput, 
        context: AgentExecutionContext,
        interaction_id: str
    ) -> AgentOutput:
        """Demo implementation of question decomposition"""
        
        question = input_data.data.get("question", "")
        
        # Simulate processing time
        await asyncio.sleep(0.1)
        
        # Create demo decomposition
        sub_questions = [
            SubQuestion(
                id="sub_1",
                question=f"What are the key components of: {question}?",
                priority=Priority.HIGH,
                search_keywords=["components", "elements", "parts"],
                expected_perspectives=["technical", "practical"],
                estimated_complexity=ComplexityLevel.MODERATE
            ),
            SubQuestion(
                id="sub_2", 
                question=f"What are the implications of: {question}?",
                priority=Priority.MEDIUM,
                search_keywords=["implications", "consequences", "effects"],
                expected_perspectives=["short-term", "long-term"],
                estimated_complexity=ComplexityLevel.COMPLEX
            )
        ]
        
        decomposition = QuestionDecomposition(
            main_question=question,
            complexity_assessment=ComplexityLevel.MODERATE,
            sub_questions=sub_questions,
            decomposition_strategy="component_and_implication_analysis",
            total_estimated_time=10,
            recommended_approach="parallel_analysis"
        )
        
        return AgentOutput(
            agent_type=self.agent_type,
            session_id=input_data.session_id,
            interaction_id=interaction_id,
            status=AgentStatus.COMPLETED,
            data={
                "decomposition": decomposition.model_dump(),
                "sub_questions": [sq.model_dump() for sq in sub_questions],
                "analysis_summary": f"Successfully decomposed question into {len(sub_questions)} sub-questions"
            },
            quality_score=0.85,
            metadata={
                "processing_time": 0.1,
                "complexity_detected": "moderate",
                "confidence": 0.9
            }
        )


async def demonstrate_core_interfaces():
    """Demonstrate the core interfaces and data models"""
    
    print("🧠 Deep Thinking Engine - Core Interfaces Demo")
    print("=" * 50)
    
    # 1. Create and configure a demo agent
    print("\n1. Creating and configuring demo agent...")
    
    # Register the demo agent
    AgentFactory.register_agent(AgentType.DECOMPOSER, DemoAgent)
    
    # Create agent instance
    agent = AgentFactory.create_agent(AgentType.DECOMPOSER)
    
    # Display agent metadata
    metadata = agent.get_metadata()
    print(f"   Agent: {metadata.name}")
    print(f"   Description: {metadata.description}")
    print(f"   Capabilities: {', '.join(metadata.capabilities)}")
    print(f"   Version: {metadata.version}")
    
    # 2. Create a thinking session
    print("\n2. Creating thinking session...")
    
    session = ThinkingSession(
        id="demo_session_001",
        topic="How can AI improve education?",
        user_id="demo_user",
        session_type="comprehensive_analysis"
    )
    
    print(f"   Session ID: {session.id}")
    print(f"   Topic: {session.topic}")
    print(f"   Started: {session.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 3. Prepare agent input
    print("\n3. Preparing agent input...")
    
    agent_input = AgentInput(
        session_id=session.id,
        agent_type=AgentType.DECOMPOSER,
        data={
            "question": session.topic,
            "context": "Educational technology analysis",
            "complexity_hint": "moderate"
        },
        context={
            "user_preferences": {"depth": "detailed", "focus": "practical"},
            "domain": "education_technology"
        }
    )
    
    print(f"   Question: {agent_input.data['question']}")
    print(f"   Context: {agent_input.data['context']}")
    
    # 4. Create execution context
    print("\n4. Creating execution context...")
    
    execution_context = AgentExecutionContext(
        session_id=session.id,
        user_id=session.user_id,
        flow_step=1,
        execution_mode="demo",
        shared_context={
            "session_start": session.start_time.isoformat(),
            "analysis_depth": "comprehensive"
        }
    )
    
    print(f"   Flow step: {execution_context.flow_step}")
    print(f"   Execution mode: {execution_context.execution_mode}")
    
    # 5. Execute the agent
    print("\n5. Executing agent...")
    
    try:
        output = await agent.execute(agent_input, execution_context)
        
        print(f"   Status: {output.status.value}")
        print(f"   Quality Score: {output.quality_score}")
        print(f"   Execution Time: {output.execution_time:.3f}s")
        
        # Display decomposition results
        decomposition_data = output.data["decomposition"]
        print(f"\n   Decomposition Results:")
        print(f"   - Main Question: {decomposition_data['main_question']}")
        print(f"   - Complexity: {decomposition_data['complexity_assessment']}")
        print(f"   - Strategy: {decomposition_data['decomposition_strategy']}")
        print(f"   - Sub-questions: {len(decomposition_data['sub_questions'])}")
        
        for i, sq in enumerate(decomposition_data['sub_questions'], 1):
            print(f"     {i}. {sq['question']} (Priority: {sq['priority']})")
        
    except Exception as e:
        print(f"   ❌ Execution failed: {e}")
        return
    
    # 6. Display agent performance metrics
    print("\n6. Agent performance metrics...")
    
    metrics = agent.get_performance_metrics()
    print(f"   Total executions: {metrics['total_executions']}")
    print(f"   Success rate: {metrics['success_rate']:.1%}")
    print(f"   Average execution time: {metrics['average_execution_time']:.3f}s")
    print(f"   Average quality score: {metrics['average_quality_score']:.2f}")
    
    # 7. Demonstrate configuration management
    print("\n7. Configuration management demo...")
    
    config_manager = ConfigManager()
    await config_manager.initialize()
    
    # Get system configuration
    system_config = config_manager.get_config('system', {})
    if system_config:
        print(f"   System log level: {config_manager.get_nested_config('system.log_level', 'INFO')}")
        print(f"   Max concurrent agents: {config_manager.get_nested_config('system.max_concurrent_agents', 10)}")
        print(f"   Default timeout: {config_manager.get_nested_config('system.default_timeout', 300)}s")
    else:
        print("   No system configuration found (using defaults)")
    
    # Get agent-specific configuration
    agent_config = config_manager.get_agent_config(AgentType.DECOMPOSER)
    print(f"   Agent temperature: {agent_config.temperature}")
    print(f"   Agent max retries: {agent_config.max_retries}")
    print(f"   Agent quality threshold: {agent_config.quality_threshold}")
    
    await config_manager.cleanup()
    
    print("\n✅ Demo completed successfully!")
    print("\nThis demonstration showed:")
    print("- ✓ Pydantic data models for type-safe data transfer")
    print("- ✓ BaseAgent abstract class with standardized interfaces")
    print("- ✓ Agent factory for registration and creation")
    print("- ✓ Configuration management with YAML support")
    print("- ✓ Error handling and performance monitoring")
    print("- ✓ Async execution with timeout and retry logic")


if __name__ == "__main__":
    asyncio.run(demonstrate_core_interfaces())