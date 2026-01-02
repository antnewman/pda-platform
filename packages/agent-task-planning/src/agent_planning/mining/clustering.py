"""Response clustering using UMAP + HDBSCAN with fallbacks."""

import numpy as np
from dataclasses import dataclass
from typing import Optional

# Optional dependencies with fallbacks
try:
    import umap
    UMAP_AVAILABLE = True
except ImportError:
    UMAP_AVAILABLE = False

try:
    import hdbscan
    HDBSCAN_AVAILABLE = True
except ImportError:
    HDBSCAN_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    from sklearn.metrics import silhouette_score
    from sklearn.cluster import AgglomerativeClustering
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


@dataclass
class ClusterResult:
    """Result of clustering operation."""
    labels: list[int]                       # Cluster label per sample (-1 = noise)
    n_clusters: int                         # Number of clusters found
    silhouette: float                       # Cluster quality score
    embeddings: np.ndarray                  # Original embeddings
    reduced_embeddings: Optional[np.ndarray]  # UMAP-reduced embeddings
    cluster_centers: dict[int, np.ndarray]  # Centroid per cluster


class ResponseClusterer:
    """Clusters LLM responses using UMAP + HDBSCAN."""

    def __init__(
        self,
        embedding_model: str = "all-MiniLM-L6-v2",
        umap_n_components: int = 10,
        umap_n_neighbors: int = 15,
        umap_min_dist: float = 0.1,
        hdbscan_min_cluster_size: int = 2,
        hdbscan_min_samples: int = 1,
    ):
        """Initialise the clusterer.

        Args:
            embedding_model: Sentence transformer model name
            umap_n_components: Target dimensionality for UMAP
            umap_n_neighbors: UMAP local neighborhood size
            umap_min_dist: UMAP minimum distance between points
            hdbscan_min_cluster_size: Minimum samples per cluster
            hdbscan_min_samples: HDBSCAN core sample threshold
        """
        self.embedding_model_name = embedding_model
        self.umap_n_components = umap_n_components
        self.umap_n_neighbors = umap_n_neighbors
        self.umap_min_dist = umap_min_dist
        self.hdbscan_min_cluster_size = hdbscan_min_cluster_size
        self.hdbscan_min_samples = hdbscan_min_samples

        self._embedding_model = None
        self._embedding_cache: dict[str, np.ndarray] = {}

    @property
    def embedding_model(self):
        """Lazy load embedding model."""
        if self._embedding_model is None:
            if not SENTENCE_TRANSFORMERS_AVAILABLE:
                raise ImportError(
                    "sentence-transformers required for clustering. "
                    "Install with: pip install sentence-transformers"
                )
            self._embedding_model = SentenceTransformer(self.embedding_model_name)
        return self._embedding_model

    def cluster(self, responses: list[str]) -> ClusterResult:
        """Cluster responses into distinct approaches.

        Args:
            responses: List of LLM response texts

        Returns:
            ClusterResult with labels and metadata
        """
        if len(responses) < 3:
            # Not enough for meaningful clustering
            return ClusterResult(
                labels=list(range(len(responses))),  # Each its own cluster
                n_clusters=len(responses),
                silhouette=0.0,
                embeddings=np.array([]),
                reduced_embeddings=None,
                cluster_centers={},
            )

        # Step 1: Embed responses
        embeddings = self._embed_responses(responses)

        # Step 2: Reduce dimensionality with UMAP
        reduced = self._reduce_dimensionality(embeddings)

        # Step 3: Cluster with HDBSCAN (or fallback)
        labels = self._cluster_embeddings(reduced)

        # Step 4: Compute cluster centers
        centers = self._compute_centers(reduced, labels)

        # Step 5: Compute silhouette score
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        if n_clusters > 1 and n_clusters < len(responses) and SKLEARN_AVAILABLE:
            try:
                sil_score = silhouette_score(reduced, labels)
            except:
                sil_score = 0.0
        else:
            sil_score = 0.0

        return ClusterResult(
            labels=list(labels),
            n_clusters=n_clusters,
            silhouette=float(sil_score),
            embeddings=embeddings,
            reduced_embeddings=reduced,
            cluster_centers=centers,
        )

    def _embed_responses(self, responses: list[str]) -> np.ndarray:
        """Embed responses using sentence transformer."""
        # Check cache
        uncached = []
        uncached_indices = []
        embeddings = [None] * len(responses)

        for i, resp in enumerate(responses):
            cache_key = resp[:500]  # Truncate for cache key
            if cache_key in self._embedding_cache:
                embeddings[i] = self._embedding_cache[cache_key]
            else:
                uncached.append(resp)
                uncached_indices.append(i)

        # Embed uncached
        if uncached:
            new_embeddings = self.embedding_model.encode(uncached, show_progress_bar=False)
            for idx, emb in zip(uncached_indices, new_embeddings):
                embeddings[idx] = emb
                cache_key = responses[idx][:500]
                self._embedding_cache[cache_key] = emb

        return np.array(embeddings)

    def _reduce_dimensionality(self, embeddings: np.ndarray) -> np.ndarray:
        """Reduce dimensionality using UMAP."""
        if not UMAP_AVAILABLE:
            # Fallback: simple PCA-like reduction using SVD
            if embeddings.shape[1] <= self.umap_n_components:
                return embeddings

            # Center the data
            centered = embeddings - embeddings.mean(axis=0)
            # SVD
            U, S, Vt = np.linalg.svd(centered, full_matrices=False)
            # Project onto top components
            return centered @ Vt[:self.umap_n_components].T

        # Use UMAP
        reducer = umap.UMAP(
            n_components=min(self.umap_n_components, embeddings.shape[0] - 1),
            n_neighbors=min(self.umap_n_neighbors, embeddings.shape[0] - 1),
            min_dist=self.umap_min_dist,
            metric="cosine",
            random_state=42,
        )
        return reducer.fit_transform(embeddings)

    def _cluster_embeddings(self, embeddings: np.ndarray) -> np.ndarray:
        """Cluster reduced embeddings using HDBSCAN or fallback."""
        if HDBSCAN_AVAILABLE:
            clusterer = hdbscan.HDBSCAN(
                min_cluster_size=self.hdbscan_min_cluster_size,
                min_samples=self.hdbscan_min_samples,
                metric="euclidean",
            )
            labels = clusterer.fit_predict(embeddings)
        elif SKLEARN_AVAILABLE:
            # Fallback to Agglomerative Clustering
            # Estimate number of clusters based on silhouette
            best_labels = None
            best_score = -1

            for n_clusters in range(2, min(len(embeddings) // 2 + 1, 10)):
                clusterer = AgglomerativeClustering(n_clusters=n_clusters)
                labels = clusterer.fit_predict(embeddings)
                try:
                    score = silhouette_score(embeddings, labels)
                    if score > best_score:
                        best_score = score
                        best_labels = labels
                except:
                    continue

            labels = best_labels if best_labels is not None else np.zeros(len(embeddings))
        else:
            # Last resort: each response is its own cluster
            labels = np.arange(len(embeddings))

        return labels

    def _compute_centers(
        self,
        embeddings: np.ndarray,
        labels: np.ndarray
    ) -> dict[int, np.ndarray]:
        """Compute centroid for each cluster."""
        centers = {}
        for label in set(labels):
            if label == -1:  # Skip noise
                continue
            mask = labels == label
            centers[label] = embeddings[mask].mean(axis=0)
        return centers

    def get_nearest_to_center(
        self,
        cluster_id: int,
        embeddings: np.ndarray,
        labels: np.ndarray,
        centers: dict[int, np.ndarray],
    ) -> int:
        """Get index of sample nearest to cluster center."""
        if cluster_id not in centers:
            # Return first sample in cluster
            return int(np.where(labels == cluster_id)[0][0])

        mask = labels == cluster_id
        cluster_embeddings = embeddings[mask]
        cluster_indices = np.where(mask)[0]

        center = centers[cluster_id]
        distances = np.linalg.norm(cluster_embeddings - center, axis=1)
        nearest_idx = np.argmin(distances)

        return int(cluster_indices[nearest_idx])
