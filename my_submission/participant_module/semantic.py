"""Semantic stages on top of lexical retrieval, cheapest first:

  1. embeddings  widen the candidate pool with sentences close in meaning to the criterion
  2. reranker    cross-encoder relevance of (criterion, sentence) for the best pool members
  3. NLI         does the sentence entail the criterion statement about this target?

Every stage is optional: when a model is missing or time is short, the stage is skipped and the
candidates keep the scores of the earlier stages. Scores are stored on each candidate
(`candidate.extra`) and fused by `fuse`.
"""

from __future__ import annotations

import math
import time
from collections.abc import Sequence
from dataclasses import dataclass, field

from participant_module.criteria import Profile
from participant_module.models import Models
from participant_module.pdf_text import Sentence
from participant_module.retrieve import Candidate, sentence_quality
from participant_module.safety import Budget

MAX_EMBED_SENTENCES = 4000


@dataclass
class StageLog:
    timings: dict[str, float] = field(default_factory=dict)
    skipped: list[str] = field(default_factory=list)


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


# Fusion weights tuned on weak gold pages with 2-fold CV (dev/tune_fusion.py, run sem3):
# lexical + embedding similarity ranked the reference page into the first 3 cited pages in 0.747
# of cases vs 0.684 for lexical alone; reranker and NLI did not improve ranking there.
WEIGHTS = {"lex": 0.2, "emb": 0.3, "rr": 0.2, "nli": 0.3, "qual": 0.3}


def fuse(c: Candidate, profile: Profile, weights: dict[str, float] | None = None) -> float:
    """Final candidate score from every stage that ran (missing stages are re-weighted away)."""
    w = weights or WEIGHTS
    parts: list[tuple[float, float]] = [(w["lex"], c.score_lexical)]
    if "emb" in c.extra:
        parts.append((w["emb"], max(0.0, c.extra["emb"])))
    if "rr" in c.extra:
        parts.append((w["rr"], _sigmoid(c.extra["rr"])))
    if "nli" in c.extra:
        parts.append((w["nli"], c.extra["nli"]))
    total = sum(weight for weight, _ in parts) or 1.0
    value = sum(weight * v for weight, v in parts) / total
    return value * (1 - w["qual"] + w["qual"] * sentence_quality(c.sentence.text))


class Semantic:
    def __init__(self, models: Models, budget: Budget, log: StageLog) -> None:
        self.models = models
        self.budget = budget
        self.log = log
        self.matrix = None  # embeddings of eligible sentences
        self.row: dict[int, int] = {}  # sentence.index -> row

    def embed_sentences(self, sentences: Sequence[Sentence]) -> None:
        """Embed eligible sentences, evidence-dense sections first, capped."""
        if not self.budget.allows(40_000) or not self.models.available("embedder"):
            self.log.skipped.append("embed")
            return
        start = time.monotonic()
        priority = {"abstract": 0, "summary": 1, "results": 2, "introduction": 3, "methods": 4, "body": 5}
        chosen = sorted(sentences, key=lambda x: (priority.get(x.role, 6), x.index))[:MAX_EMBED_SENTENCES]
        matrix = self.models.embed([x.text for x in chosen])
        if matrix is None:
            self.log.skipped.append("embed")
            return
        self.matrix = matrix
        self.row = {x.index: i for i, x in enumerate(chosen)}
        self.log.timings["embed"] = time.monotonic() - start

    def widen(self, profile: Profile, pool: list[Candidate], everything: Sequence[Candidate],
              top_k: int = 25) -> list[Candidate]:
        """Add the sentences most similar to the criterion; record cosine similarity on all."""
        if self.matrix is None:
            return pool
        query = self.models.embed(profile.queries[:3])
        if query is None:
            return pool
        centroid = query.mean(axis=0)
        sims = self.matrix @ centroid
        by_index = {c.sentence.index: c for c in everything}
        present = {c.sentence.index for c in pool}
        order = sims.argsort()[::-1]
        index_of_row = {r: i for i, r in self.row.items()}
        added = 0
        for row in order:
            sentence_index = index_of_row[int(row)]
            if sentence_index not in present and sentence_index in by_index:
                pool.append(by_index[sentence_index])
                present.add(sentence_index)
                added += 1
                if added >= top_k:
                    break
        for c in pool:
            row = self.row.get(c.sentence.index)
            if row is not None:
                c.extra["emb"] = float(sims[row])
        return pool

    def rerank(self, profile: Profile, pool: list[Candidate], top_k: int = 30) -> None:
        if top_k <= 0:
            return
        if not self.budget.allows(25_000) or not self.models.available("reranker"):
            if "rerank" not in self.log.skipped:
                self.log.skipped.append("rerank")
            return
        start = time.monotonic()
        query = profile.description
        chosen = sorted(pool, key=lambda c: fuse(c, profile), reverse=True)[:top_k]
        scores = self.models.rerank(query, [c.sentence.text for c in chosen])
        if scores is None:
            return
        for c, s in zip(chosen, scores):
            c.extra["rr"] = s
        self.log.timings["rerank"] = self.log.timings.get("rerank", 0.0) + time.monotonic() - start

    def verify(self, profile: Profile, pool: list[Candidate], target: str, top_k: int = 6) -> None:
        if top_k <= 0:
            return
        if not self.budget.allows(20_000) or not self.models.available("nli"):
            if "nli" not in self.log.skipped:
                self.log.skipped.append("nli")
            return
        start = time.monotonic()
        hypotheses = profile.hypotheses_for(target)
        chosen = sorted(pool, key=lambda c: fuse(c, profile), reverse=True)[:top_k]
        premises, hyps, owners = [], [], []
        for c in chosen:
            for h in hypotheses:
                premises.append(c.sentence.text)
                hyps.append(h)
                owners.append(c)
        probs = self.models.entailment(premises, hyps)
        if probs is None:
            return
        best: dict[int, float] = {}
        for c, p in zip(owners, probs):
            best[id(c)] = max(best.get(id(c), 0.0), p)
        for c in chosen:
            c.extra["nli"] = best.get(id(c), 0.0)
        self.log.timings["nli"] = self.log.timings.get("nli", 0.0) + time.monotonic() - start
