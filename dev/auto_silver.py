"""Weak page labels from the organizer's TRL rationale (data/silver_auto/<case_id>.json).

Every public case carries the organizer's one-sentence TRL rationale (public-cases.json,
reference_labels.rationale). It paraphrases what the report says about the TRL-defining work, so
the pages whose text best matches it are a weak reference for "where the evidence for the
TRL-level criterion is". The match is lexical (BM25 over pages, using the module's own extraction)
and only matches clearly above the rest of the document are kept.

These are NOT expert labels: they give one weak gold-page set per case, for the ladder criterion
at the organizer's estimated TRL. Used only to measure whether our evidence lands on the right
pages.

Usage: apctt-env/base/bin/python dev/auto_silver.py [--all | ids]
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

from participant_module import pdf_text, structure  # noqa: E402
from participant_module.retrieve import BM25, stems  # noqa: E402

OUT = harness.ROOT / "data" / "silver_auto"


def page_matches(case_id: str, rationale: str) -> list[tuple[int, float]]:
    meta = harness.manifest_case(case_id)
    document = {"document_id": "D001", "path": str(harness.PDF_DIR / f"{case_id}.pdf"),
                "page_count": meta["page_count"]}
    docs = pdf_text.read_case({"documents": [document]}, allow_ocr=lambda: False)
    structure.assign_case_roles(docs)
    pages = [p for p in docs[0].pages if p.role not in structure.NON_EVIDENCE_ROLES]
    index = BM25([stems(p.text) for p in pages])
    scores = index.scores(stems(rationale))
    return sorted(((p.page, s) for p, s in zip(pages, scores)), key=lambda x: -x[1])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("ids", nargs="*")
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    kept = 0
    case_ids = harness.select_cases(args.ids, every=args.all)
    for case_id in case_ids:
        meta = harness.manifest_case(case_id)
        labels = meta["reference_labels"]
        ranked = page_matches(case_id, labels["rationale"])
        if not ranked:
            continue
        values = [s for _, s in ranked]
        median = statistics.median(values)
        spread = statistics.pstdev(values) or 1.0
        # keep the top pages that stand out from the document (z >= 2), at most 3
        gold = [(p, s) for p, s in ranked[:3] if (s - median) / spread >= 2.0]
        record = {
            "case_id": case_id,
            "source": "organizer TRL rationale in public-cases.json, matched to pages by BM25; "
                      "weak label, not an expert label",
            "estimated_trl": labels["estimated_trl"],
            "rationale": labels["rationale"],
            "gold_pages": [{"document_id": "D001", "page": p, "z": round((s - median) / spread, 2)}
                           for p, s in gold],
            "top5": [[p, round(s, 2)] for p, s in ranked[:5]],
        }
        (OUT / f"{case_id}.json").write_text(json.dumps(record, indent=2) + "\n")
        kept += bool(gold)
        print(f"{case_id}: trl={labels['estimated_trl']} gold={[g['page'] for g in record['gold_pages']]} "
              f"top={record['top5'][:3]}")
    print(f"\n{kept}/{len(case_ids)} cases with a confident page match -> {OUT}")


if __name__ == "__main__":
    main()
