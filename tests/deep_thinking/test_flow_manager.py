"""
Tests for the Flow Manager
"""

import pytest
from src.mcps.deep_thinking.flows.flow_manager import FlowManager, FlowStatus, FlowStepStatus
from src.mcps.deep_thinking.config.exceptions import FlowExecutionError, ConfigurationError


class TestFlowManager:
    """Test flow manager functionality"""
    
    @pytest.fixture
    def flow_manager(self):
        """Create a flow manager for testing"""
        return FlowManager()
    
    def test_flow_manager_initialization(self, flow_manager):
        """Test flow manager initialization"""
        stats = flow_manager.get_flow_statistics()
        assert stats['total_flows'] == 0
        assert len(stats['available_flow_types']) > 0
        assert 'comprehensive_analysis' in stats['available_flow_types']
        assert 'quick_analysis' in stats['available_flow_types']
    
    def test_flow_creation(self, flow_manager):
        """Test flow creation"""
        session_id = "test-session-123"
        flow_id = flow_manager.create_flow(session_id, "comprehensive_analysis")
        
        assert flow_id is not None
        assert session_id in flow_id
        
        flow = flow_manager.get_flow(flow_id)
        assert flow is not None
        assert flow.session_id == session_id
        assert flow.status == FlowStatus.INITIALIZED
    
    def test_flow_start_and_progress(self, flow_manager):
        """Test flow start and progress tracking"""
        session_id = "test-session-456"
        flow_id = flow_manager.create_flow(session_id, "quick_analysis")
        
        # Start flow
        flow_manager.start_flow(flow_id)
        flow = flow_manager.get_flow(flow_id)
        assert flow.status == FlowStatus.RUNNING
        
        # Check progress
        progress = flow_manager.get_flow_progress(flow_id)
        assert progress is not None
        assert progress['total_steps'] > 0
        assert progress['completed_steps'] == 0
        assert progress['progress_percentage'] == 0
    
    def test_step_execution(self, flow_manager):
        """Test step execution and completion"""
        session_id = "test-session-789"
        flow_id = flow_manager.create_flow(session_id, "quick_analysis")
        flow_manager.start_flow(flow_id)
        
        # Get first step
        next_step = flow_manager.get_next_step(flow_id)
        assert next_step is not None
        assert next_step.status == FlowStepStatus.PENDING
        
        # Complete step
        step_result = "Problem analyzed successfully"
        flow_manager.complete_step(flow_id, next_step.step_id, step_result, quality_score=0.85)
        
        # Verify completion
        flow = flow_manager.get_flow(flow_id)
        completed_step = flow.steps[next_step.step_id]
        assert completed_step.status == FlowStepStatus.COMPLETED
        assert completed_step.result == step_result
        assert completed_step.quality_score == 0.85
        
        # Check progress update
        progress = flow_manager.get_flow_progress(flow_id)
        assert progress['completed_steps'] == 1
        assert progress['progress_percentage'] > 0
    
    def test_step_dependencies(self, flow_manager):
        """Test step dependency handling"""
        session_id = "test-session-deps"
        flow_id = flow_manager.create_flow(session_id, "comprehensive_analysis")
        flow_manager.start_flow(flow_id)
        
        flow = flow_manager.get_flow(flow_id)
        
        # Find dependent steps
        decompose_step = None
        evidence_step = None
        
        for step in flow.steps.values():
            if step.step_id == 'decompose':
                decompose_step = step
            elif step.step_id == 'evidence':
                evidence_step = step
        
        assert decompose_step is not None
        assert evidence_step is not None
        assert 'decompose' in evidence_step.dependencies
        
        # First step should be decompose
        next_step = flow_manager.get_next_step(flow_id)
        assert next_step.step_id == 'decompose'
        
        # Complete first step
        flow_manager.complete_step(flow_id, 'decompose', "Problem decomposed", 0.8)
        
        # Now evidence step should be available
        next_step = flow_manager.get_next_step(flow_id)
        assert next_step.step_id == 'evidence'
    
    def test_flow_pause_resume(self, flow_manager):
        """Test flow pause and resume functionality"""
        session_id = "test-session-pause"
        flow_id = flow_manager.create_flow(session_id, "quick_analysis")
        flow_manager.start_flow(flow_id)
        
        # Pause flow
        flow_manager.pause_flow(flow_id)
        flow = flow_manager.get_flow(flow_id)
        assert flow.status == FlowStatus.PAUSED
        
        # Resume flow
        flow_manager.resume_flow(flow_id)
        flow = flow_manager.get_flow(flow_id)
        assert flow.status == FlowStatus.RUNNING
    
    def test_step_failure_and_retry(self, flow_manager):
        """Test step failure handling and retry capability"""
        session_id = "test-session-error"
        flow_id = flow_manager.create_flow(session_id, "quick_analysis")
        flow_manager.start_flow(flow_id)
        
        next_step = flow_manager.get_next_step(flow_id)
        
        # Fail the step
        flow_manager.fail_step(flow_id, next_step.step_id, "Test error message")
        
        # Verify failure
        flow = flow_manager.get_flow(flow_id)
        failed_step = flow.steps[next_step.step_id]
        assert failed_step.status == FlowStepStatus.FAILED
        assert failed_step.error_message == "Test error message"
        assert failed_step.retry_count == 1
        assert failed_step.can_retry()
    
    def test_flow_serialization(self, flow_manager):
        """Test flow state serialization"""
        session_id = "test-session-serialize"
        flow_id = flow_manager.create_flow(session_id, "comprehensive_analysis")
        flow_manager.start_flow(flow_id)
        
        # Complete some steps
        flow_manager.complete_step(flow_id, 'decompose', "Step 1 completed", 0.9)
        
        # Test serialization
        flow = flow_manager.get_flow(flow_id)
        flow_dict = flow.to_dict()
        
        assert 'flow_id' in flow_dict
        assert 'steps' in flow_dict
        assert 'progress' in flow_dict
        assert len(flow_dict['steps']) > 0
        
        # Test step serialization
        step_dict = flow.steps['decompose'].to_dict()
        assert step_dict['status'] == 'completed'
        assert step_dict['result'] == "Step 1 completed"
        assert step_dict['quality_score'] == 0.9
    
    def test_flow_statistics(self, flow_manager):
        """Test flow statistics and monitoring"""
        # Create multiple flows
        flow_ids = []
        for i in range(3):
            session_id = f"test-session-stats-{i}"
            flow_id = flow_manager.create_flow(session_id, "quick_analysis")
            flow_ids.append(flow_id)
            flow_manager.start_flow(flow_id)
        
        # Check statistics
        stats = flow_manager.get_flow_statistics()
        assert stats['total_flows'] == 3
        assert 'running' in stats['status_distribution']
        assert stats['status_distribution']['running'] == 3
        
        # Test active flow listing
        active_flows = flow_manager.list_active_flows()
        assert len(active_flows) == 3
        
        # Test session-specific listing
        session_flows = flow_manager.list_active_flows("test-session-stats-0")
        assert len(session_flows) == 1
    
    def test_error_handling(self, flow_manager):
        """Test error handling for invalid operations"""
        # Test invalid flow ID
        with pytest.raises(FlowExecutionError):
            flow_manager.get_next_step("invalid-flow-id")
        
        # Test invalid flow type
        with pytest.raises(ConfigurationError):
            flow_manager.create_flow("test-session", "invalid-flow-type")
        
        # Test invalid step ID
        session_id = "test-session-invalid"
        flow_id = flow_manager.create_flow(session_id, "quick_analysis")
        
        with pytest.raises(FlowExecutionError):
            flow_manager.complete_step(flow_id, "invalid-step-id", "result")


if __name__ == "__main__":
    pytest.main([__file__])