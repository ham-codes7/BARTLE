"""Failure-mode runs (PLAN §6.2): the module must return a contract-valid result on unusual inputs.

Each scenario builds a case the way the server would (kit code), runs the module in a fresh
process with the network blocked and 4 CPU threads, and checks:
  - the kit's validator accepts the result (for the scenario's own checklist),
  - the result uses exactly the checklist's criterion IDs, in any order,
  - every supporting_span is on its cited page, by a second extractor (pypdf),
  - total time stays under the 180 s limit, and peak memory is reported.

Usage (base environment's Python):
    apctt-env/base/bin/python dev/robustness.py            # all scenarios
    apctt-env/base/bin/python dev/robustness.py scanned big_300
"""

from __future__ import annotations

import argparse
import base64
import copy
import hashlib
import io
import json
import multiprocessing as mp
import os
import resource
import sys
import tempfile
import time
import traceback
from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402
from score import normalise  # noqa: E402

DEADLINE_MS = 180_000.0


# ---------------------------------------------------------------------------- building PDFs


def pdf_pages(case_id: str, start: int = 1, end: int | None = None) -> bytes:
    """Pages start..end (1-based, inclusive) of a public case PDF, as a new PDF."""
    from pypdf import PdfReader, PdfWriter

    reader = PdfReader(harness.PDF_DIR / f"{case_id}.pdf")
    writer = PdfWriter()
    for index in range(start - 1, end or len(reader.pages)):
        writer.add_page(reader.pages[index])
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def scanned_pdf(case_id: str, pages: int, scale: float = 2.0) -> bytes:
    """An image-only PDF: the first pages of a case rendered to pictures (no text layer)."""
    import pypdfium2 as pdfium

    document = pdfium.PdfDocument(str(harness.PDF_DIR / f"{case_id}.pdf"))
    images = [document[i].render(scale=scale).to_pil().convert("RGB") for i in range(pages)]
    buffer = io.BytesIO()
    images[0].save(buffer, format="PDF", save_all=True, append_images=images[1:], resolution=72 * scale)
    return buffer.getvalue()


def blank_pdf(pages: int) -> bytes:
    from pypdf import PdfWriter

    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=612, height=792)
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def request_case(case_id: str, contents: list[bytes], checklist_version: str, titles: list[str] | None = None) -> dict:
    """The server's request case for public case `case_id`, with the given PDFs as documents."""
    base = harness.manifest_case(case_id)
    documents = []
    for index, content in enumerate(contents):
        document = dict(base["document"])
        document["document_id"] = f"D{index + 1:03d}"
        if titles:
            document["title"] = titles[index]
        document["content_base64"] = base64.b64encode(content).decode("ascii")
        document["sha256"] = hashlib.sha256(content).hexdigest()
        documents.append(document)
    return {
        "schema_version": harness.SCHEMA_VERSION,
        "input_profile": "pdf_report",
        "checklist_version": checklist_version,
        "case_id": f"ROBUST-{case_id}",
        "assessment_as_of": None,
        "assessment_target": dict(base["assessment_target"]),
        "intended_application": base["intended_application"],
        "intended_environment": base["intended_environment"],
        "title": base["title"],
        "documents": documents,
        "sdg_targets": list(base["sdg_targets"]),
    }


def mutated_checklist() -> dict:
    """New IDs and version, reversed order, one reworded description, one extra criterion."""
    original = harness.checklist()
    criteria = []
    for number, criterion in enumerate(reversed(original["criteria"]), start=1):
        criteria.append({**criterion, "criterion_id": f"ZZ-{number:02d}"})
    criteria[3]["description"] = criteria[3]["description"].replace("(TRL", "(readiness level")
    criteria.append({
        "criterion_id": "ZZ-EXTRA",
        "description": "The report describes the uncertainty of the main results.",
    })
    return {**original, "version": "MUTATED-CHECKLIST-v9", "criteria": criteria}


# ---------------------------------------------------------------------------- scenarios


class Scenario:
    def __init__(self, name: str, build: Callable[[Path], tuple[dict, dict]], settings: dict | None = None,
                 env: dict | None = None, deadline_ms: float = DEADLINE_MS, note: str = "") -> None:
        self.name, self.build, self.settings, self.env = name, build, settings or {}, env or {}
        self.deadline_ms, self.note = deadline_ms, note


def _worker(case: dict, scratch: Path) -> dict:
    from apctt_contracts.pdf import local_worker_case

    return local_worker_case(case, scratch / "documents")


def _damage(path: str, keep: float) -> None:
    data = Path(path).read_bytes()
    Path(path).write_bytes(data[: int(len(data) * keep)])


