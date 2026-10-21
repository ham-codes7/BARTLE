"""Document structure of report-style PDFs: a role for every page.

Roles:
  front_matter  cover, credits, conversion factors, abbreviations (before the abstract)
  contents      contents / list of figures / list of tables pages
  abstract      the abstract
  introduction  introduction, purpose and scope, background, study area, previous studies
  methods       data, methods, model development and construction
  results       results, calibration, validation, evaluation, application, accuracy
  summary       summary, conclusions
  references    references cited
  appendix      appendixes, glossary, supplemental tables
  body          any other section of the main text

Roles follow the section headings found on the pages (heading lines are kept separate by
pdf_text.join_lines); a page takes the role of the last heading seen, so a role carries forward
over pages without headings.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

from participant_module.pdf_text import _DOT_LEADER, DocumentText, Page, is_heading, is_section_line

EVIDENCE_ROLES = ("abstract", "introduction", "methods", "results", "summary", "body", "appendix")
NON_EVIDENCE_ROLES = ("front_matter", "contents", "references")

_ROLE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("references", re.compile(r"^(references( cited)?|literature cited|selected references|bibliography)$", re.I)),
    ("abstract", re.compile(r"^(abstract|executive summary)$", re.I)),
    ("summary", re.compile(r"^(summary|conclusions?|summary and conclusions?|concluding remarks)\b", re.I)),
    ("appendix", re.compile(r"^(appendix(es)?|appendices|glossary|supplemental (information|data|tables?))\b", re.I)),
    ("introduction", re.compile(
        r"^(introduction|purpose and scope|background|previous (studies|investigations|work)|"
        r"description of (the )?(study area|study reach|basin|watershed)|study area|scope)\b", re.I)),
    ("results", re.compile(
        r"\b(results?|calibration|validation|verification|evaluation|accuracy|performance|"
        r"comparison|application|uncertainty|limitations|assessment|testing|tests?|findings)\b", re.I)),
    ("methods", re.compile(
        r"\b(methods?|methodology|approach|data( collection| sources)?|model (development|construction|design)|"
        r"development of|construction of|design of|computation|procedures?|instrumentation|"
        r"installation|implementation|description of)\b", re.I)),
]
_CONTENTS = re.compile(r"^(contents|figures|tables|illustrations|list of (figures|tables))$", re.I)
_FRONT = re.compile(
    r"^(conversion factors|abbreviations|acknowledg(e)?ments|datum|supplemental information|foreword|preface)\b",
    re.I,
)


def heading_lines(page: Page) -> list[str]:
    return [line for line in page.text.split("\n") if is_heading(line) or is_section_line(line)]


def heading_role(heading: str) -> str | None:
    text = heading.strip().rstrip(":")
    if _CONTENTS.match(text):
        return "contents"
    if _FRONT.match(text):
        return "front_matter"
    for role, pattern in _ROLE_PATTERNS:
        if pattern.search(text):
            return role
    return None


def _is_contents_page(page: Page) -> bool:
    lines = page.text.split("\n")
    leaders = sum(1 for line in lines if _DOT_LEADER.search(line))
    if leaders >= 3:
        return True
    # Contents without dot leaders: "Contents" at the top, followed by entries with page numbers.
    top = [line.strip().lower() for line in lines[:3]]
    return "contents" in top and len(re.findall(r"[A-Za-z]\s+(?:\d{1,3}|[ivx]{1,5})\b", page.text)) >= 5


def assign_roles(document: DocumentText) -> None:
    """Set `page.role` for every page of the document (in place)."""
    pages = document.pages
    if not pages:
        return
    abstract_at = None
    for page in pages:
        if _is_contents_page(page):
            continue
        if any(re.fullmatch(r"(abstract|executive summary)", h.strip(), re.I) for h in heading_lines(page)):
            abstract_at = page.page
            break
    if abstract_at is None:
        # No abstract heading: the first non-contents page with real running text starts the body.
        for page in pages:
            if not _is_contents_page(page) and len(page.text) > 1500 and page.page > 1:
                abstract_at = page.page
                break
        abstract_at = abstract_at or 1

    role = "front_matter"
    for page in pages:
        if _is_contents_page(page):
            page.role = "contents"
            continue
        if page.page < abstract_at:
            page.role = "front_matter"
            continue
        headings = heading_lines(page)
        page_role = None
        if page.page == abstract_at and role == "front_matter":
            role = page_role = "abstract"
            # Title lines above the abstract heading are not sections.
            for position, heading in enumerate(headings):
                if re.fullmatch(r"(abstract|executive summary)", heading.strip(), re.I):
                    headings = headings[position + 1 :]
                    break
        for heading in headings:
            found = heading_role(heading)
            if found in ("contents", "front_matter"):
                continue  # such headings after the abstract are captions or appendix lists
            if found:
                if role == "references" and found not in ("appendix",):
                    continue  # titles inside the reference list are not sections
                page_role = page_role or found  # the page starts in the first section it shows
                role = found
            elif role in ("abstract", "introduction") and len(heading) > 3:
                role = "body" if role == "abstract" else role
        # A page takes the first section it shows (the abstract page stays "abstract").
        page.role = page_role or role


def assign_case_roles(documents: Sequence[DocumentText]) -> None:
    for document in documents:
        assign_roles(document)


def roles_summary(document: DocumentText) -> str:
    """Compact run-length string of page roles, for debugging: 'front_matter:1-5 abstract:6 ...'."""
    out: list[str] = []
    start = 1
    for index, page in enumerate(document.pages):
        last = index == len(document.pages) - 1
        if last or document.pages[index + 1].role != page.role:
            span = f"{start}" if start == page.page else f"{start}-{page.page}"
            out.append(f"{page.role}:{span}")
            start = page.page + 1
    return " ".join(out)
