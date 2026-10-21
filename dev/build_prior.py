"""Build my_submission/assets/trl_prior.json from the public sample-case manifest.

The prior is the organizer's estimated-TRL distribution of the 99 public cases, per target type,
with add-alpha smoothing over TRL 1-9 so that no level has zero probability. Types absent from the
public set (component, subsystem) use the pooled distribution.

Usage: python dev/build_prior.py
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "apctt-participant-kit-0.5.0-cpu" / "contracts" / "public-cases.json"
OUT = ROOT / "my_submission" / "assets" / "trl_prior.json"
ALPHA = 0.5


def distribution(counts: Counter[int]) -> list[float]:
    total = sum(counts.values()) + ALPHA * 9
    return [round((counts.get(trl, 0) + ALPHA) / total, 6) for trl in range(1, 10)]


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    by_type: dict[str, Counter[int]] = {}
    pooled: Counter[int] = Counter()
    for case in manifest["cases"]:
        trl = case["reference_labels"]["estimated_trl"]
        kind = case["assessment_target"]["type"]
        by_type.setdefault(kind, Counter())[trl] += 1
        pooled[trl] += 1

    prior = {
        "source": f"{MANIFEST.name} ({manifest['manifest_version']}, {manifest['created']}): "
        "organizer estimated TRL per public case; not expert labels",
        "alpha": ALPHA,
        "counts": {kind: dict(sorted(c.items())) for kind, c in sorted(by_type.items())},
        "pooled_counts": dict(sorted(pooled.items())),
        "by_type": {kind: distribution(c) for kind, c in sorted(by_type.items())},
        "pooled": distribution(pooled),
    }
    OUT.write_text(json.dumps(prior, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
