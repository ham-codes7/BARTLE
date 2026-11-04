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


def select(
    candidates: Sequence[Candidate],
    max_pages: int = MAX_PAGES,
    fill: Sequence[Candidate] = (),
    fill_floor: float | None = None,
    anchor_ratio: float = ANCHOR_MIN_RATIO,
    diverse_ratio: float | None = None,
) -> list[Candidate]:
    """Best sentence first; then the best abstract/summary sentence (reports state their key
    facts there, and assessors cite those pages); then the next best pages. One item per page.

    Only the first three distinct pages count for page agreement and only the first item is
    checked as a quotation, so free page slots are filled from `fill` (weaker candidates, at
    least `fill_floor`) once the criterion has real evidence."""
    ranked = sorted(candidates, key=lambda c: c.score, reverse=True)
    if not ranked:
        return []
    chosen: list[Candidate] = [ranked[0]]
    pages = {(ranked[0].sentence.document_id, ranked[0].sentence.page)}
    if ranked[0].sentence.role not in ANCHOR_ROLES:
        for candidate in ranked[1:]:
            key = (candidate.sentence.document_id, candidate.sentence.page)
            if candidate.sentence.role in ANCHOR_ROLES and key not in pages:
                if candidate.score >= anchor_ratio * ranked[0].score:
                    chosen.append(candidate)
                    pages.add(key)
                break
    if diverse_ratio is not None:
        # experts tend to cite different parts of a report (abstract, methods, results)
        for candidate in ranked[1:]:
            if len(chosen) >= max_pages or candidate.score < diverse_ratio * ranked[0].score:
                break
            key = (candidate.sentence.document_id, candidate.sentence.page)
            if key not in pages and candidate.sentence.role not in {c.sentence.role for c in chosen}:
                pages.add(key)
                chosen.append(candidate)
    extra = sorted(fill, key=lambda c: c.score, reverse=True) if fill_floor is not None else []
    for candidate in [*ranked[1:], *(c for c in extra if c.score >= fill_floor)]:
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
