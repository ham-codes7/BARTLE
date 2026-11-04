"""Part-B proxy on the labelled reports for one or more module settings.

Each configuration runs the module on the 20 labelled cases (dev/run_cases.py) and is scored on
all of them and, separately, on the 5 cases labelled blind (without the pipeline's suggestions),
which guards against tuning to labels that were drafted from the pipeline's own output.

Usage (base environment's Python):
    apctt-env/base/bin/python dev/sweep_b.py base fill='fill_floor=0.2'
    apctt-env/base/bin/python dev/sweep_b.py --score-only full6
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SILVER = ROOT / "data" / "silver"
BLIND = {"USGS-SDG-012", "USGS-SDG-030", "USGS-SDG-060", "USGS-SDG-087", "USGS-SDG-096"}


def labelled() -> list[dict]:
    return [json.loads(p.read_text()) for p in sorted(SILVER.glob("USGS-*.json"))]


def first_pages(items: list[dict], n: int = 3) -> list[tuple[str, int]]:
    out: list[tuple[str, int]] = []
    for item in items:
        key = (item["document_id"], item["page"])
        if key not in out:
            out.append(key)
    return out[:n]


def score(run: str, cases: set[str] | None = None) -> dict:
    met_hits = met_total = notest_hits = notest_total = 0
    for label in labelled():
        if cases is not None and label["case_id"] not in cases:
            continue
        result = json.loads((ROOT / "dev" / "out" / run / f"{label['case_id']}.json").read_text())
        for cid, lab in label["criteria"].items():
            said = (result.get("criterion_status") or {}).get(cid)
            if lab["status"] == "met":
                met_total += 1
                gold = {(g["document_id"], g["page"]) for g in lab["gold_pages"]}
                pages = first_pages((result.get("evidence_reference") or {}).get(cid, []))
                met_hits += said == "met" and any(p in gold for p in pages)
            else:
                notest_total += 1
                notest_hits += said != "met"
    met = met_hits / met_total if met_total else 0.0
    notest = notest_hits / notest_total if notest_total else 0.0
    return {"B": round((2 * met + notest) / 3, 4), "met": round(met, 4), "notest": round(notest, 4)}


def run(name: str, settings: list[str]) -> None:
    ids = [label["case_id"] for label in labelled()]
    args = [sys.executable, str(ROOT / "dev" / "run_cases.py"), *ids, "--jobs", "3", "--run", f"sweep-{name}"]
    for item in settings:
        args += ["--set", item]
    subprocess.run(args, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main() -> None:
    argv = sys.argv[1:]
    score_only = "--score-only" in argv
    for spec in (a for a in argv if a != "--score-only"):
        name, _, rest = spec.partition("=")
        settings = [s for s in rest.strip("'\"").split(",") if s]
        if not score_only:
            run(name, settings)
        folder = name if score_only else f"sweep-{name}"
        print(f"{name:14s} all {score(folder)}  blind {score(folder, BLIND)}  {settings}", flush=True)


if __name__ == "__main__":
    main()
