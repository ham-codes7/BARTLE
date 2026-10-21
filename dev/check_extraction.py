"""Check page extraction on public cases: speed, empty pages, and that sentences can be found again
on the cited page by a different extractor (pdfplumber), the fabrication guard of part C.

Usage: apctt-env/base/bin/python dev/check_extraction.py [--all | ids] [--sample N]
"""

from __future__ import annotations

import argparse
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402
from score import span_on_page  # noqa: E402

from participant_module import pdf_text  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("ids", nargs="*")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--sample", type=int, default=15)
    args = parser.parse_args()
    rng = random.Random(0)
    total_checked = total_found = 0
    slow = []
    misses = []
    for case_id in harness.select_cases(args.ids, args.smoke, args.all):
        meta = harness.manifest_case(case_id)
        document = {"document_id": "D001", "path": str(harness.PDF_DIR / f"{case_id}.pdf"),
                    "page_count": meta["page_count"]}
        t0 = time.monotonic()
        docs = pdf_text.read_case({"documents": [document]}, allow_ocr=lambda: False)
        sentences = pdf_text.case_sentences(docs)
        elapsed = time.monotonic() - t0
        empty = sum(1 for p in docs[0].pages if sum(len(l) for l in p.lines) < pdf_text.MIN_PAGE_CHARS)
        sample = rng.sample(sentences, min(args.sample, len(sentences)))
        found = 0
        for s in sample:
            if span_on_page(case_id, s.page, s.text):
                found += 1
            else:
                misses.append((case_id, s.page, s.text[:120]))
        total_checked += len(sample)
        total_found += found
        slow.append((elapsed, case_id))
        print(f"{case_id}: {meta['page_count']}p {len(sentences)} sentences {elapsed:.2f}s "
              f"empty_pages={empty} found={found}/{len(sample)}", flush=True)
    print(f"\nspans found on page: {total_found}/{total_checked}")
    print("slowest:", sorted(slow, reverse=True)[:3])
    for miss in misses[:15]:
        print("MISS", miss)


if __name__ == "__main__":
    main()
