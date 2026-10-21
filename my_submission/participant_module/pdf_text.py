"""PDF page text: extraction, cleanup and sentence segmentation.

Page numbers are always PDF page indices (1..page_count), never printed page numbers.
Every sentence keeps the exact text the module will quote, so a supporting span is always a piece
of the cited page's own text (no generated text, no fabrication).
"""

from __future__ import annotations

import re
import unicodedata
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

# A page with fewer non-whitespace characters than this is treated as having no text layer.
MIN_PAGE_CHARS = 100
MAX_PAGE_CHARS = 60_000
MAX_SENTENCE_CHARS = 600
MIN_SENTENCE_CHARS = 25


@dataclass
class Page:
    document_id: str
    page: int  # 1-based PDF page index
    text: str  # cleaned page text, lines joined into paragraphs
    lines: list[str]
    ocr: bool = False
    role: str = "body"  # set by structure.py


@dataclass
class Sentence:
    document_id: str
    page: int
    index: int  # running index within the case
    text: str
    role: str = "body"
    features: dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentText:
    document_id: str
    page_count: int
    pages: list[Page]
    error: str | None = None


_REPLACEMENTS = {
    "￾": "-",  # pdfium marker for a hyphen at a line break
    "­": "",  # soft hyphen
    "‐": "-",
    "‑": "-",
    "‒": "-",
    " ": " ",
    " ": " ",
    " ": " ",
    "ﬁ": "fi",
    "ﬂ": "fl",
    "ﬀ": "ff",
    "ﬃ": "ffi",
    "ﬄ": "ffl",
    "\r": "\n",
}
_TRANSLATE = str.maketrans(_REPLACEMENTS)
_PAGE_NUMBER = re.compile(r"^(?:page\s+)?(?:\d{1,4}|[ivxlcdm]{1,7})$", re.I)
_DOT_LEADER = re.compile(r"\.{5,}|(?:\. ){4,}")
_NUMERIC_TOKEN = re.compile(r"^[\-–+±(]?[\d.,%/×x]+[)%]?$")


def normalise_text(text: str) -> str:
    text = text.translate(_TRANSLATE)
    text = unicodedata.normalize("NFC", text)
    return "".join(ch for ch in text if ch == "\n" or ch == "\t" or unicodedata.category(ch)[0] != "C")


def _line_key(line: str) -> str:
    """Key for running-header detection: digits removed, case and spaces folded."""
    return re.sub(r"\s+", " ", re.sub(r"\d+", "#", line.lower())).strip()


def extract_document(document: Mapping[str, Any]) -> DocumentText:
    """Raw per-page lines of one PDF with pypdfium2 (pypdf as fallback)."""
    doc_id = str(document["document_id"])
    page_count = int(document.get("page_count") or 0)
    raw: list[str] = []
    error = None
    try:
        import pypdfium2 as pdfium

        pdf = pdfium.PdfDocument(document["path"])
        try:
            for index in range(len(pdf)):
                page = pdf[index]
                textpage = page.get_textpage()
                raw.append(textpage.get_text_range() or "")
                textpage.close()
                page.close()
        finally:
            pdf.close()
    except Exception as exc:  # fall back to pypdf
        error = f"pdfium: {type(exc).__name__}"
        raw = []
        try:
            from pypdf import PdfReader

            reader = PdfReader(document["path"])
            raw = [(p.extract_text() or "") for p in reader.pages]
        except Exception as exc2:
            error += f"; pypdf: {type(exc2).__name__}"
    if page_count <= 0:
        page_count = len(raw)
    # Keep exactly page_count pages so evidence pages always exist in the server's view.
    raw = (raw + [""] * page_count)[:page_count]
    pages = []
    for number, text in enumerate(raw, start=1):
        text = normalise_text(text)[:MAX_PAGE_CHARS]
        lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
        pages.append(Page(doc_id, number, "", [line for line in lines if line]))
    return DocumentText(doc_id, page_count, pages, error)


def strip_running_lines(pages: Sequence[Page]) -> None:
    """Remove page-number lines and headers/footers repeated on many pages (in place)."""
    if not pages:
        return
    counts: Counter[str] = Counter()
    for page in pages:
        edge = page.lines[:3] + page.lines[-3:]
        counts.update({_line_key(line) for line in edge})
    threshold = max(3, int(0.3 * len(pages)))
    repeated = {key for key, n in counts.items() if n >= threshold and len(key) < 120}
    for page in pages:
        kept = []
        for position, line in enumerate(page.lines):
            at_edge = position < 3 or position >= len(page.lines) - 3
            if at_edge and (_PAGE_NUMBER.match(line) or _line_key(line) in repeated):
                continue
            kept.append(line)
        page.lines = kept


