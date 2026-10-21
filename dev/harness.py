"""Shared helpers for running the module directly on public cases (no server).

Cases are built with the kit's own code (tools/get_public_cases.build_request and
apctt_contracts.pdf.local_worker_case), so the module receives exactly what the server would pass
it, and results are checked with the kit's validator (apctt_contracts.results.validate_result).

Run with the base environment's Python, so the module sees the same packages as at the event:
    apctt-env/base/bin/python dev/<script>.py
"""

from __future__ import annotations

import json
import os
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
KIT = ROOT / "apctt-participant-kit-0.5.0-cpu"
SUBMISSION = ROOT / "my_submission"
PDF_DIR = ROOT / "data" / "pdfs"
MODEL_STORE = ROOT / "models"
MANIFEST = KIT / "contracts" / "public-cases.json"
CHECKLIST = KIT / "contracts" / "checklist.official.json"
SCHEMA_VERSION = json.loads((KIT / "config" / "dev.json").read_text())["schema_version"]

for path in (SUBMISSION, KIT / "src", KIT / "tools"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
os.environ.setdefault("APCTT_MODEL_STORE", str(MODEL_STORE))


@lru_cache(maxsize=1)
def manifest() -> dict[str, Any]:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def checklist() -> dict[str, Any]:
    return json.loads(CHECKLIST.read_text(encoding="utf-8"))


def manifest_case(case_id: str) -> dict[str, Any]:
    for case in manifest()["cases"]:
        if case["case_id"] == case_id:
            return case
    raise KeyError(case_id)


def select_cases(ids: list[str], smoke: bool = False, every: bool = False) -> list[str]:
    if every:
        return [c["case_id"] for c in manifest()["cases"]]
    if smoke:
        return list(manifest()["smoke_cases"])
    out = []
    for text in ids:
        out.append(text if text.startswith("USGS-") else f"USGS-SDG-{int(text):03d}")
    return out


def worker_case(case_id: str, scratch: Path, checklist_data: dict[str, Any] | None = None) -> dict[str, Any]:
    """The case exactly as the server passes it to the module, with the PDF copied to scratch."""
    from apctt_contracts.pdf import local_worker_case
    from get_public_cases import build_request

    checklist_data = checklist_data or checklist()
    case = manifest_case(case_id)
    pdf = PDF_DIR / f"{case_id}.pdf"
    body = build_request(case, pdf.read_bytes(), SCHEMA_VERSION, checklist_data["version"])
    return local_worker_case(body["case"], scratch / "documents")


def module_config(checklist_data: dict[str, Any] | None = None, settings: dict[str, Any] | None = None) -> dict[str, Any]:
    checklist_data = checklist_data or checklist()
    return {
        "checklist": {"version": checklist_data["version"], "criteria": checklist_data["criteria"]},
        "module": {"settings": settings or {}},
        "compute": {"device": "cpu", "seed": 42},
    }


def validate(result: dict[str, Any], case: dict[str, Any], checklist_data: dict[str, Any] | None = None) -> list[tuple[str, str]]:
    from apctt_contracts.config import Checklist
    from apctt_contracts.results import validate_result

    checklist_data = checklist_data or checklist()
    issues = validate_result(result, case=case, checklist=Checklist.model_validate(checklist_data))
    return [(issue.path, issue.rule) for issue in issues]


def reference_trl(case_id: str) -> int:
    return manifest_case(case_id)["reference_labels"]["estimated_trl"]
