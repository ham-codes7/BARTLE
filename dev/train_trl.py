"""Train the TRL model (my_submission/assets/trl_model.json) from a dev run's case features.

Targets: the organizer's estimated TRL of the public cases (not expert labels). The model is a set
of cumulative logistic regressions P(TRL >= k | features) for the thresholds k with enough cases on
both sides; other thresholds follow the type prior. Exported as plain JSON coefficients.

Reports leave-one-out part-A scores (prior also rebuilt without the held-out case), so the number
is an honest estimate on unseen reports of the same kind:
    prior only  vs  prior + evidence model

Usage: apctt-env/base/bin/python dev/train_trl.py <run> [--C 0.3] [--write]
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

from participant_module.decide import model_posterior  # noqa: E402
from participant_module.safety import decode_trl  # noqa: E402

ALPHA = 0.5
KINDS = ["trl1", "trl2", "trl3", "trl4", "trl5", "trl6", "trl7", "trl8", "trl9", "requirements", "test_article"]
STATS = ["max", "cues"]  # NLI features added nothing in LOO (0.818 with and without)
FEATURES = ["is_system"] + [f"{k}_{s}" for k in KINDS for s in STATS]
THRESHOLDS = [5, 6, 7, 8]
MIN_PER_SIDE = 4


def a_score(trl: int, ref: int) -> float:
    d = abs(trl - ref)
    return 1.0 if d == 0 else 0.5 if d == 1 else 0.0


def prior_from(rows: list[dict]) -> dict:
    by_type: dict[str, Counter] = {}
    pooled: Counter = Counter()
    for r in rows:
        by_type.setdefault(r["type"], Counter())[r["ref"]] += 1
        pooled[r["ref"]] += 1

    def dist(c: Counter) -> list[float]:
        total = sum(c.values()) + ALPHA * 9
        return [(c.get(t, 0) + ALPHA) / total for t in range(1, 10)]

    return {"by_type": {k: dist(v) for k, v in by_type.items()}, "pooled": dist(pooled)}


def prior_vector(prior: dict, kind: str) -> list[float]:
    return prior["by_type"].get(kind) or prior["pooled"]


def fit(rows: list[dict], C: float) -> dict:
    X = np.array([[r["features"].get(f, 0.0) for f in FEATURES] for r in rows])
    mean = X.mean(axis=0)
    scale = X.std(axis=0)
    scale[scale == 0] = 1.0
    Z = (X - mean) / scale
    refs = np.array([r["ref"] for r in rows])
    thresholds = {}
    for k in THRESHOLDS:
        y = (refs >= k).astype(int)
        if y.sum() < MIN_PER_SIDE or (len(y) - y.sum()) < MIN_PER_SIDE:
            continue
        clf = LogisticRegression(C=C, max_iter=2000, class_weight=None)
        clf.fit(Z, y)
        thresholds[str(k)] = {"coef": clf.coef_[0].round(6).tolist(), "intercept": round(float(clf.intercept_[0]), 6)}
    return {"features": FEATURES, "mean": mean.round(6).tolist(), "scale": scale.round(6).tolist(),
            "thresholds": thresholds}


def load_rows(run: str) -> list[dict]:
    out_dir = harness.ROOT / "dev" / "out" / run
    rows = []
    for path in sorted(out_dir.glob("*.debug.json")):
        case_id = path.name.replace(".debug.json", "")
        debug = json.loads(path.read_text())
        if "features" not in debug:
            continue
        meta = harness.manifest_case(case_id)
        rows.append({"case_id": case_id, "features": debug["features"], "ref": meta["reference_labels"]["estimated_trl"],
                     "type": meta["assessment_target"]["type"]})
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("run")
    parser.add_argument("--C", type=float, default=0.3)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    rows = load_rows(args.run)
    prior_scores, model_scores, preds = [], [], Counter()
    for i, held in enumerate(rows):
        train = rows[:i] + rows[i + 1 :]
        prior = prior_vector(prior_from(train), held["type"])
        trl_p, _ = decode_trl(prior)
        prior_scores.append(a_score(trl_p, held["ref"]))
        model = fit(train, args.C)
        post = model_posterior(prior, held["features"], model)
        trl_m, _ = decode_trl(post)
        model_scores.append(a_score(trl_m, held["ref"]))
        preds[(trl_m, held["ref"])] += 1
    print(f"cases {len(rows)}  C={args.C}")
    print(f"LOO part A  prior only: {np.mean(prior_scores):.4f}   prior+evidence: {np.mean(model_scores):.4f}")
    print("(pred, ref) counts:", sorted(preds.items(), key=lambda x: -x[1])[:12])
    if args.write:
        model = fit(rows, args.C)
        model["source"] = (f"dev/train_trl.py on run {args.run}: {len(rows)} public cases, targets = organizer "
                           f"estimated TRL (not expert labels); C={args.C}")
        path = harness.SUBMISSION / "assets" / "trl_model.json"
        path.write_text(json.dumps(model, indent=1) + "\n")
        print("wrote", path)


if __name__ == "__main__":
    main()
