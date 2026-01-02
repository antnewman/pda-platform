"""Tests for guardrails."""

import pytest

from agent_planning.guardrails.limits import GuardrailConfig, GuardrailViolation
from agent_planning.guardrails.validators import validate_task_content, validate_tool_usage


class TestGuardrailConfig:
    """Tests for GuardrailConfig."""

    def test_default_values(self):
        """Test default configuration values."""
        config = GuardrailConfig()
        assert config.max_tasks == 15
        assert config.max_iterations == 50
        assert config.max_cost_usd == 5.0
        assert config.timeout_seconds == 300.0

    def test_custom_values(self):
        """Test custom configuration."""
        config = GuardrailConfig(
            max_tasks=10,
            max_iterations=100,
            max_cost_usd=1.0,
        )
        assert config.max_tasks == 10
        assert config.max_iterations == 100
        assert config.max_cost_usd == 1.0

    def test_requires_approval(self):
        """Test approval requirement checking."""
        config = GuardrailConfig(
            require_approval_for=["delete", "send", "publish"]
        )

        assert config.requires_approval("Delete the file")
        assert config.requires_approval("SEND email to client")
        assert not config.requires_approval("Read the document")


class TestValidators:
    """Tests for content validators."""

    def test_blocked_patterns(self):
        """Test blocked pattern validation."""
        config = GuardrailConfig(
            blocked_patterns=[r"rm\s+-rf", r"DROP\s+TABLE"]
        )

        with pytest.raises(GuardrailViolation):
            validate_task_content("Run rm -rf /", config)

        with pytest.raises(GuardrailViolation):
            validate_task_content("Execute DROP TABLE users", config)

        # Should not raise
        validate_task_content("Delete the temporary file", config)

    def test_tool_validation(self):
        """Test tool allowlist validation."""
        config = GuardrailConfig(
            allowed_tools=["search", "read_file", "write_file"]
        )

        # Should not raise
        validate_tool_usage("search", config)
        validate_tool_usage("read_file", config)

        # Should raise
        with pytest.raises(GuardrailViolation):
            validate_tool_usage("execute_shell", config)

    def test_no_config(self):
        """Test that validation passes with no config."""
        # Should not raise
        validate_task_content("Anything goes", None)
        validate_tool_usage("any_tool", None)