def _is_table_line(line: str) -> bool:
    tokens = line.split()
    if len(tokens) < 3:
        return False
    numeric = sum(1 for t in tokens if _NUMERIC_TOKEN.match(t))
    return numeric / len(tokens) >= 0.5


_STOPWORDS = {"a", "an", "and", "as", "at", "by", "for", "from", "in", "of", "on", "or", "the", "to", "with"}


def is_heading(line: str) -> bool:
    """A short title-case line without closing punctuation, such as 'Purpose and Scope'."""
    if not line or len(line) > 80 or line[-1] in ".,;:" or not line[0].isupper():
        return False
    words = re.findall(r"[A-Za-z][A-Za-z'’\-]*", line)
    if not 1 <= len(words) <= 10 or len(words) < len(line.split()) * 0.6:
        return False
    if words[-1].lower() in _STOPWORDS:
        return False  # "... National Park and Preserve in" continues on the next line
    content = [w for w in words if w.lower() not in _STOPWORDS]
    return bool(content) and sum(w[0].isupper() for w in content) / len(content) >= 0.8


# Section names that are headings wherever they appear as a line of their own.
SECTION_NAMES = re.compile(
    r"^(abstract|introduction|contents|figures|tables|conversion factors|abbreviations|"
    r"acknowledg(e)?ments|purpose and scope|background|methods?|results|discussion|"
    r"results and discussion|summary|conclusions?|summary and conclusions?|references( cited)?|"
    r"literature cited|appendix(es)?|appendices|glossary)$",
    re.I,
)


_APPENDIX_LINE = re.compile(r"^Appendix(es)?(\s+[0-9A-Z]{1,3}[.:\u2014–-]?)?(\s|$)")


def is_section_line(line: str) -> bool:
    """A section heading by name ('Abstract', 'References Cited', 'Appendix 1. Input files')."""
    return bool(SECTION_NAMES.match(line)) or (len(line) <= 100 and bool(_APPENDIX_LINE.match(line)))


def join_lines(lines: Sequence[str]) -> str:
    """Join wrapped lines into paragraphs; line-break hyphens are kept as printed.

    Headings stay on their own line so they never become part of a quoted sentence.
    """
    paragraphs: list[str] = []
    current = ""
    for position, line in enumerate(lines):
        following = lines[position + 1] if position + 1 < len(lines) else ""
        continues = following[:1].islower()  # next line carries on the same sentence
        mid_sentence = (
            bool(current)
            and not re.search(r"[.!?:][\"”')\]]?$", current)
            and not current.startswith("By ")  # author byline above the abstract
        )
        named = bool(SECTION_NAMES.match(line))
        heading = named or (
            (is_heading(line) or is_section_line(line)) and not mid_sentence and not continues
        )
        if _DOT_LEADER.search(line) or _is_table_line(line) or heading:
            if current:
                paragraphs.append(current)
                current = ""
            paragraphs.append(line)
            continue
        if not current:
            current = line
        elif current.endswith("-") and line[:1].islower():
            current = current + line  # "distributed-" + "parameter"
        else:
            current = current + " " + line
        if re.search(r"[.!?:][\"”')\]]?$", line) and len(line) < 60:
            paragraphs.append(current)
            current = ""
    if current:
        paragraphs.append(current)
    return "\n".join(paragraphs)


_ABBREVIATIONS = {
    "u.s", "e.g", "i.e", "et al", "al", "fig", "figs", "no", "nos", "vol", "p", "pp", "approx",
    "dr", "mr", "mrs", "ms", "st", "mt", "ft", "in", "jan", "feb", "mar", "apr", "jun", "jul",
    "aug", "sep", "sept", "oct", "nov", "dec", "inc", "co", "corp", "ltd", "dept", "eq", "eqs",
    "sec", "ch", "ed", "eds", "ref", "refs", "cf", "vs", "ca", "est", "max", "min", "avg",
    "sq", "mi", "km", "cm", "mm", "lb", "lbs", "oz", "gal", "yr", "yrs", "hr", "hrs", "nr",
}
# State abbreviations ("Valley Park, Mo.") are not listed: inside a sentence they are followed by
# "(" or a lowercase word, where the splitter never splits; before a capital they end a sentence.
_SPLIT = re.compile(r"(?<=[.!?])[\"”')\]]*\s+(?=[\"“]?[A-Z0-9])")


