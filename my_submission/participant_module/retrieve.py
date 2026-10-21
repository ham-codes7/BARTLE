"""Candidate evidence sentences per criterion: BM25 lexical retrieval fused with domain cues,
page roles and target overlap.

BM25 is implemented here with numpy (no third-party retrieval package). Scores are combined per
sentence into a `Candidate` with its components kept, so later stages (embeddings, reranking,
NLI, calibration) can add to them and so every decision stays explainable.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass, field

from participant_module.criteria import Profile
from participant_module.pdf_text import Sentence
from participant_module.structure import NON_EVIDENCE_ROLES
from participant_module.target import TargetProfile, tokens

TRL_ASSERTION = re.compile(r"\b(TRL|technology readiness level)s?\b", re.I)


@dataclass
class Candidate:
    sentence: Sentence
    bm25: float = 0.0  # normalised 0..1 within the case and criterion
    cues: int = 0
    negatives: int = 0
    role: float = 0.0
    target: float = 0.0
    score: float = 0.0
    extra: dict[str, float] = field(default_factory=dict)


class BM25:
    def __init__(self, documents: Sequence[list[str]], k1: float = 1.4, b: float = 0.75) -> None:
        self.k1, self.b = k1, b
        self.docs = [Counter(d) for d in documents]
        self.lengths = [len(d) for d in documents]
        self.avg = (sum(self.lengths) / len(self.lengths)) if self.lengths else 1.0
        df: Counter[str] = Counter()
        for counter in self.docs:
            df.update(counter.keys())
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    def scores(self, query: Sequence[str]) -> list[float]:
        terms = [t for t in set(query) if t in self.idf]
        out = []
        for counter, length in zip(self.docs, self.lengths):
            s = 0.0
            norm = self.k1 * (1 - self.b + self.b * length / (self.avg or 1.0))
            for t in terms:
                f = counter.get(t)
                if f:
                    s += self.idf[t] * f * (self.k1 + 1) / (f + norm)
            out.append(s)
        return out


def is_trl_assertion(text: str) -> bool:
    """Sentences that talk about TRL numbers are never evidence (PROBLEM_DESCRIPTION §13.4)."""
    return bool(TRL_ASSERTION.search(text))


def eligible(sentence: Sentence) -> bool:
    return sentence.role not in NON_EVIDENCE_ROLES and not is_trl_assertion(sentence.text)


def _stem(token: str) -> str:
    for suffix in ("ations", "ation", "ments", "ment", "ings", "ing", "ies", "ed", "es", "s"):
        if token.endswith(suffix) and len(token) - len(suffix) >= 4:
            return token[: -len(suffix)]
    return token


def stems(text: str) -> list[str]:
    return [_stem(t) for t in tokens(text)]


@dataclass
class Retriever:
    sentences: list[Sentence]
    target: TargetProfile
    index: BM25 = field(init=False)

    def __post_init__(self) -> None:
        self.index = BM25([stems(s.text) for s in self.sentences])

    def candidates(self, profile: Profile, top_k: int = 40) -> list[Candidate]:
        query: list[str] = []
        for q in profile.queries:
            query.extend(stems(q))
        query.extend(_stem(k) for k in profile.keywords)
        if profile.kind in ("target_match", "test_article", "trl6", "trl7"):
            query.extend(_stem(t) for t in self.target.target_terms)
        raw = self.index.scores(query)
        top = max(raw) if raw else 0.0
        out: list[Candidate] = []
        for sentence, value in zip(self.sentences, raw):
            if not eligible(sentence):
                continue
            cues = sum(1 for p in profile.positive if p.search(sentence.text))
            negatives = sum(1 for p in profile.negative if p.search(sentence.text))
            candidate = Candidate(
                sentence=sentence,
                bm25=(value / top) if top > 0 else 0.0,
                cues=cues,
                negatives=negatives,
                role=profile.roles.get(sentence.role, 0.3),
                target=self.target.overlap(sentence.text),
            )
            candidate.score = combine(candidate, profile)
            out.append(candidate)
        out.sort(key=lambda c: c.score, reverse=True)
        return out[:top_k]


def sentence_quality(text: str) -> float:
    """1.0 for a complete, readable sentence; lower for fragments, captions and run-ons."""
    quality = 1.0
    if not re.search(r"[.!?][\"”')\]]?$", text):
        quality -= 0.3  # fragment (often a figure or table caption cut by layout)
    if len(text) < 50 or len(text) > 400:
        quality -= 0.2
    if re.match(r"^(Table|Figure|Fig\.)\s+[A-Z]?\d", text):
        quality -= 0.2
    digits = sum(ch.isdigit() for ch in text)
    if digits > 0.15 * len(text):
        quality -= 0.2
    return max(0.0, quality)


def combine(c: Candidate, profile: Profile) -> float:
    """Hand-set fusion for the lexical stage (replaced by a calibrated model later)."""
    cue = min(c.cues, 3) / 3.0
    if profile.kind == "target_match":
        score = 0.5 * c.target + 0.3 * c.role + 0.2 * c.bm25
    else:
        score = 0.40 * c.bm25 + 0.35 * cue + 0.15 * c.role + 0.10 * c.target - 0.2 * min(c.negatives, 2)
    return score * (0.6 + 0.4 * sentence_quality(c.sentence.text))
