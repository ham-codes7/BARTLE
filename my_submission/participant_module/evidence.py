"""Evidence items for a criterion: verbatim spans from the cited page, best first.

Part B looks only at the first three distinct (document, page) items; part C samples the FIRST item
of a met criterion. So the strongest single sentence goes first, followed by the best sentences
from two other pages.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from participant_module.retrieve import Candidate

MAX_SPAN = 400
MAX_PAGES = 3


def clip(text: str, limit: int = MAX_SPAN) -> str:
    """Shorten at a word boundary; the result is still a substring of the page text."""
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    cut = text.rfind(" ", 0, limit)
    return text[: cut if cut > limit // 2 else limit]


ANCHOR_ROLES = ("abstract", "summary")
ANCHOR_MIN_RATIO = 0.5  # an anchor sentence must score at least half of the best sentence


def select(candidates: Sequence[Candidate], max_pages: int = MAX_PAGES) -> list[Candidate]:
    """Best sentence first; then the best abstract/summary sentence (reports state their key
    facts there, and assessors cite those pages); then the next best pages. One item per page."""
    ranked = sorted(candidates, key=lambda c: c.score, reverse=True)
    if not ranked:
        return []
    chosen: list[Candidate] = [ranked[0]]
    pages = {(ranked[0].sentence.document_id, ranked[0].sentence.page)}
    if ranked[0].sentence.role not in ANCHOR_ROLES:
        for candidate in ranked[1:]:
            key = (candidate.sentence.document_id, candidate.sentence.page)
            if candidate.sentence.role in ANCHOR_ROLES and key not in pages:
                if candidate.score >= ANCHOR_MIN_RATIO * ranked[0].score:
                    chosen.append(candidate)
                    pages.add(key)
                break
    for candidate in ranked[1:]:
        if len(chosen) >= max_pages:
            break
        key = (candidate.sentence.document_id, candidate.sentence.page)
        if key in pages:
            continue
        pages.add(key)
        chosen.append(candidate)
    return chosen


def items(chosen: Sequence[Candidate]) -> list[dict[str, Any]]:
    return [
        {
            "document_id": c.sentence.document_id,
            "page": c.sentence.page,
            "supporting_span": clip(c.sentence.text),
        }
        for c in chosen
    ]