def build_mutated(scratch: Path) -> tuple[dict, dict]:
    checklist = mutated_checklist()
    case = request_case("USGS-SDG-001", [pdf_pages("USGS-SDG-001")], checklist["version"])
    return _worker(case, scratch), checklist


def build_three_docs(scratch: Path) -> tuple[dict, dict]:
    checklist = harness.checklist()
    parts = [pdf_pages("USGS-SDG-001", 1, 8), pdf_pages("USGS-SDG-001", 9, 17), pdf_pages("USGS-SDG-001", 18)]
    case = request_case("USGS-SDG-001", parts, checklist["version"], ["Part 1", "Part 2", "Part 3"])
    return _worker(case, scratch), checklist


def build_big(scratch: Path) -> tuple[dict, dict]:
    """300 pages in 3 documents (the server's limits): the largest report plus two others."""
    checklist = harness.checklist()
    parts = [pdf_pages("USGS-SDG-075"), pdf_pages("USGS-SDG-065", 1, 66), pdf_pages("USGS-SDG-001")]
    case = request_case("USGS-SDG-075", parts, checklist["version"])
    return _worker(case, scratch), checklist


def build_damaged(scratch: Path) -> tuple[dict, dict]:
    """Passes the server's page count, then the file is cut short before the module reads it."""
    checklist = harness.checklist()
    case = _worker(request_case("USGS-SDG-001", [pdf_pages("USGS-SDG-001")], checklist["version"]), scratch)
    _damage(case["documents"][0]["path"], 0.3)
    return case, checklist


def build_one_damaged(scratch: Path) -> tuple[dict, dict]:
    checklist = harness.checklist()
    parts = [pdf_pages("USGS-SDG-001"), pdf_pages("USGS-SDG-012")]
    case = _worker(request_case("USGS-SDG-001", parts, checklist["version"]), scratch)
    _damage(case["documents"][1]["path"], 0.2)
    return case, checklist


def build_scanned(scratch: Path) -> tuple[dict, dict]:
    checklist = harness.checklist()
    case = request_case("USGS-SDG-001", [scanned_pdf("USGS-SDG-001", 12)], checklist["version"])
    return _worker(case, scratch), checklist


def build_blank(scratch: Path) -> tuple[dict, dict]:
    checklist = harness.checklist()
    case = request_case("USGS-SDG-001", [blank_pdf(5)], checklist["version"])
    return _worker(case, scratch), checklist


def build_normal(scratch: Path) -> tuple[dict, dict]:
    checklist = harness.checklist()
    case = request_case("USGS-SDG-001", [pdf_pages("USGS-SDG-001")], checklist["version"])
    return _worker(case, scratch), checklist


SCENARIOS = [
    Scenario("mutated_checklist", build_mutated, note="renamed IDs, reversed order, extra criterion"),
    Scenario("three_docs", build_three_docs, note="one report split into 3 documents"),
    Scenario("big_300", build_big, note="300 pages in 3 documents"),
    Scenario("damaged_pdf", build_damaged, note="file truncated after intake"),
    Scenario("one_damaged", build_one_damaged, note="2 documents, the second truncated"),
    Scenario("scanned", build_scanned, note="12 image-only pages (OCR path)"),
    Scenario("blank", build_blank, note="5 empty pages"),
    Scenario("no_models", build_normal, env={"APCTT_MODEL_STORE": "/nonexistent/model-store"},
             note="model store missing"),
    Scenario("tight_deadline", build_big, deadline_ms=45_000.0, note="300 pages with only 45 s left"),
]


# ---------------------------------------------------------------------------- running and checking


def _block_network() -> None:
    import socket

    def refuse(*_args, **_kwargs):
        raise OSError("network disabled for this test run")

    socket.socket.connect = refuse  # type: ignore[method-assign]
    socket.create_connection = refuse  # type: ignore[assignment]
    socket.getaddrinfo = refuse  # type: ignore[assignment]


def page_text(path: str, page: int) -> str:
    import logging

    from pypdf import PdfReader

    logging.getLogger("pypdf").setLevel(logging.ERROR)

    try:
        reader = PdfReader(path)
        return reader.pages[page - 1].extract_text() or ""
    except Exception:
        return ""


