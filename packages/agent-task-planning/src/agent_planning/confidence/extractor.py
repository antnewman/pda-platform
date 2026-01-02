"""Main confidence extraction implementation."""

import asyncio
import json
import time
from typing import Any, Optional, Union, Callable

from ..providers.base import BaseProvider
from ..guardrails.limits import GuardrailConfig
from .models import (
    ConfidenceResult,
    BatchConfidenceResult,
    OutlierReport,
    ReviewLevel,
)
from .schemas import (
    SchemaType,
    CustomSchema,
    get_schema_definition,
    SCHEMA_DEFINITIONS,
)
from .aggregation import (
    detect_numeric_outliers,
    aggregate_numeric,
    aggregate_categorical,
    aggregate_text_exact,
    aggregate_list_fields,
    compute_field_confidence,
    compute_overall_confidence,
    check_early_stop,
)


class ConfidenceExtractor:
    """Extract structured data with confidence scoring via self-consistency."""

    def __init__(
        self,
        provider: BaseProvider,
        guardrails: Optional[GuardrailConfig] = None,
    ):
        """Initialise the confidence extractor.

        Args:
            provider: LLM provider to use for extraction
            guardrails: Configuration including confidence settings
        """
        self.provider = provider
        self.guardrails = guardrails or GuardrailConfig()

        # Extract confidence-specific settings from guardrails
        self.samples = getattr(self.guardrails, 'confidence_samples', 5)
        self.temperature = getattr(self.guardrails, 'confidence_temperature', 0.7)
        self.early_stop_threshold = getattr(
            self.guardrails, 'confidence_early_stop_threshold', 0.6
        )

    async def extract(
        self,
        query: str,
        context: Optional[str] = None,
        schema: Union[SchemaType, CustomSchema] = SchemaType.RISK,
        samples: Optional[int] = None,
        temperature: Optional[float] = None,
        early_stop: bool = True,
    ) -> ConfidenceResult:
        """Extract structured data with confidence scoring.

        Args:
            query: The question or extraction task
            context: Document or context to extract from
            schema: Schema type or custom schema definition
            samples: Number of samples (overrides guardrails)
            temperature: Sampling temperature (overrides guardrails)
            early_stop: Whether to stop early on agreement

        Returns:
            ConfidenceResult with consensus, confidence scores, and outliers
        """
        start_time = time.time()

        # Resolve settings
        num_samples = samples or self.samples
        temp = temperature or self.temperature

        # Get schema definition
        if isinstance(schema, CustomSchema):
            schema_def = {
                "name": schema.name,
                "extraction_prompt": schema.extraction_prompt,
                "aggregation_fields": schema.aggregation_fields,
            }
        else:
            schema_def = get_schema_definition(schema)

        # Build extraction prompt
        extraction_prompt = self._build_extraction_prompt(
            query, context, schema_def["extraction_prompt"]
        )

        # Collect samples
        extractions = []
        raw_responses = []
        total_tokens = 0
        total_cost = 0.0
        samples_used = 0
        early_stopped = False

        for i in range(num_samples):
            try:
                response = await self.provider.complete(
                    messages=[{"role": "user", "content": extraction_prompt}],
                    temperature=temp,
                    max_tokens=2000,
                )

                # Track usage
                samples_used += 1
                total_tokens += response.tokens_used
                total_cost += response.cost_usd

                # Parse extraction
                extracted = self._parse_extraction(response.content)
                if extracted:
                    extractions.append(extracted)
                    raw_responses.append(extracted)

                # Check for early stopping
                if early_stop and check_early_stop(
                    extractions, self.early_stop_threshold
                ):
                    early_stopped = True
                    break

            except Exception as e:
                # Log but continue with other samples
                raw_responses.append({"error": str(e)})

        # Calculate cost saved via early stopping
        if early_stopped:
            samples_not_run = num_samples - samples_used
            avg_cost_per_sample = total_cost / samples_used if samples_used > 0 else 0
            cost_saved = samples_not_run * avg_cost_per_sample
        else:
            cost_saved = 0.0

        # Aggregate results
        if not extractions:
            # No successful extractions
            return ConfidenceResult(
                query=query,
                consensus={},
                confidence=0.0,
                field_confidence={},
                outliers=[],
                raw_responses=raw_responses,
                samples_used=samples_used,
                samples_requested=num_samples,
                early_stopped=early_stopped,
                cost_usd=total_cost,
                cost_saved_usd=cost_saved,
                tokens_used=total_tokens,
                latency_ms=int((time.time() - start_time) * 1000),
                review_level=ReviewLevel.EXPERT_REQUIRED,
                review_reason="No successful extractions",
            )

        # Perform aggregation
        consensus, field_confidence, outliers = self._aggregate_extractions(
            extractions, schema_def.get("aggregation_fields", {})
        )

        # Compute overall confidence
        overall_confidence = compute_overall_confidence(field_confidence)

        # Determine review level
        review_level, review_reason = self._determine_review_level(
            overall_confidence, outliers, field_confidence
        )

        latency_ms = int((time.time() - start_time) * 1000)

        return ConfidenceResult(
            query=query,
            consensus=consensus,
            confidence=overall_confidence,
            field_confidence=field_confidence,
            outliers=outliers,
            raw_responses=raw_responses,
            samples_used=samples_used,
            samples_requested=num_samples,
            early_stopped=early_stopped,
            cost_usd=total_cost,
            cost_saved_usd=cost_saved,
            tokens_used=total_tokens,
            latency_ms=latency_ms,
            review_level=review_level,
            review_reason=review_reason,
        )

    async def extract_batch(
        self,
        queries: list[str],
        context: Optional[str] = None,
        schemas: Optional[list[Union[SchemaType, CustomSchema]]] = None,
        max_concurrent: int = 3,
        progress_callback: Optional[Callable] = None,
    ) -> BatchConfidenceResult:
        """Extract from multiple queries with concurrency control.

        Args:
            queries: List of extraction queries
            context: Shared context for all queries
            schemas: Schema per query (or single schema for all)
            max_concurrent: Maximum concurrent extractions
            progress_callback: Optional async callback(completed, total)

        Returns:
            BatchConfidenceResult with all results and totals
        """
        # Normalise schemas
        if schemas is None:
            schemas = [SchemaType.RISK] * len(queries)
        elif len(schemas) == 1:
            schemas = schemas * len(queries)

        semaphore = asyncio.Semaphore(max_concurrent)
        results = []
        completed = 0
        failed = 0

        async def process_one(query: str, schema: Union[SchemaType, CustomSchema]):
            nonlocal completed, failed
            async with semaphore:
                try:
                    result = await self.extract(query, context, schema)
                    completed += 1
                    if progress_callback:
                        await progress_callback(completed, len(queries))
                    return result
                except Exception as e:
                    failed += 1
                    if progress_callback:
                        await progress_callback(completed, len(queries))
                    return None

        tasks = [
            process_one(q, s) for q, s in zip(queries, schemas)
        ]
        results = await asyncio.gather(*tasks)

        # Filter out None results
        valid_results = [r for r in results if r is not None]

        return BatchConfidenceResult(
            results=valid_results,
            total_cost_usd=sum(r.cost_usd for r in valid_results),
            total_tokens=sum(r.tokens_used for r in valid_results),
            total_latency_ms=sum(r.latency_ms for r in valid_results),
            queries_succeeded=completed,
            queries_failed=failed,
        )

    def _build_extraction_prompt(
        self,
        query: str,
        context: Optional[str],
        schema_prompt: str
    ) -> str:
        """Build the full extraction prompt."""
        parts = [
            "You are a precise extraction assistant. Extract structured information exactly as specified.",
            "",
            "EXTRACTION SCHEMA:",
            schema_prompt,
            "",
            "IMPORTANT:",
            "- Extract only what is explicitly stated or can be directly inferred",
            "- Use null for fields that cannot be determined",
            "- Be consistent in formatting",
            "- Return valid JSON only, no markdown formatting",
            "",
        ]

        if context:
            parts.extend([
                "CONTEXT DOCUMENT:",
                context,
                "",
            ])

        parts.extend([
            "QUERY:",
            query,
            "",
            "OUTPUT (valid JSON array):",
        ])

        return "\n".join(parts)

    def _parse_extraction(self, content: str) -> Optional[dict[str, Any]]:
        """Parse extraction response into structured data."""
        # Clean up common formatting issues
        content = content.strip()

        # Remove markdown code blocks if present
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

        try:
            parsed = json.loads(content)
            # Handle both single object and array responses
            if isinstance(parsed, list):
                return {"items": parsed}
            return parsed
        except json.JSONDecodeError:
            # Try to find JSON in the response
            import re
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

    def _aggregate_extractions(
        self,
        extractions: list[dict[str, Any]],
        aggregation_fields: dict[str, list[str]]
    ) -> tuple[dict[str, Any], dict[str, float], list[OutlierReport]]:
        """Aggregate multiple extractions into consensus with outlier detection.

        Returns:
            Tuple of (consensus_dict, field_confidence_dict, outlier_list)
        """
        consensus = {}
        field_confidence = {}
        all_outliers = []

        # Get all fields from extractions
        all_fields = set()
        for ext in extractions:
            if isinstance(ext, dict):
                all_fields.update(ext.keys())

        # Categorise fields
        numeric_fields = aggregation_fields.get("numeric", [])
        categorical_fields = aggregation_fields.get("categorical", [])
        text_fields = aggregation_fields.get("text", [])
        list_fields = aggregation_fields.get("list", [])

        for field in all_fields:
            values = [ext.get(field) for ext in extractions if field in ext]
            values = [v for v in values if v is not None]

            if not values:
                continue

            sample_indices = list(range(len(values)))

            if field in numeric_fields:
                try:
                    numeric_values = [float(v) for v in values]
                    agg = aggregate_numeric(numeric_values)
                    consensus[field] = agg["median"]

                    # Outlier detection
                    _, outliers = detect_numeric_outliers(
                        numeric_values, sample_indices, field
                    )
                    all_outliers.extend(outliers)

                    field_confidence[field] = compute_field_confidence(
                        numeric_values, "numeric"
                    )
                except (ValueError, TypeError):
                    # Fall back to text handling
                    mode, agreement = aggregate_text_exact([str(v) for v in values])
                    consensus[field] = mode
                    field_confidence[field] = agreement

            elif field in categorical_fields:
                mode, agreement = aggregate_categorical([str(v) for v in values])
                consensus[field] = mode
                field_confidence[field] = agreement

            elif field in list_fields:
                common, coverage = aggregate_list_fields(values)
                consensus[field] = common
                field_confidence[field] = coverage

            else:
                # Default to text handling
                mode, agreement = aggregate_text_exact([str(v) for v in values])
                consensus[field] = mode
                field_confidence[field] = agreement

        return consensus, field_confidence, all_outliers

    def _determine_review_level(
        self,
        confidence: float,
        outliers: list[OutlierReport],
        field_confidence: dict[str, float]
    ) -> tuple[ReviewLevel, Optional[str]]:
        """Determine appropriate human review level."""

        # Expert required if outliers detected or very low confidence
        if outliers or confidence < 0.4:
            reasons = []
            if outliers:
                reasons.append(f"{len(outliers)} outlier(s) detected")
            if confidence < 0.4:
                reasons.append(f"low overall confidence ({confidence:.2f})")
            return ReviewLevel.EXPERT_REQUIRED, "; ".join(reasons)

        # Detailed review for low confidence
        if confidence < 0.6:
            low_fields = [f for f, c in field_confidence.items() if c < 0.5]
            reason = f"moderate confidence ({confidence:.2f})"
            if low_fields:
                reason += f"; low confidence on: {', '.join(low_fields)}"
            return ReviewLevel.DETAILED_REVIEW, reason

        # Spot check for moderate confidence
        if confidence < 0.8:
            return ReviewLevel.SPOT_CHECK, f"good confidence ({confidence:.2f}), spot check recommended"

        # No review needed for high confidence
        return ReviewLevel.NONE, None


