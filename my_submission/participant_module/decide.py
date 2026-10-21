"""Joint TRL and criterion decisions.

The TRL ladder criteria (one per TRL level) and the TRL are decided together: experts label the
ladder consistently with their TRL, so the module never claims a ladder level above its own TRL.

TRL posterior over t = 1..9:
    log P(t) = log prior(t) + beta * sum_k [ k <= t ] log(eps + q_k) + [ k > t ] log(eps + 1 - q_k)
where q_k (0..1) is the evidence strength found for ladder level k. The TRL reported is the one
with the highest expected part-A score under this posterior (safety.decode_trl).
"""

from __future__ import annotations

import json
import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

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


# --------------------------------------------------------------------------- learned TRL model
def case_features(outcomes: Iterable[Any], target_type: str | None) -> dict[str, float]:
    """Case-level features keyed by criterion KIND (never by criterion ID)."""
    features: dict[str, float] = {"is_system": 1.0 if target_type == "system" else 0.0}
    for o in outcomes:
        kind = o.profile.kind
        pool = sorted(o.candidates, key=lambda c: c.score, reverse=True)
        top = [c.score for c in pool[:3]]
        features[f"{kind}_max"] = max(top, default=0.0)
        features[f"{kind}_top3"] = sum(top) / 3.0
        features[f"{kind}_nli"] = max((c.extra.get("nli", 0.0) for c in pool), default=0.0)
        features[f"{kind}_cues"] = float(max((c.cues for c in pool[:5]), default=0))
    return features


def load_trl_model(asset_root: Path) -> dict[str, Any] | None:
    try:
        return json.loads((Path(asset_root) / "trl_model.json").read_text(encoding="utf-8"))
    except Exception:
        return None


def model_posterior(prior: Sequence[float], features: Mapping[str, float], model: Mapping[str, Any]) -> list[float]:
    """P(TRL = t) from cumulative logistic models P(TRL >= k); unmodelled k follow the prior."""
    names = model["features"]
    x = [float(features.get(n, 0.0)) for n in names]
    mean, scale = model["mean"], model["scale"]
    z = [(v - m) / s if s else 0.0 for v, m, s in zip(x, mean, scale)]
    prior_ge = [sum(prior[k - 1 :]) for k in range(1, 10)]  # P(TRL >= k) under the prior
    ge = list(prior_ge)
    for key, spec in model["thresholds"].items():
        k = int(key)
        logit = spec["intercept"] + sum(c * v for c, v in zip(spec["coef"], z))
        ge[k - 1] = 1.0 / (1.0 + math.exp(-logit))
    ge[0] = 1.0
    for k in range(1, 9):  # monotone: P(>= k+1) <= P(>= k)
        ge[k] = min(ge[k], ge[k - 1])
    probs = [ge[k] - (ge[k + 1] if k < 8 else 0.0) for k in range(9)]
    total = sum(probs) or 1.0
    return [max(p, 0.0) / total for p in probs]


def decide_trl_model(prior: Sequence[float], features: Mapping[str, float], model: Mapping[str, Any]) -> Decision:
    posterior = model_posterior(prior, features, model)
    trl, score = decode_trl(posterior)
    lower, upper = interval(posterior, trl)
    return Decision(trl, score, posterior, lower, upper)
