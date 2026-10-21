"""TRL decoding from the learned cumulative model."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "my_submission"))

from participant_module.decide import decide_trl_model, model_posterior  # noqa: E402

PRIOR = [0.01, 0.01, 0.01, 0.02, 0.12, 0.5, 0.29, 0.02, 0.02]
MODEL = {
    "features": ["f"],
    "mean": [0.0],
    "scale": [1.0],
    "thresholds": {"6": {"coef": [2.0], "intercept": 1.5}, "7": {"coef": [2.0], "intercept": -0.5}},
}


def test_posterior_is_a_distribution_and_monotone_in_evidence():
    low = model_posterior(PRIOR, {"f": -2.0}, MODEL)
    high = model_posterior(PRIOR, {"f": 2.0}, MODEL)
    for post in (low, high):
        assert abs(sum(post) - 1.0) < 1e-9 and min(post) >= 0.0
    assert sum(high[6:]) > sum(low[6:])  # more evidence -> more mass at TRL >= 7
    assert decide_trl_model(PRIOR, {"f": 2.0}, MODEL).trl >= decide_trl_model(PRIOR, {"f": -2.0}, MODEL).trl


def test_no_thresholds_falls_back_to_prior():
    post = model_posterior(PRIOR, {}, {"features": [], "mean": [], "scale": [], "thresholds": {}})
    assert [round(p, 6) for p in post] == [round(p / sum(PRIOR), 6) for p in PRIOR]


def test_crossing_thresholds_are_made_monotone():
    crossing = {"features": ["f"], "mean": [0.0], "scale": [1.0],
                "thresholds": {"6": {"coef": [0.0], "intercept": -3.0}, "7": {"coef": [0.0], "intercept": 3.0}}}
    post = model_posterior(PRIOR, {"f": 0.0}, crossing)
    assert min(post) >= 0.0 and abs(sum(post) - 1.0) < 1e-9
