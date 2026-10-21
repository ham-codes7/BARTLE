"""Joint TRL and criterion decisions.

The TRL ladder criteria (one per TRL level) and the TRL are decided together: experts label the
ladder consistently with their TRL, so the module never claims a ladder level above its own TRL.

TRL posterior over t = 1..9:
    log P(t) = log prior(t) + beta * sum_k [ k <= t ] log(eps + q_k) + [ k > t ] log(eps + 1 - q_k)
where q_k (0..1) is the evidence strength found for ladder level k. The TRL reported is the one
with the highest expected part-A score under this posterior (safety.decode_trl).
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from participant_module.criteria import Profile
from participant_module.result import INSUFFICIENT, MET, NOT_MET
from participant_module.safety import decode_trl, interval

EPS = 0.05


@dataclass
class Decision:
    trl: int
    expected_score: float
    posterior: list[float]
    lower: int
    upper: int


def trl_posterior(prior: Sequence[float], strengths: Mapping[int, float], beta: float) -> list[float]:
    logs = []
    for t in range(1, 10):
        value = math.log(max(prior[t - 1], 1e-9))
        for level, q in strengths.items():
            q = min(1.0, max(0.0, q))
            value += beta * (math.log(EPS + q) if level <= t else math.log(EPS + 1 - q))
        logs.append(value)
    top = max(logs)
    weights = [math.exp(v - top) for v in logs]
    total = sum(weights)
    return [w / total for w in weights]


def decide_trl(prior: Sequence[float], strengths: Mapping[int, float], beta: float) -> Decision:
    posterior = trl_posterior(prior, strengths, beta)
    trl, score = decode_trl(posterior)
    lower, upper = interval(posterior, trl)
    return Decision(trl, score, posterior, lower, upper)


def criterion_status(
    profile: Profile, strength: float, has_evidence: bool, trl: int, threshold: float,
    negative_only: bool,
) -> str:
    """met / not met / insufficient evidence for one criterion, given the decided TRL."""
    if profile.level is not None:
        if profile.level > trl:
            return NOT_MET if negative_only else INSUFFICIENT
        return MET if has_evidence else INSUFFICIENT
    if has_evidence and strength >= threshold:
        return MET
    return INSUFFICIENT


MISSING_TEXT = {
    "ladder_above": "The reports do not show the assessed target reaching this readiness level; "
    "the evidence found supports a lower level.",
    "no_evidence": "No passage in the reports was found that supports this criterion.",
    "weak": "Passages related to this criterion were found, but none states it clearly enough.",
}
