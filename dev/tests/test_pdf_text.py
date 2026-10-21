"""Unit tests for page cleanup and sentence segmentation (no PDFs needed)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "my_submission"))

from participant_module import pdf_text as pt  # noqa: E402


def test_abbreviations_do_not_split():
    text = ("The U.S. Geological Survey (USGS) calibrated the model (fig. 2). Data from S.L. "
            "Markstrom and others, 2008, were used near Valley Park, Mo. (USGS station 07019130), "
            "and at Arnold, Mo. The model was run.")
    sentences = pt.split_sentences(text)
    assert sentences == [
        "The U.S. Geological Survey (USGS) calibrated the model (fig. 2).",
        "Data from S.L. Markstrom and others, 2008, were used near Valley Park, Mo. (USGS station "
        "07019130), and at Arnold, Mo.",
        "The model was run.",
    ]


def test_headings_stay_separate_but_wrapped_names_do_not():
    lines = [
        "Abstract",
        "Libraries of maps were created in cooperation with the",
        "U.S. Army Corps of Engineers, Metropolitan St. Louis Sewer",
        "District, and the cities of Pacific and Eureka.",
        "Introduction",
        "The study began in 2016.",
    ]
    paragraphs = pt.join_lines(lines).split("\n")
    assert paragraphs[0] == "Abstract"
    assert paragraphs[1].startswith("Libraries of maps") and paragraphs[1].endswith("Eureka.")
    assert "Introduction" in paragraphs


def test_line_break_hyphen_and_ligatures():
    assert pt.normalise_text("distributed￾parameter eﬃcient") == "distributed-parameter efficient"
    assert pt.join_lines(["a modular, distributed-", "parameter model."]) == "a modular, distributed-parameter model."


BODIES = [f"{word} paragraph of the report." for word in
          ("First", "Second", "Third", "Fourth", "Fifth", "Sixth", "Seventh", "Eighth", "Ninth", "Tenth")]


def test_running_headers_and_page_numbers_removed():
    pages = [
        pt.Page("D001", n, "", ["Flood Maps of the River, Ohio, 2019", body, str(n)])
        for n, body in enumerate(BODIES, start=1)
    ]
    pt.strip_running_lines(pages)
    assert [page.lines for page in pages] == [[body] for body in BODIES]


def test_prose_filter():
    assert pt.is_prose("The model was calibrated to 16 flood events at the streamgage.")
    assert not pt.is_prose("81°24' 81°22' 40°46' 40°44' Base from U.S. Geological Survey")
    assert not pt.is_prose("# # # # NTR1–5 NTR1–4 NTR1–3")
    assert not pt.is_prose("MINNESOTA IOWA WISCONSIN ILLINOIS Austin Charles City Waverly")


def test_page_sentences_skip_headings_tables_and_contents():
    page = pt.Page("D001", 3, "", [])
    page.text = "\n".join([
        "Introduction",
        "Abstract ........................................ 1",
        "1,120 1,125 1,130 1,135 1,140",
        "The hydraulic model was calibrated to 16 flood events. Results matched within 0.5 foot.",
    ])
    texts = [s.text for s in pt.page_sentences(page, 0)]
    assert texts == ["The hydraulic model was calibrated to 16 flood events.", "Results matched within 0.5 foot."]


def test_title_case_first_line_of_paragraph_is_not_a_heading():
    lines = ["Abstract", "The New River Gorge National Park and Preserve in",
             "West Virginia receives more than 1 million visitors each year."]
    assert pt.join_lines(lines).split("\n") == [
        "Abstract",
        "The New River Gorge National Park and Preserve in West Virginia receives more than 1 million visitors each year.",
    ]
    assert pt.join_lines(["Hydraulic Model Calibration", "the model was calibrated."]).count("\n") == 0
