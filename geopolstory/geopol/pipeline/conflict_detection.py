from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable, List, Optional, Sequence, Tuple

import numpy as np
try:  # optional dependency loaded lazily
    from sentence_transformers import SentenceTransformer  # type: ignore
except Exception:  # pragma: no cover - handled lazily
    SentenceTransformer = None  # type: ignore

from ..models import Conflict, Episode, RawNews
from .processing import Preprocessor, build_entity_signature


@dataclass
class DetectionResult:
    conflict: Conflict
    created: bool
    similarity: float


class ConflictDetector:
    """Detects whether a new article belongs to an existing conflict.

    Strategy:
    1) Build entity signature from NER (fast, deterministic)
    2) Compute text embedding (title + lead) and compare to conflict centroids
    3) Thresholds: if signature match and similarity > t1 -> same conflict
       else if signature partial + similarity > t2 -> same conflict
       else create new conflict
    """

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> None:
        self.pre = Preprocessor()
        # Lazy-load model
        self._model: Optional[SentenceTransformer] = None
        self.model_name = model_name

    def _ensure_model(self) -> None:
        if self._model is None:
            if SentenceTransformer is None:
                raise RuntimeError(
                    "sentence-transformers not installed. Install requirements-ml.txt or monkeypatch _embed."
                )
            self._model = SentenceTransformer(self.model_name)

    def _embed(self, texts: List[str]) -> np.ndarray:
        self._ensure_model()
        return np.array(self._model.encode(texts, normalize_embeddings=True))

    def detect_or_create(self, article: RawNews) -> DetectionResult:
        ner = self.pre.ner(article.text[:2000])
        signature = build_entity_signature(ner)

        # Try direct signature match first
        conflict = Conflict.objects.filter(entity_signature=signature).first()
        if conflict:
            return DetectionResult(conflict=conflict, created=False, similarity=1.0)

        # Embedding similarity versus existing conflicts
        text = f"{article.title}\n\n{article.text[:1000]}"
        vec = self._embed([text])[0]
        best_sim, best_conflict = -1.0, None
        candidates = list(Conflict.objects.all().only("id", "name", "embedding"))
        for c in candidates:
            if not c.embedding:
                continue
            cvec = np.array(c.embedding, dtype=float)
            sim = float(np.dot(vec, cvec) / (np.linalg.norm(vec) * np.linalg.norm(cvec) + 1e-9))
            if sim > best_sim:
                best_sim, best_conflict = sim, c

        THRESHOLD_NEW = 0.60
        if best_conflict and best_sim >= THRESHOLD_NEW:
            return DetectionResult(conflict=best_conflict, created=False, similarity=best_sim)

        # Create new conflict
        conflict = Conflict.objects.create(
            name=article.title[:200],
            description=article.text[:500],
            entity_signature=signature,
            embedding=vec.tolist(),
            confidence=0.5,
        )
        return DetectionResult(conflict=conflict, created=True, similarity=0.0)

    def update_conflict_embedding(self, conflict: Conflict, new_vectors: List[np.ndarray]) -> None:
        # Update centroid embedding as running average
        prev = np.array(conflict.embedding, dtype=float) if conflict.embedding else None
        if prev is None:
            conflict.embedding = new_vectors[-1].tolist()
        else:
            new = np.mean([prev] + new_vectors, axis=0)
            conflict.embedding = new.tolist()
        conflict.save(update_fields=["embedding"])
