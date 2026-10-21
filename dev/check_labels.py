"""Check silver label files: structure, statuses, gold pages, and that each quote is on its first
gold page (pypdf text, independent of the module's extractor).

Usage: python dev/check_labels.py [case_id ...]   (default: every file in data/silver)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402
from score import span_on_page  # noqa: E402

SILVER = harness.ROOT / "data" / "silver"
STATUSES = {"met", "not met", "insufficient evidence"}


def check(path: Path) -> list[str]:
    problems: list[str] = []
    label = json.loads(path.read_text())
    case_id = label["case_id"]
    meta = harness.manifest_case(case_id)
    ids = [c["criterion_id"] for c in harness.checklist()["criteria"]]
    criteria = label.get("criteria", {})
    if set(criteria) != set(ids):
        problems.append(f"criteria keys differ from checklist: missing {set(ids) - set(criteria)}")
    for cid, entry in criteria.items():
        status = entry.get("status")
        if status not in STATUSES:
            problems.append(f"{cid}: bad status {status!r}")
            continue
        gold = entry.get("gold_pages", [])
        if status == "met":
            if not gold:
                problems.append(f"{cid}: met without gold pages")
                continue
            for g in gold:
                if not 1 <= g["page"] <= meta["page_count"]:
                    problems.append(f"{cid}: page {g['page']} out of range")
            quote = entry.get("quote", "")
            if not quote:
                problems.append(f"{cid}: met without quote")
            elif not span_on_page(case_id, gold[0]["page"], quote):
                problems.append(f"{cid}: quote not found on page {gold[0]['page']}")
        elif gold:
            problems.append(f"{cid}: gold pages given for status {status!r}")
    return problems


def main() -> None:
    paths = ([SILVER / f"{harness.select_cases([c])[0]}.json" for c in sys.argv[1:]]
             or sorted(SILVER.glob("USGS-*.json")))
    bad = 0
    for path in paths:
        problems = check(path)
        bad += bool(problems)
        print(f"{path.stem}: {'OK' if not problems else '; '.join(problems)}")
    print(f"\n{len(paths) - bad}/{len(paths)} label files OK")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
