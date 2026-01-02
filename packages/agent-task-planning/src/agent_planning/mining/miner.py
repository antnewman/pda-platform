"""Main outlier mining implementation."""

import asyncio
import time
from typing import Any, Optional, Union

from ..providers.base import BaseProvider
from ..confidence.schemas import SchemaType, CustomSchema, get_schema_definition
from .config import MiningConfig
from .models import (
    MiningCandidate,
    MiningResult,
    BatchMiningResult,
    ClusterInfo,
    SaturationSignal,
    QualityScore,
)
from .clustering import ResponseClusterer
from .utils import (
    diversify_prompt,
    parse_json_response,
    assess_quality,
    compute_novelty,
    compute_coherence,
    compute_coverage,
    compute_composite_score,
)


class OutlierMiner:
    """Mine outliers for novel insights and diverse approaches."""

    def __init__(
        self,
        provider: BaseProvider,
        config: Optional[MiningConfig] = None,
    ):
        """Initialise the outlier miner.

        Args:
            provider: LLM provider for generation
            config: Mining configuration
        """
        self.provider = provider
        self.config = config or MiningConfig()
        self.clusterer = ResponseClusterer(
            umap_n_components=self.config.umap_n_components,
            umap_n_neighbors=self.config.umap_n_neighbors,
            umap_min_dist=self.config.umap_min_dist,
            hdbscan_min_cluster_size=self.config.hdbscan_min_cluster_size,
            hdbscan_min_samples=self.config.hdbscan_min_samples,
        )

    async def mine(
        self,
        query: str,
        context: Optional[str] = None,
        schema: Union[SchemaType, CustomSchema] = SchemaType.RISK,
    ) -> MiningResult:
        """Mine for diverse approaches and outlier insights.

        Args:
            query: The question or extraction task
            context: Document or context to extract from
            schema: Schema type or custom schema

        Returns:
            MiningResult with diverse candidates
        """
        start_time = time.time()

        # Get schema definition
        if isinstance(schema, CustomSchema):
            schema_def = {
                "name": schema.name,
                "extraction_prompt": schema.extraction_prompt,
            }
            schema_name = schema.name
        else:
            schema_def = get_schema_definition(schema)
            schema_name = schema.value

        # Build base extraction prompt
        base_prompt = self._build_extraction_prompt(
            query, context, schema_def["extraction_prompt"]
        )

        # Step 1: Generate diverse responses
        generations = []
        total_tokens = 0
        total_cost = 0.0

        for i in range(self.config.samples):
            try:
                # Get temperature for this sample
                temperature = self.config.get_temperature(i, self.config.samples)

                # Diversify prompt
                diversified_prompt = diversify_prompt(
                    base_prompt, i, self.config.diversification
                )

                # Generate
                response = await self.provider.complete(
                    messages=[{"role": "user", "content": diversified_prompt}],
                    temperature=temperature,
                    max_tokens=2000,
                )

                total_tokens += response.tokens_used
                total_cost += response.cost_usd

                # Parse extraction
                extracted = parse_json_response(response.content)

                # Assess quality
                quality = assess_quality(
                    response.content,
                    query,
                    extracted,
                    self.config.quality_threshold
                )

                generations.append({
                    "sample_index": i,
                    "content": response.content,
                    "extracted": extracted,
                    "quality": quality,
                    "temperature": temperature,
                    "tokens_used": response.tokens_used,
                    "cost_usd": response.cost_usd,
                })

            except Exception as e:
                # Log but continue
                generations.append({
                    "sample_index": i,
                    "error": str(e),
                })

        # Step 2: Filter by quality
        filtered = [g for g in generations if g.get("quality") and g["quality"].passed_threshold]
        quality_pass_rate = len(filtered) / len(generations) if generations else 0

        # Step 3: Cluster responses
        if not filtered:
            # No valid responses
            return self._empty_result(query, context, schema_name, total_tokens, total_cost, start_time)

        response_texts = [g["content"] for g in filtered]
        cluster_result = self.clusterer.cluster(response_texts)

        # Step 4: Build candidates from clusters
        candidates = []
        clusters_info = []

        for cluster_id in set(cluster_result.labels):
            if cluster_id == -1:  # Skip noise
                continue

            # Get samples in this cluster
            cluster_indices = [i for i, label in enumerate(cluster_result.labels) if label == cluster_id]
            if not cluster_indices:
                continue

            # Pick representative (nearest to center)
            if cluster_result.reduced_embeddings is not None:
                rep_idx = self.clusterer.get_nearest_to_center(
                    cluster_id,
                    cluster_result.reduced_embeddings,
                    cluster_result.labels,
                    cluster_result.cluster_centers,
                )
            else:
                rep_idx = cluster_indices[0]

            generation = filtered[rep_idx]

            # Create candidate
            candidate_id = f"cand_{cluster_id}"
            candidate = MiningCandidate(
                id=candidate_id,
                cluster_id=str(cluster_id),
                sample_indices=cluster_indices,
                content=generation.get("extracted", {}),
                raw_response=generation["content"],
                quality=generation["quality"],
                approach_summary=f"Cluster {cluster_id} approach",
                distinctive_features=[],
                assumptions=[],
                novelty_score=0.0,
                coherence_score=0.0,
                coverage_score=0.0,
                composite_score=0.0,
                differences_from_consensus=[],
                generation_rank=generation["sample_index"],
                token_count=generation.get("tokens_used", 0),
                temperature_used=generation.get("temperature", 0.8),
            )

            candidates.append(candidate)

            # Create cluster info
            is_singleton = len(cluster_indices) == 1
            clusters_info.append(ClusterInfo(
                cluster_id=str(cluster_id),
                size=len(cluster_indices),
                summary=f"Approach found in {len(cluster_indices)} sample(s)",
                distinctive_theme="",
                sample_indices=cluster_indices,
                centroid_distance=0.0,
                is_singleton=is_singleton,
            ))

        # Step 5: Score candidates
        if cluster_result.reduced_embeddings is not None:
            for i, candidate in enumerate(candidates):
                rep_idx = candidate.sample_indices[0]
                cand_embedding = cluster_result.reduced_embeddings[rep_idx]
                other_embeddings = [
                    cluster_result.reduced_embeddings[c.sample_indices[0]]
                    for j, c in enumerate(candidates) if j != i
                ]

                candidate.novelty_score = compute_novelty(cand_embedding, other_embeddings)
                candidate.coherence_score = compute_coherence(
                    candidate.content, candidate.quality.overall
                )
                candidate.coverage_score = compute_coverage(candidate.content, query)
                candidate.composite_score = compute_composite_score(
                    candidate.novelty_score,
                    candidate.coherence_score,
                    candidate.coverage_score,
                    self.config.novelty_weight,
                    self.config.coherence_weight,
                    self.config.coverage_weight,
                )

        # Step 6: Rank candidates
        candidates.sort(key=lambda c: c.composite_score, reverse=True)
        top_candidates = candidates[:self.config.max_candidates_returned]

        # Step 7: Compute diversity
        novelty_scores = [c.novelty_score for c in candidates]
        diversity_score = sum(novelty_scores) / len(novelty_scores) if novelty_scores else 0
        effective_diversity = diversity_score * quality_pass_rate

        # Build result
        latency_ms = int((time.time() - start_time) * 1000)

        return MiningResult(
            query=query,
            context=context,
            schema_used=schema_name,
            candidates=top_candidates,
            consensus_baseline=None,
            num_clusters=cluster_result.n_clusters,
            clusters=clusters_info,
            silhouette_score=cluster_result.silhouette,
            diversity_score=diversity_score,
            effective_diversity=effective_diversity,
            convergence_point=None,
            samples_generated=len(generations),
            samples_passed_quality=len(filtered),
            quality_pass_rate=quality_pass_rate,
            saturation_signals=[],
            review_priority=[c.id for c in top_candidates],
            high_novelty_candidates=[c.id for c in top_candidates if c.novelty_score > 0.7],
            potential_hallucinations=[
                c.id for c in top_candidates
                if c.quality.semantic_entropy > self.config.entropy_threshold
            ],
            tokens_used=total_tokens,
            cost_usd=total_cost,
            config=self.config,
            latency_ms=latency_ms,
        )

    async def mine_batch(
        self,
        queries: list[str],
        context: Optional[str] = None,
        schemas: Optional[list[Union[SchemaType, CustomSchema]]] = None,
        max_concurrent: int = 2,
    ) -> BatchMiningResult:
        """Mine multiple queries with concurrency control.

        Args:
            queries: List of queries to mine
            context: Shared context for all queries
            schemas: Schema per query (or single for all)
            max_concurrent: Maximum concurrent mining operations

        Returns:
            BatchMiningResult with all results
        """
        if schemas is None:
            schemas = [SchemaType.RISK] * len(queries)
        elif len(schemas) == 1:
            schemas = schemas * len(queries)

        semaphore = asyncio.Semaphore(max_concurrent)
        succeeded = 0
        failed = 0

        async def mine_one(query: str, schema: Union[SchemaType, CustomSchema]):
            nonlocal succeeded, failed
            async with semaphore:
                try:
                    result = await self.mine(query, context, schema)
                    succeeded += 1
                    return result
                except Exception as e:
                    failed += 1
                    return None

        tasks = [mine_one(q, s) for q, s in zip(queries, schemas)]
        all_results = await asyncio.gather(*tasks)

        valid_results = [r for r in all_results if r is not None]

        return BatchMiningResult(
            results=valid_results,
            total_cost_usd=sum(r.cost_usd for r in valid_results),
            total_tokens=sum(r.tokens_used for r in valid_results),
            total_latency_ms=sum(r.latency_ms for r in valid_results),
            queries_succeeded=succeeded,
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

    def _empty_result(
        self,
        query: str,
        context: Optional[str],
        schema_name: str,
        tokens: int,
        cost: float,
        start_time: float
    ) -> MiningResult:
        """Create empty result when no valid responses."""
        return MiningResult(
            query=query,
            context=context,
            schema_used=schema_name,
            candidates=[],
            consensus_baseline=None,
            num_clusters=0,
            clusters=[],
            silhouette_score=0.0,
            diversity_score=0.0,
            effective_diversity=0.0,
            convergence_point=None,
            samples_generated=0,
            samples_passed_quality=0,
            quality_pass_rate=0.0,
            saturation_signals=[],
            review_priority=[],
            high_novelty_candidates=[],
            potential_hallucinations=[],
            tokens_used=tokens,
            cost_usd=cost,
            config=self.config,
            latency_ms=int((time.time() - start_time) * 1000),
        )


# Convenience functions

async def mine(
    query: str,
    provider: BaseProvider,
    context: Optional[str] = None,
    schema: Union[SchemaType, CustomSchema] = SchemaType.RISK,
    config: Optional[MiningConfig] = None,
) -> MiningResult:
    """Convenience function for single mining operation."""
    miner = OutlierMiner(provider, config)
    return await miner.mine(query, context, schema)


async def mine_batch(
    queries: list[str],
    provider: BaseProvider,
    context: Optional[str] = None,
    schemas: Optional[list[Union[SchemaType, CustomSchema]]] = None,
    config: Optional[MiningConfig] = None,
    max_concurrent: int = 2,
) -> BatchMiningResult:
    """Convenience function for batch mining."""
    miner = OutlierMiner(provider, config)
    return await miner.mine_batch(queries, context, schemas, max_concurrent)