def split_sentences(paragraph: str) -> list[str]:
    paragraph = re.sub(r"\s+", " ", paragraph).strip()
    if not paragraph:
        return []
    out: list[str] = []
    start = 0
    for match in _SPLIT.finditer(paragraph):
        end = match.start()
        head = paragraph[start:end]
        last = re.search(r"([A-Za-z.]+)\.$", head)
        if last:
            token = last.group(1).lower().rstrip(".")
            if token in _ABBREVIATIONS or len(token) == 1 or re.fullmatch(r"(?:[a-z]\.)+[a-z]", token):
                continue  # "U.S. Geological", "S.L. Markstrom", "fig. 2"
        piece = paragraph[start:match.end()].strip()
        if piece:
            out.append(piece)
        start = match.end()
    tail = paragraph[start:].strip()
    if tail:
        out.append(tail)
    return out


def _long_sentence_pieces(sentence: str) -> list[str]:
    """Split an over-long run (often a table or list) at semicolons, then hard-wrap."""
    if len(sentence) <= MAX_SENTENCE_CHARS:
        return [sentence]
    pieces: list[str] = []
    for part in re.split(r"(?<=;)\s+", sentence):
        while len(part) > MAX_SENTENCE_CHARS:
            cut = part.rfind(" ", 0, MAX_SENTENCE_CHARS)
            cut = cut if cut > MAX_SENTENCE_CHARS // 2 else MAX_SENTENCE_CHARS
            pieces.append(part[:cut].strip())
            part = part[cut:].strip()
        if part:
            pieces.append(part)
    return pieces


def is_prose(text: str) -> bool:
    """Reject map labels, coordinate grids, equations and figure debris; keep running text."""
    if text.count("°") >= 2 or text.count("#") >= 3 or text.count('" "') >= 2:
        return False
    tokens = text.split()
    words = re.findall(r"[A-Za-z]{2,}", text)
    if len(words) < 4 or len(words) < 0.5 * len(tokens):
        return False
    lower = sum(1 for w in words if w.islower())
    return lower >= 0.5 * len(words)


def page_sentences(page: Page, start_index: int) -> list[Sentence]:
    sentences: list[Sentence] = []
    index = start_index
    for paragraph in page.text.split("\n"):
        if (_DOT_LEADER.search(paragraph) or _is_table_line(paragraph) or is_heading(paragraph)
                or is_section_line(paragraph)):
            continue
        for sentence in split_sentences(paragraph):
            for piece in _long_sentence_pieces(sentence):
                if len(piece) < MIN_SENTENCE_CHARS or not is_prose(piece):
                    continue
                sentences.append(Sentence(page.document_id, page.page, index, piece, page.role))
                index += 1
    return sentences


def ocr_page(path: str, page_number: int, engine: Any) -> str:
    """Text of one page by OCR (rapidocr-onnxruntime). Lines are returned top to bottom."""
    import numpy as np
    import pypdfium2 as pdfium

    pdf = pdfium.PdfDocument(path)
    try:
        page = pdf[page_number - 1]
        image = page.render(scale=2.0).to_numpy()
        page.close()
    finally:
        pdf.close()
    result, _ = engine(np.ascontiguousarray(image[:, :, :3]))
    if not result:
        return ""
    rows = sorted(result, key=lambda r: (round(r[0][0][1] / 12), r[0][0][0]))
    return "\n".join(str(r[1]) for r in rows)


def read_case(
    case: Mapping[str, Any],
    allow_ocr: Callable[[], bool] | None = None,
    max_ocr_pages: int = 6,
) -> list[DocumentText]:
    """Extract and clean every document of the case.

    OCR (about 4-10 s per page on CPU) is used only for documents that look scanned, where at
    least half of the pages have no text layer; in born-digital reports the empty pages are maps
    and photographs. It runs only while `allow_ocr()` is true and for at most `max_ocr_pages`.
    """
    documents: list[DocumentText] = []
    engine = None
    ocr_done = 0
    for document in case.get("documents", []):
        doc = extract_document(document)
        empty = [p for p in doc.pages if sum(len(line) for line in p.lines) < MIN_PAGE_CHARS]
        scanned = bool(doc.pages) and len(empty) >= 0.5 * len(doc.pages)
        for page in empty if scanned else []:
            if ocr_done >= max_ocr_pages:
                break
            if allow_ocr is not None and not allow_ocr():
                continue
            try:
                if engine is None:
                    from rapidocr_onnxruntime import RapidOCR

                    engine = RapidOCR()
                text = normalise_text(ocr_page(document["path"], page.page, engine))
                lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
                page.lines = [line for line in lines if line]
                page.ocr = True
                ocr_done += 1
            except Exception:
                ocr_done = max_ocr_pages  # OCR unavailable: stop trying
        strip_running_lines(doc.pages)
        for page in doc.pages:
            page.text = join_lines(page.lines)
        documents.append(doc)
    return documents


def case_sentences(documents: Sequence[DocumentText]) -> list[Sentence]:
    sentences: list[Sentence] = []
    for doc in documents:
        for page in doc.pages:
            sentences.extend(page_sentences(page, len(sentences)))
    return sentences
