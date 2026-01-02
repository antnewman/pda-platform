"""Content validation for tasks and outputs."""

import re
from typing import Optional

from agent_planning.guardrails.limits import GuardrailConfig, GuardrailViolation


def validate_task_content(
    content: str,
    config: Optional[GuardrailConfig] = None,
) -> None:
    """
    Validate task content against guardrails.

    Args:
        content: Task content to validate
        config: Guardrail configuration

    Raises:
        GuardrailViolation: If content violates guardrails
    """
    if config is None:
        return

    # Check blocked patterns
    for pattern in config.blocked_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            raise GuardrailViolation(
                f"Task content matches blocked pattern: {pattern}"
            )

    # Check for approval requirements
    if config.requires_approval(content):
        raise GuardrailViolation(
            f"Task requires human approval: {content[:50]}..."
        )


def validate_tool_usage(
    tool_name: str,
    config: Optional[GuardrailConfig] = None,
) -> None:
    """
    Validate that a tool is allowed.

    Args:
        tool_name: Name of the tool
        config: Guardrail configuration

    Raises:
        GuardrailViolation: If tool is not allowed
    """
    if config is None or config.allowed_tools is None:
        return

    if tool_name not in config.allowed_tools:
        raise GuardrailViolation(
            f"Tool not in allowed list: {tool_name}"
        )
