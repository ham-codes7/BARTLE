"""Evidence page selection: best first, one item per page, free slots filled, sections spread."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "my_submission"))

from participant_module import evidence as ev  # noqa: E402
from participant_module.pdf_text import Sentence  # noqa: E402
from participant_module.retrieve import Candidate  # noqa: E402


def cand(page: int, score: float, role: str = "methods") -> Candidate:
    return Candidate(Sentence("D001", page, page, f"Sentence on page {page}.", role), score=score)


def pages(chosen):
    return [c.sentence.page for c in chosen]


def test_best_first_and_one_item_per_page():
    chosen = ev.select([cand(5, 0.5), cand(9, 0.9), cand(9, 0.8), cand(7, 0.6)])
    assert pages(chosen) == [9, 7, 5]


def test_free_slots_filled_only_when_asked():
    usable = [cand(3, 0.8)]
    fill = [cand(3, 0.8), cand(4, 0.35), cand(6, 0.25), cand(8, 0.1)]
    assert pages(ev.select(usable, fill=fill)) == [3]
    assert pages(ev.select(usable, fill=fill, fill_floor=0.2)) == [3, 4, 6]


def test_no_evidence_means_no_fill():
    assert ev.select([], fill=[cand(4, 0.9)], fill_floor=0.2) == []


def test_sections_spread_before_same_section_pages():
    usable = [cand(20, 0.9, "results"), cand(21, 0.85, "results"), cand(12, 0.7, "methods")]
    assert pages(ev.select(usable)) == [20, 21, 12]
    assert pages(ev.select(usable, diverse_ratio=0.6)) == [20, 12, 21]
