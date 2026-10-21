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


def select(candidates: Sequence[Candidate], max_pages: int = MAX_PAGES) -> list[Candidate]:
    """Best candidate per page, for the top `max_pages` pages, in score order."""
    chosen: list[Candidate] = []
    pages: set[tuple[str, int]] = set()
    for candidate in sorted(candidates, key=lambda c: c.score, reverse=True):
        key = (candidate.sentence.document_id, candidate.sentence.page)
        if key in pages:
            continue
        pages.add(key)
        chosen.append(candidate)
        if len(chosen) >= max_pages:
            break
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
