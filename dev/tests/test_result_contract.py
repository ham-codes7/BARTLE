"""The module's own contract copy agrees with the kit's validator, and repair always yields a
result the kit accepts.

Run with the kit's environment (it has pytest and the kit sources):
    apctt-participant-kit-0.5.0-cpu/.venv/bin/python -m pytest dev/tests -q
"""

from __future__ import annotations

import copy
import json
import random
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
KIT = ROOT / "apctt-participant-kit-0.5.0-cpu"
sys.path[:0] = [str(ROOT / "my_submission"), str(KIT / "src")]

from apctt_contracts.config import Checklist  # noqa: E402
from apctt_contracts.results import validate_result  # noqa: E402
from participant_module import result as contract  # noqa: E402
from participant_module.safety import abstained_result, decode_trl, fallback_result, interval  # noqa: E402

CHECKLIST = json.loads((KIT / "contracts" / "checklist.official.json").read_text())
IDS = [c["criterion_id"] for c in CHECKLIST["criteria"]]
VERSION = CHECKLIST["version"]
CASE = {
    "schema_version": "apctt-pdf-example-v1",
    "input_profile": "pdf_report",
    "checklist_version": VERSION,
    "case_id": "TEST-001",
    "assessment_as_of": None,
    "assessment_target": {"target_id": "T1", "type": "technology", "description": "test target"},
    "intended_application": "test",
    "intended_environment": "test",
    "title": "test",
    "documents": [
        {"document_id": "D001", "title": "a", "document_date": None, "language": "en",
         "format": "pdf", "page_count": 10, "path": "/nonexistent/001.pdf"},
        {"document_id": "D002", "title": "b", "document_date": None, "language": "en",
         "format": "pdf", "page_count": 3, "path": "/nonexistent/002.pdf"},
    ],
}


def kit_issues(result):
    return validate_result(result, case=CASE, checklist=Checklist.model_validate(CHECKLIST))


def good_result():
    return {
        "schema_version": CASE["schema_version"],
        "checklist_version": VERSION,
        "case_id": CASE["case_id"],
        "assessment_target": dict(CASE["assessment_target"]),
        "assessment_status": "completed",
        "predicted_trl": 6,
        "criterion_status": {cid: "met" for cid in IDS},
        "evidence_reference": {
            cid: [{"document_id": "D001", "page": 2, "supporting_span": "Calibrated to 16 events."}]
            for cid in IDS
        },
        "missing_evidence": {},
        "abstention_reason": None,
        "error_code": None,
        "confidence": 0.6,
        "uncertainty": {"kind": "trl_interval", "lower": 5, "upper": 7},
        "trl_rationale": "Calibrated model used for flood mapping.",
        "criterion_rationale": {IDS[0]: "principles cited"},
    }


def mutations():
    """Each mutation breaks one or more result rules."""
    def m(fn):
        r = good_result()
        fn(r)
        return r

    return [
        m(lambda r: r.update(predicted_trl=10)),
        m(lambda r: r.update(predicted_trl="6")),
        m(lambda r: r.update(predicted_trl=True)),
        m(lambda r: r.update(assessment_status="abstained")),
        m(lambda r: r.update(assessment_status="maybe")),
        m(lambda r: r.update(abstention_reason="tired")),
        m(lambda r: r.update(error_code="X")),
        m(lambda r: r.update(confidence=float("nan"))),
        m(lambda r: r.update(confidence=1.5)),
        m(lambda r: r.update(confidence=None)),
        m(lambda r: r.update(uncertainty={"kind": "trl_interval", "lower": 7, "upper": 8})),
        m(lambda r: r.update(uncertainty={"kind": "x", "lower": 1, "upper": 2})),
        m(lambda r: r.update(extra_field=1)),
        m(lambda r: r.update(case_id="OTHER")),
        m(lambda r: r.update(checklist_version="v0")),
        m(lambda r: r["criterion_status"].pop(IDS[3])),
        m(lambda r: r["criterion_status"].update({IDS[0]: "yes"})),
        m(lambda r: r["criterion_status"].update({"UNKNOWN": "met"})),
        m(lambda r: r["evidence_reference"].update({IDS[1]: []})),
        m(lambda r: r["evidence_reference"].pop(IDS[2])),
        m(lambda r: r["evidence_reference"].update({IDS[4]: [{"document_id": "D009", "page": 1}]})),
        m(lambda r: r["evidence_reference"].update({IDS[4]: [{"document_id": "D002", "page": 4}]})),
        m(lambda r: r["evidence_reference"].update({IDS[4]: [{"document_id": "D002", "page": 0}]})),
        m(lambda r: r["evidence_reference"].update({IDS[4]: [{"document_id": "D001", "page": 2, "supporting_span": "  "}]})),
        m(lambda r: r["evidence_reference"].update({IDS[4]: [{"document_id": "D001", "page": 2, "x": 1}]})),
        m(lambda r: r["evidence_reference"].update({IDS[4]: "page 2"})),
        m(lambda r: r["criterion_status"].update({IDS[5]: "insufficient evidence"})),
        m(lambda r: r.update(missing_evidence={IDS[0]: ""})),
        m(lambda r: r.update(trl_rationale="  ")),
        m(lambda r: r.update(criterion_rationale={"BAD": "x"})),
        m(lambda r: r.update(criterion_status=[])),
        m(lambda r: r.pop("error_code")),
    ]


