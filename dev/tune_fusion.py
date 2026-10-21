"""Tune evidence-fusion weights on the weak gold pages (data/silver_auto), with 2-fold CV.

For each case with weak gold pages, the pool of the ladder criterion at the organizer's TRL (saved
by run_cases in <case>.debug.json) is re-ranked with candidate weights; a case is a hit when one of
the first 3 distinct pages is a gold page.

Caveat: the weak gold pages were found by lexical (BM25) matching of the organizer's rationale, so
this objective is biased towards the lexical score. Results are a sanity check, not ground truth.

Usage: python dev/tune_fusion.py <run>
"""

from __future__ import annotations

import itertools
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

SILVER_AUTO = harness.ROOT / "data" / "silver_auto"


def sig(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def score(item: dict, w: dict) -> float:
    parts = [(w["lex"], item["lex"])]
    if "emb" in item:
        parts.append((w["emb"], max(0.0, item["emb"])))
    if "rr" in item:
        parts.append((w["rr"], sig(item["rr"])))
    if "nli" in item:
        parts.append((w["nli"], item["nli"]))
    total = sum(p for p, _ in parts) or 1.0
    value = sum(p * v for p, v in parts) / total
    return value * (1 - w["qual"] + w["qual"] * item["q"])


def hit(pool: list[dict], gold: set, w: dict) -> bool:
    ranked = sorted(pool, key=lambda it: score(it, w), reverse=True)
    pages: list = []
    for it in ranked:
        key = (it["doc"], it["page"])
        if key not in pages:
            pages.append(key)
        if len(pages) == 3:
            break
    return any(p in gold for p in pages)


def load(run: str) -> list[tuple[str, list[dict], set]]:
    out = []
    for path in sorted((harness.ROOT / "dev" / "out" / run).glob("*.debug.json")):
        case_id = path.name.replace(".debug.json", "")
        label_path = SILVER_AUTO / f"{case_id}.json"
        if not label_path.exists():
            continue
        label = json.loads(label_path.read_text())
        gold = {(g["document_id"], g["page"]) for g in label["gold_pages"]}
        pools = json.loads(path.read_text()).get("pools", {})
        pool = pools.get(f"trl{label['estimated_trl']}")
        if gold and pool:
            out.append((case_id, pool, gold))
    return out


def main() -> None:
    data = load(sys.argv[1])
    grid = {
        "lex": [0.2, 0.35, 0.5],
        "emb": [0.0, 0.15, 0.3],
        "rr": [0.0, 0.2, 0.4],
        "nli": [0.0, 0.3, 0.6],
        "qual": [0.2, 0.4],
    }
    combos = [dict(zip(grid, values)) for values in itertools.product(*grid.values())]
    folds = [[d for i, d in enumerate(data) if i % 2 == f] for f in (0, 1)]

    def rate(rows, w):
        return sum(hit(p, g, w) for _, p, g in rows) / max(1, len(rows))

    current = {"lex": 0.35, "emb": 0.15, "rr": 0.20, "nli": 0.30, "qual": 0.4}
    lexical = {"lex": 1.0, "emb": 0.0, "rr": 0.0, "nli": 0.0, "qual": 0.4}
    print(f"cases {len(data)}")
    print(f"current weights {current}: {rate(data, current):.3f}")
    print(f"lexical only: {rate(data, lexical):.3f}")
    for f in (0, 1):
        train, test = folds[f], folds[1 - f]
        best = max(combos, key=lambda w: (rate(train, w), -abs(w['lex'] - 0.35)))
        print(f"fold {f}: best on train {rate(train, best):.3f} -> test {rate(test, best):.3f}  {best}")
    ranked = sorted(combos, key=lambda w: rate(data, w), reverse=True)[:5]
    for w in ranked:
        print(f"all data {rate(data, w):.3f} {w}")


if __name__ == "__main__":
    main()