def spans_off_page(result: dict, case: dict, originals: dict[str, str]) -> tuple[list[str], int]:
    """Evidence spans that a second extractor cannot find on the cited page, and the number of
    spans on image-only pages (OCR text), which this check cannot verify."""
    bad, unverifiable = [], 0
    for criterion, items in (result.get("evidence_reference") or {}).items():
        for item in items:
            path = originals.get(item["document_id"])
            needle = normalise(item["supporting_span"])
            if not path or not needle:
                bad.append(f"{criterion}: no source for {item['document_id']}")
                continue
            hay = normalise(page_text(path, item["page"]))
            if not hay:
                unverifiable += 1
                continue
            if needle in hay:
                continue
            shingles = [needle[i: i + 30] for i in range(0, max(1, len(needle) - 29), 10)]
            if sum(s in hay for s in shingles) < 0.9 * len(shingles):
                bad.append(f"{criterion}: {item['document_id']} p{item['page']}")
    return bad, unverifiable


def run_scenario(scenario: Scenario) -> dict:
    for key, value in scenario.env.items():
        os.environ[key] = value
    _block_network()
    for var in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
        os.environ[var] = "4"
    record: dict[str, Any] = {"scenario": scenario.name, "note": scenario.note}
    try:
        with tempfile.TemporaryDirectory() as scratch:
            scratch_path = Path(scratch)
            case, checklist = scenario.build(scratch_path)
            # keep intact copies for the span check (damaged scenarios cut the module's files)
            originals = {}
            for document in case["documents"]:
                copy_path = scratch_path / f"check-{document['document_id']}.pdf"
                copy_path.write_bytes(Path(document["path"]).read_bytes())
                originals[document["document_id"]] = str(copy_path)
            pages = sum(d["page_count"] for d in case["documents"])
            t0 = time.monotonic()
            from participant_module.adapter import AssessmentModule

            module = AssessmentModule()
            config = harness.module_config(checklist, scenario.settings)
            module.load(config, harness.SUBMISSION / "assets")
            context = SimpleNamespace(
                run_id="robust", seed=42, time_budget_ms=int(scenario.deadline_ms), scratch_dir=scratch_path,
                remaining_ms=lambda: scenario.deadline_ms - (time.monotonic() - t0) * 1000.0,
            )
            result = module.assess(copy.deepcopy(case), context)
            elapsed = time.monotonic() - t0
            module.reset_case()
            module.close()
            issues = harness.validate(result, case, checklist)
            expected = sorted(c["criterion_id"] for c in checklist["criteria"])
            from participant_module import pipeline

            off_page, unverifiable = spans_off_page(result, case, originals)
            record.update(
                pages=pages,
                documents=len(case["documents"]),
                status=result.get("assessment_status"),
                trl=result.get("predicted_trl"),
                met=sum(1 for s in result.get("criterion_status", {}).values() if s == "met"),
                issues=issues,
                ids_match=sorted(result.get("criterion_status", {})) == expected,
                spans_off_page=off_page,
                spans_unverifiable=unverifiable,
                within_deadline=elapsed * 1000.0 < scenario.deadline_ms,
                seconds=round(elapsed, 1),
                peak_rss_mb=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 2**20, 1),
                skipped=(pipeline.LAST or {}).get("skipped"),
                rationale=result.get("trl_rationale", "")[:160],
            )
            record["ok"] = (not issues and record["ids_match"] and not record["spans_off_page"]
                            and record["within_deadline"])
    except Exception as error:
        record.update(ok=False, error=repr(error), trace=traceback.format_exc())
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("names", nargs="*", help="scenario names (default: all)")
    args = parser.parse_args()
    chosen = [s for s in SCENARIOS if not args.names or s.name in args.names]
    out_dir = harness.ROOT / "dev" / "out" / "robustness"
    out_dir.mkdir(parents=True, exist_ok=True)
    ctx = mp.get_context("spawn")
    records = []
    for scenario in chosen:  # one at a time, so timings and memory are not shared
        with ctx.Pool(processes=1, maxtasksperchild=1) as pool:
            record = pool.apply(run_scenario, (scenario,))
        records.append(record)
        flag = "PASS" if record.get("ok") else "FAIL"
        print(f"{flag} {record['scenario']:18s} {record.get('status')} trl={record.get('trl')} "
              f"met={record.get('met')} pages={record.get('pages')} {record.get('seconds')}s "
              f"rss={record.get('peak_rss_mb')}MB issues={record.get('issues')} "
              f"off_page={len(record.get('spans_off_page') or [])} ocr_spans={record.get('spans_unverifiable')} skipped={record.get('skipped')}"
              + (f" ERROR {record.get('error')}" if record.get("error") else ""), flush=True)
    (out_dir / "summary.json").write_text(json.dumps(records, indent=2) + "\n")
    failed = [r["scenario"] for r in records if not r.get("ok")]
    print(f"\n{len(records) - len(failed)}/{len(records)} passed" + (f"; failed: {failed}" if failed else ""))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
