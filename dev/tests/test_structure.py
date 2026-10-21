"""Page-role assignment on a synthetic report."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "my_submission"))

from participant_module import pdf_text as pt  # noqa: E402
from participant_module import structure as st  # noqa: E402

PAGES = [
    ["Construction of a Flood Model for the River", "Scientific Investigations Report 2020–5000"],
    ["Contents", "Abstract 1", "Introduction 1", "Methods 3", "Results 5", "Summary 7",
     "References Cited 8"],
    ["Conversion Factors", "Multiply By To obtain", "foot (ft) 0.3048 meter (m)"],
    ["Construction of a Flood Model for the River", "By A. Author", "Abstract",
     "A hydraulic model was built and calibrated to 16 floods.", "Introduction",
     "Flooding is common in the basin."],
    ["Purpose and Scope", "This report describes the model."],
    ["Methods", "Cross sections were surveyed in 2019."],
    ["Results", "Simulated water levels were within 0.5 foot of observed levels."],
    ["The results show good agreement with observations at all gages."],
    ["Summary", "The model is ready for use by emergency planners."],
    ["References Cited", "Chow, V.T., 1959, Open-channel hydraulics: New York, McGraw-Hill."],
    ["Appendix 1. Model input files", "The input files are listed here for reference."],
]


def build() -> pt.DocumentText:
    pages = []
    for number, lines in enumerate(PAGES, start=1):
        page = pt.Page("D001", number, "", list(lines))
        page.text = pt.join_lines(page.lines)
        pages.append(page)
    return pt.DocumentText("D001", len(pages), pages)


def test_roles_follow_headings():
    document = build()
    st.assign_roles(document)
    assert [p.role for p in document.pages] == [
        "front_matter", "contents", "front_matter", "abstract", "introduction", "methods",
        "results", "results", "summary", "references", "appendix",
    ]


def test_heading_role_mapping():
    assert st.heading_role("References Cited") == "references"
    assert st.heading_role("Model Calibration and Validation") == "results"
    assert st.heading_role("Purpose and Scope") == "introduction"
    assert st.heading_role("Summary and Conclusions") == "summary"
    assert st.heading_role("Hydraulic Analyses") is None
