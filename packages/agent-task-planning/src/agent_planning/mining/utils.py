"""Utility functions for outlier mining."""

import json
import re
import numpy as np
from typing import Any, Optional

from .models import QualityScore
from .config import PromptDiversification


# Role injection templates for prompt diversification
ROLE_TEMPLATES = [
    "You are a cautious analyst who identifies potential problems.",
    "You are an optimistic strategist who sees opportunities.",
    "You are a pragmatic project manager focused on delivery.",
    "You are a critical reviewer looking for gaps and weaknesses.",
    "You are a creative problem-solver who thinks unconventionally.",
    "You are a risk-averse auditor who prioritises safety.",
    "You are an experienced practitioner who has seen similar situations.",
    "You are a fresh perspective from outside the domain.",
    "You are a detail-oriented specialist who examines specifics.",
    "You are a big-picture thinker who considers systemic effects.",
]

# Instruction variation templates
INSTRUCTION_VARIATIONS = [
    "Analyse this and provide your assessment:",
    "Consider this carefully and share your findings:",
    "Review the following and identify key points:",
    "Examine this situation and provide insights:",
    "Evaluate this and give your professional opinion:",
    "Study this and highlight what stands out:",
    "Assess this from multiple angles:",
    "Look at this critically and share observations:",
    "Consider what others might miss in this:",
    "Think through this systematically:",
]


def diversify_prompt(
    base_prompt: str,
    sample_index: int,
    strategy: PromptDiversification,
) -> str:
    """Apply prompt diversification strategy.

    Args:
        base_prompt: Original prompt
        sample_index: Which sample this is (for deterministic variation)
        strategy: Which diversification strategy to use

    Returns:
        Modified prompt with diversification applied
    """
    if strategy == PromptDiversification.NONE:
        return base_prompt

    parts = []

    if strategy in (PromptDiversification.ROLE_INJECTION, PromptDiversification.ALL):
        role = ROLE_TEMPLATES[sample_index % len(ROLE_TEMPLATES)]
        parts.append(role)

    if strategy in (PromptDiversification.INSTRUCTION_VARIATION, PromptDiversification.ALL):
        instruction = INSTRUCTION_VARIATIONS[sample_index % len(INSTRUCTION_VARIATIONS)]
        parts.append(instruction)

    if parts:
        prefix = " ".join(parts)
        return f"{prefix}\n\n{base_prompt}"

    return base_prompt


def parse_json_response(content: str) -> Optional[dict[str, Any]]:
    """Parse JSON from LLM response."""
    content = content.strip()

    # Remove markdown code blocks
    if content.startswith("```"):
        lines = content.split("\n")
        content = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

    try:
        parsed = json.loads(content)
        if isinstance(parsed, list):
            return {"items": parsed}
        return parsed
    except json.JSONDecodeError:
        # Try to find JSON in the response
        json_match = re.search(r'\[[\s\S]*\]|\{[\s\S]*\}', content)
        if json_match:
            try:
                parsed = json.loads(json_match.group())
                if isinstance(parsed, list):
                    return {"items": parsed}
                return parsed
            except json.JSONDecodeError:
                pass
        return None


def assess_quality(
    response: str,
    query: str,
    extracted: Optional[dict],
    threshold: float = 0.6
) -> QualityScore:
    """Assess quality of a response.

    Args:
        response: Raw LLM response text
        query: Original query
        extracted: Parsed/extracted content
        threshold: Quality threshold

    Returns:
        QualityScore
    """
    # Basic coherence check
    coherence = 1.0
    if not response or len(response.strip()) < 10:
        coherence = 0.0
    if extracted is None:
        coherence -= 0.3

    # Relevance check (simple keyword matching)
    query_words = set(query.lower().split())
    response_words = set(response.lower().split())
    overlap = len(query_words & response_words)
    relevance = min(1.0, overlap / max(len(query_words), 1))

    # Completeness check
    completeness = 0.7  # Default moderate
    if extracted and isinstance(extracted, dict):
        items = extracted.get("items", [])
        if isinstance(items, list) and len(items) > 0:
            completeness = 0.9

    # Entropy (placeholder - would require proper implementation)
    entropy = 0.3

    return QualityScore.compute(
        coherence=max(0, coherence),
        relevance=relevance,
        completeness=completeness,
        entropy=entropy,
        threshold=threshold
    )


def compute_novelty(
    candidate_embedding: np.ndarray,
    other_embeddings: list[np.ndarray]
) -> float:
    """Compute novelty based on distance from other candidates.

    Args:
        candidate_embedding: Embedding of this candidate
        other_embeddings: Embeddings of other candidates

    Returns:
        Novelty score 0-1
    """
    if not other_embeddings:
        return 1.0

    # Compute cosine similarities
    similarities = []
    for other in other_embeddings:
        # Cosine similarity
        dot = np.dot(candidate_embedding, other)
        norm_prod = np.linalg.norm(candidate_embedding) * np.linalg.norm(other)
        if norm_prod > 0:
            sim = dot / norm_prod
        else:
            sim = 0
        similarities.append(sim)

    # Novelty = 1 - max similarity
    max_sim = max(similarities)
    return 1.0 - max_sim


def compute_coherence(content: dict[str, Any], quality_overall: float) -> float:
    """Compute coherence score.

    Args:
        content: Extracted content
        quality_overall: Overall quality score

    Returns:
        Coherence score 0-1
    """
    if not content:
        return 0.0

    score = quality_overall

    # Check if has structured items
    if isinstance(content, dict):
        items = content.get("items", [])
        if isinstance(items, list) and items:
            score = min(score + 0.1, 1.0)

            # Check consistency
            if len(items) > 1:
                first_keys = set(items[0].keys()) if isinstance(items[0], dict) else set()
                consistent = all(
                    set(item.keys()) == first_keys
                    for item in items[1:]
                    if isinstance(item, dict)
                )
                if consistent:
                    score = min(score + 0.1, 1.0)

    return score


def compute_coverage(content: dict[str, Any], query: str) -> float:
    """Compute coverage score.

    Args:
        content: Extracted content
        query: Original query

    Returns:
        Coverage score 0-1
    """
    if not content:
        return 0.0

    score = 0.5

    # Query keyword coverage
    query_words = set(query.lower().split())
    content_str = str(content).lower()
    matched = sum(1 for w in query_words if w in content_str)
    if query_words:
        score += 0.25 * (matched / len(query_words))

    # Check for substantial content
    if isinstance(content, dict):
        items = content.get("items", [])
        if isinstance(items, list) and len(items) > 0:
            score += 0.25

    return min(1.0, score)


def compute_composite_score(
    novelty: float,
    coherence: float,
    coverage: float,
    novelty_weight: float = 0.4,
    coherence_weight: float = 0.3,
    coverage_weight: float = 0.3
) -> float:
    """Compute weighted composite score.

    Args:
        novelty: Novelty score 0-1
        coherence: Coherence score 0-1
        coverage: Coverage score 0-1
        novelty_weight: Weight for novelty
        coherence_weight: Weight for coherence
        coverage_weight: Weight for coverage

    Returns:
        Composite score 0-1
    """
    return (
        novelty * novelty_weight +
        coherence * coherence_weight +
        coverage * coverage_weight
    )
