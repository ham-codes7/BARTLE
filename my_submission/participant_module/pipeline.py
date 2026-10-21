"""The assessment pipeline: read -> structure -> retrieve -> decide -> result.

Each stage checks the time budget; when time runs short the pipeline returns what it has, which
is always a complete, contract-valid result.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from participant_module import evidence as ev
from participant_module import pdf_text, structure
from participant_module.criteria import Profile
from participant_module.decide import (
    MISSING_TEXT, case_features, criterion_status, decide_trl, decide_trl_model,
)
from participant_module.result import COMPLETED, INSUFFICIENT, MET, NOT_MET
from participant_module.models import Models
from participant_module.retrieve import Candidate, Retriever, eligible, sentence_quality
from participant_module.semantic import Semantic, StageLog, fuse
from participant_module.safety import Budget, abstained_result, prior_for
from participant_module.target import build_target

DEFAULTS = {
    "beta": 1.0,  # weight of ladder evidence against the prior
    "theme_threshold": 0.45,  # strength needed to claim a non-ladder criterion met
    "evidence_floor": 0.30,  # a candidate weaker than this is not evidence
    "ocr_min_ms": 60_000,  # OCR only while this much usable time is left
    "semantic": True,  # embeddings, reranker and NLI stages
    "pool_lexical": 30,
    "pool_semantic": 25,
    "rerank_k": 0,  # reranker off: no gain on weak gold pages (dev/tune_fusion.py)
    "nli_k": 0,  # NLI off: no gain for ranking or for the TRL model (dev/train_trl.py)
}


# Debug information of the last case (read by the development harness only).
LAST: dict[str, Any] = {}


@dataclass
class CriterionOutcome:
    profile: Profile
    candidates: list[Candidate]
    chosen: list[Candidate]
    strength: float


def strength_of(candidates: Sequence[Candidate]) -> float:
    return max((c.score for c in candidates), default=0.0)


def run(
    case: Mapping[str, Any], profiles: Sequence[Profile], checklist_version: str,
    prior: Mapping[str, Any] | None, settings: Mapping[str, Any], budget: Budget,
    models: Models | None = None, trl_model: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    params = {**DEFAULTS, **{k: v for k, v in settings.items() if k in DEFAULTS}}
    criterion_ids = [p.criterion_id for p in profiles]

    documents = pdf_text.read_case(case, allow_ocr=lambda: budget.allows(params["ocr_min_ms"]))
    structure.assign_case_roles(documents)
    sentences = pdf_text.case_sentences(documents)
    if not sentences:
        return abstained_result(
            case, criterion_ids, checklist_version, "insufficient evidence",
            "No readable text was found in the reports.",
        )

    target = build_target(case)
    retriever = Retriever(sentences, target)
    log = StageLog()
    semantic = Semantic(models, budget, log) if models is not None else None
    if semantic is not None and params["semantic"]:
        semantic.embed_sentences([x for x in sentences if eligible(x)])
    outcomes: dict[str, CriterionOutcome] = {}
    for profile in profiles:
        everything = retriever.candidates(profile, top_k=None)
        pool = everything[: int(params["pool_lexical"])]
        if semantic is not None and params["semantic"]:
            pool = semantic.widen(profile, pool, everything, int(params["pool_semantic"]))
            semantic.rerank(profile, pool, int(params["rerank_k"]))
            semantic.verify(profile, pool, target.description or target.title, int(params["nli_k"]))
            for c in pool:
                c.score = fuse(c, profile)
        pool.sort(key=lambda c: c.score, reverse=True)
        floor = params["evidence_floor"]
        usable = [c for c in pool if c.score >= floor and c.negatives == 0]
        outcomes[profile.criterion_id] = CriterionOutcome(
            profile, pool, ev.select(usable), strength_of(pool)
        )

    target_type = target.target_type or None
    dist = prior_for(prior, target_type)
    features = case_features(outcomes.values(), target_type)
    if trl_model:
        decision = decide_trl_model(dist, features, trl_model)
    else:
        strengths = {
            o.profile.level: o.strength for o in outcomes.values() if o.profile.level is not None
        }
        decision = decide_trl(dist, strengths, float(params["beta"]))
    LAST.clear()
    LAST.update(features=features, timings=dict(log.timings), skipped=list(log.skipped),
                posterior=decision.posterior,
                pools={o.profile.kind: [
                    {"doc": c.sentence.document_id, "page": c.sentence.page, "role": c.sentence.role,
                     "lex": round(c.score_lexical, 4), "bm25": round(c.bm25, 4), "cues": c.cues,
                     "neg": c.negatives, "target": round(c.target, 3),
                     "q": round(sentence_quality(c.sentence.text), 2), "rolew": round(c.role, 2),
                     **{k: round(v, 4) for k, v in c.extra.items()}}
                    for c in o.candidates[:60]] for o in outcomes.values()})

    statuses: dict[str, str] = {}
    evidence: dict[str, list[dict[str, Any]]] = {}
    missing: dict[str, str] = {}
    rationale: dict[str, str] = {}
    for profile in profiles:
        if profile.kind == "target_match":
            continue
        o = outcomes[profile.criterion_id]
        negative_only = bool(o.candidates) and all(c.negatives > 0 for c in o.candidates[:5])
        status = criterion_status(
            profile, o.strength, bool(o.chosen), decision.trl, float(params["theme_threshold"]),
            negative_only,
        )
        statuses[profile.criterion_id] = status
        evidence[profile.criterion_id] = ev.items(o.chosen) if status == MET else []
        if status == INSUFFICIENT:
            if profile.level is not None and profile.level > decision.trl:
                missing[profile.criterion_id] = MISSING_TEXT["ladder_above"]
            else:
                missing[profile.criterion_id] = MISSING_TEXT["weak" if o.candidates else "no_evidence"]
        elif status == NOT_MET:
            rationale[profile.criterion_id] = "The reports describe this level as not reached or only planned."

    # Target match: met when other criteria are met with evidence that names the target.
    for profile in profiles:
        if profile.kind != "target_match":
            continue
        o = outcomes[profile.criterion_id]
        any_met = any(s == MET for s in statuses.values())
        on_target = [c for c in o.chosen if c.target >= 0.5]
        if any_met and on_target:
            statuses[profile.criterion_id] = MET
            evidence[profile.criterion_id] = ev.items(on_target)
        else:
            statuses[profile.criterion_id] = INSUFFICIENT
            missing[profile.criterion_id] = (
                "No passage was found that ties the evidence to the assessed target itself."
            )

    met_levels = sorted(
        o.profile.level for o in outcomes.values()
        if o.profile.level is not None and statuses.get(o.profile.criterion_id) == MET
    )
    trl_rationale = (
        f"TRL {decision.trl}: evidence found for readiness levels {met_levels or 'none'}; "
        f"the decision combines this evidence with the readiness levels typical of comparable "
        f"{target.target_type or 'technology'} reports (expected agreement {decision.expected_score:.2f})."
    )
    return {
        "schema_version": case.get("schema_version"),
        "checklist_version": checklist_version,
        "case_id": case.get("case_id"),
        "assessment_target": case.get("assessment_target"),
        "assessment_status": COMPLETED,
        "predicted_trl": decision.trl,
        "criterion_status": {cid: statuses[cid] for cid in criterion_ids},
        "evidence_reference": {cid: evidence.get(cid, []) for cid in criterion_ids},
        "missing_evidence": missing,
        "abstention_reason": None,
        "error_code": None,
        "confidence": round(decision.posterior[decision.trl - 1], 4),
        "uncertainty": {"kind": "trl_interval", "lower": decision.lower, "upper": decision.upper},
        "trl_rationale": trl_rationale,
        **({"criterion_rationale": rationale} if rationale else {}),
    }
