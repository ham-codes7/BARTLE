"""Proxy scorer: the Stage 1 formulas of PROBLEM_DESCRIPTION §13 applied to a dev run.

  A (TRL decision, 45%): against the organizer's estimated TRL of each public case (not expert
    labels; the closest TRL reference we have).
  B (criterion evidence, 40%): against our silver labels in data/silver/<case_id>.json, only for
    the cases that have them.
  C (expert review, 15%): automatic stand-in for the experts. Every met claim's first evidence item
    is checked: is the supporting_span on the cited page (pypdf text, a different extractor from
    the module's pdfium; pdfplumber is not used because it interleaves two-column layouts) and is it more than a bare TRL assertion? A span not found counts as
    FABRICATED (-1), a missing span or a TRL-only sentence as 0, otherwise SUPPORTS (+1). Whether
    the span really supports the criterion is judged only through silver labels, so C here is an
    upper bound on the real C.

Usage: python dev/score.py <run> [<run> ...]   (run = folder name under dev/out)
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from functools import lru_cache
from pathlib import Path
from statistics import mean

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

SILVER = harness.ROOT / "data" / "silver"
TRL_ONLY = re.compile(r"\b(TRL|technology readiness level)s?\b", re.I)


def a_score(result: dict, reference: int) -> float:
    if result.get("assessment_status") == "completed":
        diff = abs(result["predicted_trl"] - reference)
        return 1.0 if diff == 0 else 0.5 if diff == 1 else 0.0
    if result.get("assessment_status") == "abstained":
        return 0.25
    return 0.0


def normalise(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).lower()
    text = text.replace("­", "").replace("-\n", "").replace("‐", "-").replace("‑", "-")
    return re.sub(r"[^a-z0-9]+", "", text)


@lru_cache(maxsize=64)
def _reader(case_id: str):
    from pypdf import PdfReader

    return PdfReader(harness.PDF_DIR / f"{case_id}.pdf")


@lru_cache(maxsize=4096)
def independent_page(case_id: str, page: int) -> str:
    reader = _reader(case_id)
    if not 1 <= page <= len(reader.pages):
        return ""
    return reader.pages[page - 1].extract_text() or ""


def span_on_page(case_id: str, page: int, span: str) -> bool:
    page_text = normalise(independent_page(case_id, page))
    needle = normalise(span)
    if not needle:
        return False
    if needle in page_text:
        return True
    # tolerate small extraction differences: 90% of 30-char shingles present
    shingles = [needle[i : i + 30] for i in range(0, max(1, len(needle) - 29), 10)]
    return sum(s in page_text for s in shingles) >= 0.9 * len(shingles)


def is_trl_only(span: str) -> bool:
    """A sentence whose substance is a TRL assertion (judged NOT_SUPPORTS by the experts)."""
    if not TRL_ONLY.search(span):
        return False
    rest = TRL_ONLY.sub(" ", span)
    rest = re.sub(r"\b(level|of|the|a|an|is|has|have|reached|achieved|at|to|\d)\b", " ", rest, flags=re.I)
    return len(re.findall(r"[A-Za-z]{3,}", rest)) < 6


def c_points(case_id: str, item: dict) -> tuple[int, str]:
    span = item.get("supporting_span")
    if not span:
        return 0, "no_span"
    if not span_on_page(case_id, item["page"], span):
        return -1, "fabricated"
    if is_trl_only(span):
        return 0, "trl_only"
    return 1, "supports"


def load_silver(case_id: str) -> dict | None:
    path = SILVER / f"{case_id}.json"
    return json.loads(path.read_text()) if path.exists() else None


def score_run(run: str) -> dict:
    out_dir = harness.ROOT / "dev" / "out" / run
    results = {
        p.stem: json.loads(p.read_text()) for p in sorted(out_dir.glob("USGS-*.json"))
    }
    a_values, baseline6, met_hits, notest_hits = [], [], [], []
    c_judgements: list[tuple[str, str, int, str]] = []
    per_criterion: dict[str, dict[str, int]] = {}
    for case_id, result in results.items():
        ref = harness.reference_trl(case_id)
        a_values.append(a_score(result, ref))
        baseline6.append(a_score({"assessment_status": "completed", "predicted_trl": 6}, ref))
        failed = result.get("assessment_status") == "failed"
        statuses = result.get("criterion_status") or {}
        evidence = result.get("evidence_reference") or {}
        for cid, status in statuses.items():
            if status == "met" and evidence.get(cid):
                points, label = c_points(case_id, evidence[cid][0])
                c_judgements.append((case_id, cid, points, label))
        silver = load_silver(case_id)
        if not silver:
            continue
        for cid, label in silver["criteria"].items():
            stats = per_criterion.setdefault(cid, {"tp": 0, "fn": 0, "fp": 0, "tn": 0, "page_miss": 0})
            said_met = not failed and statuses.get(cid) == "met"
            if label["status"] == "met":
                gold = {(g["document_id"], g["page"]) for g in label.get("gold_pages", [])}
                firsts: list[tuple[str, int]] = []
                for item in evidence.get(cid, []) if said_met else []:
                    key = (item["document_id"], item["page"])
                    if key not in firsts:
                        firsts.append(key)
                    if len(firsts) == 3:
                        break
                hit = said_met and any(k in gold for k in firsts)
                met_hits.append(1.0 if hit else 0.0)
                if said_met:
                    stats["tp"] += 1
                    stats["page_miss"] += 0 if hit else 1
                else:
                    stats["fn"] += 1
            else:
                notest_hits.append(0.0 if said_met else 1.0)
                stats["fp" if said_met else "tn"] += 1

    if met_hits and notest_hits:
        b = (2 * mean(met_hits) + mean(notest_hits)) / 3
    elif met_hits or notest_hits:
        b = mean(met_hits or notest_hits)
    else:
        b = None
    judged = [p for _, _, p, _ in c_judgements]
    c = max(0.0, sum(judged) / max(6, len(judged))) if judged else 0.0
    a = mean(a_values) if a_values else 0.0
    return {
        "run": run,
        "cases": len(results),
        "A": round(a, 4),
        "A_always6": round(mean(baseline6), 4) if baseline6 else None,
        "B": None if b is None else round(b, 4),
        "B_cases": sum(1 for cid in results if load_silver(cid)),
        "B_met_part": round(mean(met_hits), 4) if met_hits else None,
        "B_notest_part": round(mean(notest_hits), 4) if notest_hits else None,
        "C_upper_bound": round(c, 4),
        "C_labels": {label: sum(1 for *_, l in c_judgements if l == label)
                     for label in ("supports", "fabricated", "no_span", "trl_only")},
        "total_proxy": None if b is None else round(0.45 * a + 0.40 * b + 0.15 * c, 4),
        "per_criterion": per_criterion,
        "fabricated": [(cid_case, cid) for cid_case, cid, _, l in c_judgements if l == "fabricated"],
    }


def main() -> None:
    for run in sys.argv[1:]:
        report = score_run(run)
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
