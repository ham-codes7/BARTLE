"""Print a report's pages for labelling: page roles, then the cleaned text of evidence pages.

  python dev/label_view.py USGS-SDG-061                 # roles + text of all evidence pages
  python dev/label_view.py USGS-SDG-061 --pages 9 23    # only these pages
  python dev/label_view.py USGS-SDG-061 --grep "calibrat|real[- ]time"   # matching sentences
  python dev/label_view.py USGS-SDG-061 --candidates sem5   # the module's top pages per criterion

Without --candidates nothing from the module's ranking is shown (use that for blind labelling).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

from participant_module import pdf_text, structure  # noqa: E402


BRIEF_CUES = (
    r"purpose|calibrat|validat|verif|laborator|test(ed|ing)|accura|criteri|requirement|within \\d|"
    r"real[- ]time|operational|forecast|available (online|at|through)|web|deployed|installed|since \\d|"
    r"years of|release|approved|accepted|standard|limitation|demonstrat|applied|scenario|based on"
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("case_id")
    parser.add_argument("--pages", type=int, nargs="*")
    parser.add_argument("--grep")
    parser.add_argument("--candidates")
    parser.add_argument("--max-chars", type=int, default=4000)
    parser.add_argument("--brief", action="store_true",
                        help="abstract and summary pages in full, plus sentences matching the criterion cues")
    args = parser.parse_args()
    case_id = harness.select_cases([args.case_id])[0]
    meta = harness.manifest_case(case_id)
    document = {"document_id": "D001", "path": str(harness.PDF_DIR / f"{case_id}.pdf"),
                "page_count": meta["page_count"]}
    docs = pdf_text.read_case({"documents": [document]}, allow_ocr=lambda: False)
    structure.assign_case_roles(docs)
    doc = docs[0]
    print(f"# {case_id}: {meta['title']}")
    print(f"target ({meta['assessment_target']['type']}): {meta['assessment_target']['description']}")
    print(f"application: {meta['intended_application']}")
    print(f"environment: {meta['intended_environment']}")
    print(f"pages: {structure.roles_summary(doc)}\n")

    if args.candidates:
        debug = json.loads((harness.ROOT / "dev" / "out" / args.candidates / f"{case_id}.debug.json").read_text())
        for kind, pool in debug.get("pools", {}).items():
            pages: list[int] = []
            for item in pool:
                if item["page"] not in pages:
                    pages.append(item["page"])
            print(f"{kind}: {pages[:8]}")
        return

    if args.brief:
        for page in doc.pages:
            if page.role in ("abstract", "summary"):
                print(f"===== page {page.page} [{page.role}] =====")
                print(page.text[:6000])
        args.grep = BRIEF_CUES
        print("\n----- cue matches -----")

    if args.grep:
        pattern = re.compile(args.grep, re.I)
        for s in pdf_text.case_sentences(docs):
            if pattern.search(s.text):
                print(f"p{s.page} [{s.role}] {s.text}")
        return

    wanted = set(args.pages or [])
    for page in doc.pages:
        if wanted and page.page not in wanted:
            continue
        if not wanted and page.role in structure.NON_EVIDENCE_ROLES:
            continue
        text = page.text.strip()
        if not text:
            continue
        print(f"===== page {page.page} [{page.role}] =====")
        print(text[: args.max_chars])
        print()


if __name__ == "__main__":
    main()
