"""Result construction and an in-module copy of the result contract (DATA_CONTRACT.md §2).

The kit's validator (apctt_contracts) is not part of the common base environment, so the module
cannot import it at the event. These checks mirror the result rules of DATA_CONTRACT.md §4.2;
`repair` turns any violation into the closest valid result so the server never records
INVALID_OUTPUT.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any

MET = "met"
NOT_MET = "not met"
INSUFFICIENT = "insufficient evidence"
STATUSES = (MET, NOT_MET, INSUFFICIENT)

COMPLETED = "completed"
ABSTAINED = "abstained"
FAILED = "failed"

ABSTENTION_REASONS = (
    "insufficient evidence",
    "conflicting evidence",
    "ambiguous scope",
    "out of scope",
)

REQUIRED_FIELDS = (
    "schema_version",
    "checklist_version",
    "case_id",
    "assessment_target",
    "assessment_status",
    "predicted_trl",
    "criterion_status",
    "evidence_reference",
    "missing_evidence",
    "abstention_reason",
    "error_code",
)
OPTIONAL_FIELDS = ("confidence", "uncertainty", "trl_rationale", "criterion_rationale")
EVIDENCE_FIELDS = ("document_id", "page", "supporting_span")

MAX_SPAN_CHARS = 600
MAX_TEXT_CHARS = 2000


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _nonblank(value: Any) -> bool:
    return isinstance(value, str) and value.strip() != ""


def page_counts(case: Mapping[str, Any]) -> dict[str, int]:
    """document_id -> page_count, as the server stores the case."""
    counts: dict[str, int] = {}
    for document in case.get("documents", []):
        count = document.get("page_count")
        counts[str(document.get("document_id"))] = count if _is_int(count) else 0
    return counts


def validate(
    result: Mapping[str, Any], case: Mapping[str, Any], criterion_ids: Sequence[str],
    checklist_version: str,
) -> list[tuple[str, str]]:
    """Return (path, rule) issues, following DATA_CONTRACT.md §2–4. Empty means valid."""
    issues: list[tuple[str, str]] = []
    if not isinstance(result, Mapping):
        return [("", "result_object")]
    for field in REQUIRED_FIELDS:
        if field not in result:
            return [(field, "result_required_field")]
    for field in result:
        if field not in REQUIRED_FIELDS and field not in OPTIONAL_FIELDS:
            issues.append((str(field), "result_unknown_field"))
    for field in ("schema_version", "case_id", "assessment_target"):
        if result[field] != case.get(field):
            issues.append((field, "result_matches_case"))
    if result["checklist_version"] != checklist_version:
        issues.append(("checklist_version", "result_matches_checklist"))

    status = result["assessment_status"]
    if status not in (COMPLETED, ABSTAINED, FAILED):
        issues.append(("assessment_status", "assessment_status_value"))
        return issues
    trl = result["predicted_trl"]
    if status == COMPLETED:
        if not (_is_int(trl) and 1 <= trl <= 9):
            issues.append(("predicted_trl", "strict_trl"))
    elif trl is not None:
        issues.append(("predicted_trl", "status_combination"))
    if status == ABSTAINED:
        if result["abstention_reason"] not in ABSTENTION_REASONS:
            issues.append(("abstention_reason", "abstention_reason_value"))
    elif result["abstention_reason"] is not None:
        issues.append(("abstention_reason", "status_combination"))
    if status == FAILED:
        if not _nonblank(result["error_code"]):
            issues.append(("error_code", "error_code_required"))
        for field in OPTIONAL_FIELDS:
            if field in result:
                issues.append((field, "failed_omits_optional"))
    elif result["error_code"] is not None:
        issues.append(("error_code", "status_combination"))

    for field in OPTIONAL_FIELDS:
        if field in result and result[field] is None:
            issues.append((field, "omit_instead_of_null"))
    if "confidence" in result and result["confidence"] is not None:
        value = result["confidence"]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not (
            math.isfinite(value) and 0 <= value <= 1
        ):
            issues.append(("confidence", "confidence_range"))
    if "uncertainty" in result and result["uncertainty"] is not None:
        u = result["uncertainty"]
        ok = (
            isinstance(u, Mapping)
            and set(u) == {"kind", "lower", "upper"}
            and u.get("kind") == "trl_interval"
            and _is_int(u.get("lower"))
            and _is_int(u.get("upper"))
            and 1 <= u["lower"] <= u["upper"] <= 9
        )
        if ok and status == COMPLETED and _is_int(trl):
            ok = u["lower"] <= trl <= u["upper"]
        if not ok:
            issues.append(("uncertainty", "uncertainty_interval"))
    if "trl_rationale" in result and result["trl_rationale"] is not None:
        if status != COMPLETED:
            issues.append(("trl_rationale", "trl_rationale_requires_completed"))
        elif not _nonblank(result["trl_rationale"]):
            issues.append(("trl_rationale", "rationale_nonblank_text"))

    maps = ("criterion_status", "evidence_reference", "missing_evidence")
    for field in maps:
        if not isinstance(result[field], Mapping):
            issues.append((field, "map_object"))
    if issues and any(rule == "map_object" for _, rule in issues):
        return issues

    known = set(criterion_ids)
    statuses = result["criterion_status"]
    evidence = result["evidence_reference"]
    missing = result["missing_evidence"]
    counts = page_counts(case)
    complete = status != FAILED
    for cid in statuses:
        if cid not in known:
            issues.append((f"criterion_status.{cid}", "criterion_known_id"))
        elif statuses[cid] not in STATUSES:
            issues.append((f"criterion_status.{cid}", "criterion_status_value"))
    for cid in missing:
        if cid not in known:
            issues.append((f"missing_evidence.{cid}", "criterion_known_id"))
        elif not _nonblank(missing[cid]):
            issues.append((f"missing_evidence.{cid}", "missing_evidence_text"))
    if complete:
        for cid in criterion_ids:
            if cid not in statuses:
                issues.append((f"criterion_status.{cid}", "criterion_status_complete"))
        if set(evidence) != known:
            issues.append(("evidence_reference", "evidence_keys_match_checklist"))
    elif not set(evidence) <= known:
        issues.append(("evidence_reference", "evidence_keys_match_checklist"))
    for cid, items in evidence.items():
        if not isinstance(items, list):
            issues.append((f"evidence_reference.{cid}", "evidence_list"))
            continue
        for index, item in enumerate(items):
            path = f"evidence_reference.{cid}[{index}]"
            if not isinstance(item, Mapping):
                issues.append((path, "evidence_item_object"))
                continue
            if any(key not in EVIDENCE_FIELDS for key in item):
                issues.append((path, "result_unknown_field"))
            if not isinstance(item.get("document_id"), str) or "page" not in item:
                issues.append((path, "evidence_item_required"))
                continue
            if item["document_id"] not in counts:
                issues.append((path, "evidence_locator_exists"))
            elif not (_is_int(item["page"]) and 1 <= item["page"] <= counts[item["document_id"]]):
                issues.append((path, "evidence_page_in_document"))
            if "supporting_span" in item and not _nonblank(item["supporting_span"]):
                issues.append((path, "supporting_span_nonblank"))
    if complete:
        for cid in criterion_ids:
            if statuses.get(cid) == MET and not evidence.get(cid):
                issues.append((f"evidence_reference.{cid}", "evidence_required_for_met"))
            if statuses.get(cid) == INSUFFICIENT and not _nonblank(missing.get(cid)):
                issues.append((f"missing_evidence.{cid}", "missing_evidence_required_for_insufficient"))

    rationale = result.get("criterion_rationale")
    if rationale is not None and "criterion_rationale" in result:
        if not isinstance(rationale, Mapping):
            issues.append(("criterion_rationale", "map_object"))
        else:
            for cid, text in rationale.items():
                if cid not in known:
                    issues.append((f"criterion_rationale.{cid}", "rationale_known_criterion"))
                elif not _nonblank(text):
                    issues.append((f"criterion_rationale.{cid}", "rationale_nonblank_text"))
    return issues


def clean_evidence(items: Any, counts: Mapping[str, int]) -> list[dict[str, Any]]:
    """Keep only well-formed evidence items whose page exists; trim spans."""
    cleaned: list[dict[str, Any]] = []
    if not isinstance(items, list):
        return cleaned
    for item in items:
        if not isinstance(item, Mapping):
            continue
        doc = item.get("document_id")
        page = item.get("page")
        if not isinstance(doc, str) or doc not in counts:
            continue
        if not (_is_int(page) and 1 <= page <= counts[doc]):
            continue
        entry: dict[str, Any] = {"document_id": doc, "page": page}
        span = item.get("supporting_span")
        if _nonblank(span):
            entry["supporting_span"] = span.strip()[:MAX_SPAN_CHARS]
        cleaned.append(entry)
    return cleaned


def repair(
    result: Mapping[str, Any], case: Mapping[str, Any], criterion_ids: Sequence[str],
    checklist_version: str,
) -> dict[str, Any]:
    """Rebuild `result` field by field into a contract-valid result.

    Unsupported `met` claims become `insufficient evidence`; malformed optional fields are
    dropped; an inconsistent status falls back to an abstention.
    """
    counts = page_counts(case)
    statuses_in = result.get("criterion_status") if isinstance(result, Mapping) else None
    evidence_in = result.get("evidence_reference") if isinstance(result, Mapping) else None
    missing_in = result.get("missing_evidence") if isinstance(result, Mapping) else None
    statuses_in = statuses_in if isinstance(statuses_in, Mapping) else {}
    evidence_in = evidence_in if isinstance(evidence_in, Mapping) else {}
    missing_in = missing_in if isinstance(missing_in, Mapping) else {}

    statuses: dict[str, str] = {}
    evidence: dict[str, list[dict[str, Any]]] = {}
    missing: dict[str, str] = {}
    for cid in criterion_ids:
        status = statuses_in.get(cid)
        status = status if status in STATUSES else INSUFFICIENT
        items = clean_evidence(evidence_in.get(cid), counts)
        if status == MET and not items:
            status = INSUFFICIENT
        statuses[cid] = status
        evidence[cid] = items
        if status == INSUFFICIENT:
            text = missing_in.get(cid)
            missing[cid] = (
                text.strip()[:MAX_TEXT_CHARS]
                if _nonblank(text)
                else "No passage in the reports was found that supports this criterion."
            )

    out: dict[str, Any] = {
        "schema_version": case.get("schema_version"),
        "checklist_version": checklist_version,
        "case_id": case.get("case_id"),
        "assessment_target": case.get("assessment_target"),
        "criterion_status": statuses,
        "evidence_reference": evidence,
        "missing_evidence": missing,
        "error_code": None,
    }
    status = result.get("assessment_status") if isinstance(result, Mapping) else None
    trl = result.get("predicted_trl") if isinstance(result, Mapping) else None
    if status == COMPLETED and _is_int(trl) and 1 <= trl <= 9:
        out.update(assessment_status=COMPLETED, predicted_trl=trl, abstention_reason=None)
        text = result.get("trl_rationale")
        if _nonblank(text):
            out["trl_rationale"] = text.strip()[:MAX_TEXT_CHARS]
    else:
        reason = result.get("abstention_reason") if isinstance(result, Mapping) else None
        out.update(
            assessment_status=ABSTAINED,
            predicted_trl=None,
            abstention_reason=reason if reason in ABSTENTION_REASONS else "insufficient evidence",
        )

    confidence = result.get("confidence") if isinstance(result, Mapping) else None
    if (
        isinstance(confidence, (int, float))
        and not isinstance(confidence, bool)
        and math.isfinite(confidence)
    ):
        out["confidence"] = min(1.0, max(0.0, float(confidence)))
    u = result.get("uncertainty") if isinstance(result, Mapping) else None
    if isinstance(u, Mapping) and _is_int(u.get("lower")) and _is_int(u.get("upper")):
        lower, upper = max(1, u["lower"]), min(9, u["upper"])
        if out["assessment_status"] == COMPLETED:
            lower, upper = min(lower, trl), max(upper, trl)
        if lower <= upper:
            out["uncertainty"] = {"kind": "trl_interval", "lower": lower, "upper": upper}
    rationale = result.get("criterion_rationale") if isinstance(result, Mapping) else None
    if isinstance(rationale, Mapping):
        kept = {
            cid: text.strip()[:MAX_TEXT_CHARS]
            for cid, text in rationale.items()
            if cid in statuses and _nonblank(text)
        }
        if kept:
            out["criterion_rationale"] = kept
    return out


def finalize(
    result: Mapping[str, Any], case: Mapping[str, Any], criterion_ids: Sequence[str],
    checklist_version: str,
) -> dict[str, Any]:
    """Return `result` if it is valid, otherwise its repaired form (which is always valid)."""
    if not validate(result, case, criterion_ids, checklist_version):
        return dict(result)
    return repair(result, case, criterion_ids, checklist_version)
