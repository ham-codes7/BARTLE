"""Time budget, TRL decoding helpers and the prior-only fallback result.

Scoring part A rewards an exact TRL with 1.0, a TRL off by one with 0.5 and an abstention with
0.25 (PROBLEM_DESCRIPTION §13.2). When the pipeline cannot run, a TRL decoded from the prior has a
much higher expected score than abstaining, so the fallback returns `completed` with low confidence
and every criterion marked `insufficient evidence`.
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

from participant_module.result import ABSTAINED, COMPLETED, INSUFFICIENT

# Internal hard stop: emit a result when this many ms of the case budget remain.
RESERVE_MS = 30_000


class Budget:
    """Wraps the worker clock. Falls back to a local clock when no context is given."""

    def __init__(self, context: Any = None, total_ms: float = 180_000.0) -> None:
        self._remaining: Callable[[], float]
        if context is not None and callable(getattr(context, "remaining_ms", None)):
            self._remaining = context.remaining_ms
        else:
            start = time.monotonic()
            self._remaining = lambda: total_ms - (time.monotonic() - start) * 1000.0

    def remaining_ms(self) -> float:
        try:
            return float(self._remaining())
        except Exception:
            return 0.0

    def usable_ms(self) -> float:
        """Time left before the internal hard stop."""
        return self.remaining_ms() - RESERVE_MS

    def allows(self, needed_ms: float) -> bool:
        return self.usable_ms() >= needed_ms


def load_prior(asset_root: Path) -> dict[str, Any] | None:
    try:
        return json.loads((Path(asset_root) / "trl_prior.json").read_text(encoding="utf-8"))
    except Exception:
        return None


def prior_for(prior: Mapping[str, Any] | None, target_type: str | None) -> list[float]:
    """Probability of TRL 1..9 for this target type (uniform if no prior is available)."""
    if prior:
        dist = prior.get("by_type", {}).get(target_type) or prior.get("pooled")
        if isinstance(dist, list) and len(dist) == 9 and sum(dist) > 0:
            total = float(sum(dist))
            return [float(p) / total for p in dist]
    return [1.0 / 9] * 9


def expected_scores(dist: Sequence[float]) -> list[float]:
    """Expected part-A score of answering TRL k (index k-1) under distribution `dist`."""
    scores = []
    for k in range(9):
        value = dist[k]
        if k > 0:
            value += 0.5 * dist[k - 1]
        if k < 8:
            value += 0.5 * dist[k + 1]
        scores.append(value)
    return scores


def decode_trl(dist: Sequence[float]) -> tuple[int, float]:
    """Return (TRL, expected score) that maximises the expected part-A score."""
    scores = expected_scores(dist)
    best = max(range(9), key=lambda k: (scores[k], dist[k]))
    return best + 1, scores[best]


def interval(dist: Sequence[float], trl: int, mass: float = 0.8) -> tuple[int, int]:
    """Smallest interval around `trl` that holds at least `mass` probability."""
    lower = upper = trl
    held = dist[trl - 1]
    while held < mass and (lower > 1 or upper < 9):
        left = dist[lower - 2] if lower > 1 else -1.0
        right = dist[upper] if upper < 9 else -1.0
        if left >= right:
            lower -= 1
            held += left
        else:
            upper += 1
            held += right
    return lower, upper


def fallback_result(
    case: Mapping[str, Any], criterion_ids: Sequence[str], checklist_version: str,
    prior: Mapping[str, Any] | None, reason: str,
) -> dict[str, Any]:
    """Prior-only result: valid, `completed`, every criterion without evidence."""
    target = case.get("assessment_target") or {}
    dist = prior_for(prior, target.get("type") if isinstance(target, Mapping) else None)
    trl, _ = decode_trl(dist)
    lower, upper = interval(dist, trl)
    note = f"Not assessed from the reports: {reason}"
    return {
        "schema_version": case.get("schema_version"),
        "checklist_version": checklist_version,
        "case_id": case.get("case_id"),
        "assessment_target": target,
        "assessment_status": COMPLETED,
        "predicted_trl": trl,
        "criterion_status": {cid: INSUFFICIENT for cid in criterion_ids},
        "evidence_reference": {cid: [] for cid in criterion_ids},
        "missing_evidence": {cid: note for cid in criterion_ids},
        "abstention_reason": None,
        "error_code": None,
        "confidence": round(min(dist[trl - 1], 0.5), 4),
        "uncertainty": {"kind": "trl_interval", "lower": lower, "upper": upper},
        "trl_rationale": (
            f"Prior-only estimate ({reason}): the most likely TRL for a "
            f"{target.get('type', 'target') if isinstance(target, Mapping) else 'target'} "
            "among comparable reports. No criterion was established from the documents."
        ),
    }


def abstained_result(
    case: Mapping[str, Any], criterion_ids: Sequence[str], checklist_version: str,
    reason: str, explanation: str,
) -> dict[str, Any]:
    """A genuine abstention, for example when no document text can be read."""
    return {
        "schema_version": case.get("schema_version"),
        "checklist_version": checklist_version,
        "case_id": case.get("case_id"),
        "assessment_target": case.get("assessment_target"),
        "assessment_status": ABSTAINED,
        "predicted_trl": None,
        "criterion_status": {cid: INSUFFICIENT for cid in criterion_ids},
        "evidence_reference": {cid: [] for cid in criterion_ids},
        "missing_evidence": {cid: explanation for cid in criterion_ids},
        "abstention_reason": reason,
        "error_code": None,
    }