# Convenience functions for simpler API

async def confidence_extract(
    query: str,
    provider: BaseProvider,
    context: Optional[str] = None,
    schema: Union[SchemaType, CustomSchema] = SchemaType.RISK,
    guardrails: Optional[GuardrailConfig] = None,
    **kwargs
) -> ConfidenceResult:
    """Convenience function for single extraction.

    Args:
        query: The extraction query
        provider: LLM provider
        context: Optional context document
        schema: Schema type or custom schema
        guardrails: Optional guardrail configuration
        **kwargs: Additional arguments passed to extract()

    Returns:
        ConfidenceResult
    """
    extractor = ConfidenceExtractor(provider, guardrails)
    return await extractor.extract(query, context, schema, **kwargs)


async def confidence_extract_batch(
    queries: list[str],
    provider: BaseProvider,
    context: Optional[str] = None,
    schemas: Optional[list[Union[SchemaType, CustomSchema]]] = None,
    guardrails: Optional[GuardrailConfig] = None,
    **kwargs
) -> BatchConfidenceResult:
    """Convenience function for batch extraction.

    Args:
        queries: List of extraction queries
        provider: LLM provider
        context: Optional shared context
        schemas: Schema(s) for extraction
        guardrails: Optional guardrail configuration
        **kwargs: Additional arguments passed to extract_batch()

    Returns:
        BatchConfidenceResult
    """
    extractor = ConfidenceExtractor(provider, guardrails)
    return await extractor.extract_batch(queries, context, schemas, **kwargs)
