"""Write a human-readable spot-check sheet for silver label files (data/silver/REVIEW.md).

Usage: python dev/review_sheet.py USGS-SDG-030 USGS-SDG-096 ...
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

SILVER = harness.ROOT / "data" / "silver"
OUT = SILVER / "REVIEW.md"


def main() -> None:
    criteria = {c["criterion_id"]: c["description"] for c in harness.checklist()["criteria"]}
    lines = [
        "# Silver label spot-check",
        "",
        "For each criterion: read the description, open the PDF at the page number shown",
        "(the PDF viewer's page number, not the number printed on the page), decide yourself, then",
        "compare with the draft. Mark **agree** or **disagree**, and if you disagree write what you",
        "would label and which page proves it.",
        "",
        "PDFs: `data/pdfs/<case_id>.pdf`",
        "",
    ]
    for case in sys.argv[1:]:
        case_id = harness.select_cases([case])[0]
        label = json.loads((SILVER / f"{case_id}.json").read_text())
        meta = harness.manifest_case(case_id)
        lines += [
            f"## {case_id}: {meta['title']}",
            "",
            f"- Target: {meta['assessment_target']['description']} ({meta['assessment_target']['type']})",
            f"- Organizer TRL estimate: {meta['reference_labels']['estimated_trl']}; draft labeller's opinion: {label.get('trl_opinion')}",
            f"- Draft mode: {label.get('mode')}",
            "",
            "| Criterion | Draft | Pages | Agree? | Your label / page |",
            "|---|---|---|---|---|",
        ]
        for cid, entry in label["criteria"].items():
            pages = ", ".join(str(g["page"]) for g in entry.get("gold_pages", [])) or "-"
            lines.append(f"| {cid} | {entry['status']} | {pages} |  |  |")
        lines.append("")
        for cid, entry in label["criteria"].items():
            lines.append(f"**{cid}**: {criteria[cid]}")
            lines.append("")
            lines.append(f"- Draft: **{entry['status']}**. {entry.get('note', '')}")
            if entry.get("quote"):
                lines.append(f"- Quote (page {entry['gold_pages'][0]['page']}): \"{entry['quote']}\"")
            lines.append("")
        lines.append("---")
        lines.append("")
    OUT.write_text("\n".join(lines) + "\n")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