def test_good_result_is_valid_for_both_validators():
    r = good_result()
    assert kit_issues(r) == []
    assert contract.validate(r, CASE, IDS, VERSION) == []


@pytest.mark.parametrize("bad", mutations())
def test_mutation_detected_and_repaired(bad):
    assert kit_issues(bad), "mutation should break the kit contract"
    assert contract.validate(bad, CASE, IDS, VERSION), "our validator must also catch it"
    fixed = contract.finalize(bad, CASE, IDS, VERSION)
    assert kit_issues(fixed) == []
    assert contract.validate(fixed, CASE, IDS, VERSION) == []


def test_random_garbage_always_repairs_to_valid():
    rng = random.Random(0)
    values = [None, 0, 1, 6, -1, "", "met", "x", [], {}, [{}], 1.5, True,
              [{"document_id": "D001", "page": 3}], {"kind": "trl_interval", "lower": 2, "upper": 3}]
    fields = list(good_result()) + ["junk"]
    for _ in range(500):
        r = copy.deepcopy(good_result())
        for _ in range(rng.randint(1, 4)):
            r[rng.choice(fields)] = rng.choice(values)
        fixed = contract.finalize(r, CASE, IDS, VERSION)
        assert kit_issues(fixed) == [], (r, kit_issues(fixed))


def test_valid_result_passes_through_unchanged():
    r = good_result()
    assert contract.finalize(r, CASE, IDS, VERSION) == r


def test_fallback_and_abstention_are_valid():
    prior = json.loads((ROOT / "my_submission" / "assets" / "trl_prior.json").read_text())
    for kind in ("technology", "system", "component"):
        case = {**CASE, "assessment_target": {**CASE["assessment_target"], "type": kind}}
        r = fallback_result(case, IDS, VERSION, prior, "test")
        assert validate_result(r, case=case, checklist=Checklist.model_validate(CHECKLIST)) == []
    assert fallback_result(CASE, IDS, VERSION, prior, "t")["predicted_trl"] == 6
    assert fallback_result(CASE, IDS, VERSION, None, "t")["assessment_status"] == "completed"
    assert kit_issues(abstained_result(CASE, IDS, VERSION, "insufficient evidence", "no text")) == []


def test_decode_and_interval():
    dist = [0, 0, 0, 0.1, 0.1, 0.5, 0.3, 0, 0]
    trl, score = decode_trl(dist)
    assert trl == 6 and abs(score - 0.7) < 1e-9
    assert interval(dist, 6) == (6, 7) or interval(dist, 6)[0] <= 6 <= interval(dist, 6)[1]
    # a split between 5 and 7 favours 6 (two near misses) over either extreme
    assert decode_trl([0, 0, 0, 0, 0.45, 0.1, 0.45, 0, 0])[0] == 6
