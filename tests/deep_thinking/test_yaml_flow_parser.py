"""
Tests for the YAML Flow Parser
"""

import os
import tempfile
from pathlib import Path

import pytest
import yaml

from src.mcps.deep_thinking.config.exceptions import FlowConfigurationError
from src.mcps.deep_thinking.config.yaml_flow_parser import YAMLFlowParser
from src.mcps.deep_thinking.models.thinking_models import FlowStep, ThinkingFlow


class TestYAMLFlowParser:
    """Test YAML flow parser functionality"""

    @pytest.fixture
    def yaml_parser(self):
        """Create a YAML parser for testing"""
        return YAMLFlowParser()

    @pytest.fixture
    def sample_flow_yaml(self):
        """Sample flow YAML content"""
        return {
            "test_flow": {
                "description": "Test flow for parser",
                "version": "1.0",
                "steps": [
                    {
                        "agent": "decomposer",
                        "name": "Problem Decomposition",
                        "description": "Break down complex problem",
                        "config": {
                            "complexity_level": "adaptive",
                            "max_sub_questions": 5,
                        },
                    },
                    {
                        "agent": "evidence_seeker",
                        "name": "Evidence Collection",
                        "parallel": True,
                        "for_each": "problem_decomposition.sub_questions",  # Fixed reference
                        "config": {"source_diversity": True, "min_sources": 5},
                    },
                    {
                        "agent": "critic",
                        "name": "Critical Evaluation",
                        "repeat_until": "overall_score >= 0.8",
                        "config": {"standards": "paul_elder_full"},
                    },
                ],
                "error_handling": {
                    "retry_strategy": "exponential_backoff",
                    "max_retries": 3,
                },
            }
        }

    @pytest.fixture
    def sample_flow_file(self, sample_flow_yaml):
        """Create a temporary YAML file with sample flow"""
        with tempfile.NamedTemporaryFile(
            suffix=".yaml", mode="w", delete=False
        ) as temp_file:
            yaml.dump(sample_flow_yaml, temp_file)
            temp_path = temp_file.name

        yield temp_path

        # Clean up
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    def test_parser_initialization(self, yaml_parser):
        """Test parser initialization"""
        assert yaml_parser is not None
        assert hasattr(yaml_parser, "parse_file")
        assert hasattr(yaml_parser, "parse_yaml")

    def test_parse_yaml(self, yaml_parser, sample_flow_yaml):
        """Test parsing YAML content"""
        flows = yaml_parser.parse_yaml(sample_flow_yaml)

        assert len(flows) == 1
        assert "test_flow" in flows

        flow = flows["test_flow"]
        assert isinstance(flow, ThinkingFlow)
        assert flow.name == "test_flow"
        assert flow.description == "Test flow for parser"
        assert flow.version == "1.0"
        assert len(flow.steps) == 3

    def test_parse_file(self, yaml_parser, sample_flow_file):
        """Test parsing YAML file"""
        flows = yaml_parser.parse_file(sample_flow_file)

        assert len(flows) == 1
        assert "test_flow" in flows

        flow = flows["test_flow"]
        assert isinstance(flow, ThinkingFlow)
        assert flow.name == "test_flow"
        assert len(flow.steps) == 3

    def test_step_parsing(self, yaml_parser, sample_flow_yaml):
        """Test step parsing"""
        flows = yaml_parser.parse_yaml(sample_flow_yaml)
        flow = flows["test_flow"]

        # Check first step
        step1 = flow.steps[0]
        assert step1.agent_type == "decomposer"
        assert step1.step_name == "Problem Decomposition"
        assert step1.description == "Break down complex problem"
        assert step1.config["complexity_level"] == "adaptive"
        assert step1.config["max_sub_questions"] == 5

        # Check second step with for_each
        step2 = flow.steps[1]
        assert step2.agent_type == "evidence_seeker"
        assert step2.parallel is True
        assert step2.for_each == "problem_decomposition.sub_questions"

        # Check third step with repeat_until
        step3 = flow.steps[2]
        assert step3.agent_type == "critic"
        assert step3.repeat_until == "overall_score >= 0.8"

    def test_dependency_detection(self, yaml_parser, sample_flow_yaml):
        """Test dependency detection"""
        flows = yaml_parser.parse_yaml(sample_flow_yaml)
        flow = flows["test_flow"]

        # Get dependencies for evidence_seeker step
        evidence_step = flow.steps[1]
        dependencies = yaml_parser.get_step_dependencies(evidence_step)

        assert "problem_decomposition" in dependencies
        assert len(dependencies) == 1

    def test_condition_evaluation(self, yaml_parser):
        """Test condition evaluation"""
        context = {
            "critic": {"overall_score": 0.85, "clarity_score": 0.7},
            "decomposer": {"sub_questions": ["q1", "q2", "q3"]},
        }

        # Test various conditions
        assert (
            yaml_parser.evaluate_condition("critic.overall_score >= 0.8", context)
            is True
        )
        assert (
            yaml_parser.evaluate_condition("critic.clarity_score > 0.8", context)
            is False
        )
        assert (
            yaml_parser.evaluate_condition("decomposer.sub_questions == 3", context)
            is False
        )

    def test_reference_resolution(self, yaml_parser):
        """Test reference resolution"""
        context = {
            "critic": {"overall_score": 0.85, "scores": {"clarity": 0.7, "depth": 0.9}},
            "decomposer": {"sub_questions": ["q1", "q2", "q3"]},
        }

        # Test direct reference
        assert yaml_parser.resolve_references("critic.overall_score", context) == 0.85

        # Test nested reference
        assert yaml_parser.resolve_references("critic.scores.depth", context) == 0.9

        # Test non-existent reference
        assert yaml_parser.resolve_references("critic.missing", context) is None

    def test_topological_sort(self, yaml_parser, sample_flow_yaml):
        """Test topological sorting of steps"""
        flows = yaml_parser.parse_yaml(sample_flow_yaml)
        flow = flows["test_flow"]

        sorted_steps = yaml_parser.topological_sort(flow)

        # Problem decomposition should come before evidence_seeker
        decomposer_idx = next(
            (
                i
                for i, step_id in enumerate(sorted_steps)
                if "problem_decomposition" in step_id.lower()
            ),
            -1,
        )
        evidence_idx = next(
            (
                i
                for i, step_id in enumerate(sorted_steps)
                if "evidence" in step_id.lower()
            ),
            -1,
        )

        assert decomposer_idx != -1
        assert evidence_idx != -1
        assert decomposer_idx < evidence_idx

    def test_invalid_yaml(self, yaml_parser):
        """Test handling of invalid YAML"""
        invalid_yaml = "invalid: yaml: content: - not properly formatted"

        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as temp_file:
            temp_file.write(invalid_yaml.encode("utf-8"))
            temp_path = temp_file.name

        try:
            with pytest.raises(FlowConfigurationError):
                yaml_parser.parse_file(temp_path)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_cycle_detection(self, yaml_parser):
        """Test cycle detection in dependencies"""
        # Create a flow with cyclic dependencies
        cyclic_yaml = {
            "cyclic_flow": {
                "steps": [
                    {"agent": "step_a", "name": "Step A", "for_each": "step_c.output"},
                    {"agent": "step_b", "name": "Step B", "for_each": "step_a.output"},
                    {"agent": "step_c", "name": "Step C", "for_each": "step_b.output"},
                ]
            }
        }

        with pytest.raises(FlowConfigurationError) as excinfo:
            yaml_parser.parse_yaml(cyclic_yaml)

        assert "Cycle detected" in str(excinfo.value)

    def test_missing_required_fields(self, yaml_parser):
        """Test handling of missing required fields"""
        # Missing agent field
        invalid_yaml = {
            "invalid_flow": {
                "steps": [
                    {
                        "name": "Missing Agent",
                        "description": "This step is missing the agent field",
                    }
                ]
            }
        }

        with pytest.raises(FlowConfigurationError) as excinfo:
            yaml_parser.parse_yaml(invalid_yaml)

        assert "missing required 'agent' field" in str(excinfo.value)

    def test_nonexistent_file(self, yaml_parser):
        """Test handling of nonexistent file"""
        with pytest.raises(FlowConfigurationError) as excinfo:
            yaml_parser.parse_file("nonexistent_file.yaml")

        assert "not found" in str(excinfo.value)


if __name__ == "__main__":
    pytest.main([__file__])
