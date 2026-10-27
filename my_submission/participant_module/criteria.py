"""Criterion profiles built at load time from the configured checklist.

Criterion IDs are never hard-coded. Each criterion's description decides its KIND: a TRL level
parsed from "(TRL k)", or a theme recognised from its words (requirements, test article, target
match). The kind selects team-written cues from assets/criteria_profiles.json. A criterion of no
known kind gets a generic profile built from its own description, so any checklist works.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_TRL = re.compile(r"\bTRL\s*([1-9])\b", re.I)
_THEMES = [
    ("requirements", re.compile(r"\b(requirements?|acceptance criteria|specifications?)\b", re.I)),
    ("test_article", re.compile(r"\b(test conditions|test article|configuration|fidelity|breadboard)\b", re.I)),
    ("target_match", re.compile(r"\b(assessment target|assessed target|the target itself|parent project|different element)\b", re.I)),
]
_STOP = {
    "the", "a", "an", "of", "or", "and", "to", "in", "on", "for", "with", "that", "which", "by", "is",
    "are", "was", "were", "be", "it", "its", "this", "these", "those", "as", "at", "from", "report",
    "states", "state", "describes", "presents", "says", "whether", "their", "they", "not", "only",
    "itself", "assessed", "technology", "trl",
}


@dataclass
class Profile:
    criterion_id: str
    description: str
    kind: str
    level: int | None
    queries: list[str]
    positive: list[re.Pattern[str]]
    negative: list[re.Pattern[str]]
    roles: dict[str, float]
    keywords: list[str] = field(default_factory=list)
    hypotheses: list[str] = field(default_factory=list)
    require: list[re.Pattern[str]] = field(default_factory=list)
    threshold: float | None = None

    def hypotheses_for(self, target: str) -> list[str]:
        """NLI hypotheses with the target named; the description itself as a fallback."""
        target = " ".join(target.split())[:100] or "assessed technology"
        out = [h.replace("{target}", target) for h in self.hypotheses]
        if not out:
            out = [re.sub(r"\s*\([^)]*\)", "", self.description).split(":")[-1].strip() or self.description]
        return out


def description_keywords(description: str) -> list[str]:
    text = re.sub(r"\([^)]*\)", " ", description)  # drop "(TRL 4)" and examples
    words = re.findall(r"[a-z][a-z\-]{2,}", text.lower())
    out: list[str] = []
    for word in words:
        if word not in _STOP and word not in out:
            out.append(word)
    return out


def criterion_kind(description: str) -> tuple[str, int | None]:
    match = _TRL.search(description)
    if match:
        level = int(match.group(1))
        return f"trl{level}", level
    for kind, pattern in _THEMES:
        if pattern.search(description):
            return kind, None
    return "generic", None


def _compile(patterns: Sequence[str]) -> list[re.Pattern[str]]:
    compiled = []
    for pattern in patterns:
        try:
            compiled.append(re.compile(pattern, re.I))
        except re.error:
            continue
    return compiled


def load_assets(asset_root: Path) -> dict[str, Any]:
    try:
        return json.loads((Path(asset_root) / "criteria_profiles.json").read_text(encoding="utf-8"))
    except Exception:
        return {"kinds": {}}


def build_profiles(criteria: Sequence[Mapping[str, str]], assets: Mapping[str, Any]) -> list[Profile]:
    kinds = assets.get("kinds", {}) if isinstance(assets, Mapping) else {}
    generic = kinds.get("generic", {})
    profiles = []
    for criterion in criteria:
        description = str(criterion.get("description", ""))
        kind, level = criterion_kind(description)
        spec = kinds.get(kind) or generic
        queries = [description] + [q for q in spec.get("queries", []) if isinstance(q, str)]
        profiles.append(
            Profile(
                criterion_id=str(criterion["criterion_id"]),
                description=description,
                kind=kind,
                level=level,
                queries=queries,
                positive=_compile(spec.get("positive", [])),
                negative=_compile(spec.get("negative", [])),
                roles={str(k): float(v) for k, v in (spec.get("roles") or generic.get("roles") or {}).items()},
                keywords=description_keywords(description),
                hypotheses=[h for h in spec.get("hypotheses", []) if isinstance(h, str)],
                require=_compile(spec.get("require", [])),
                threshold=float(spec["threshold"]) if isinstance(spec.get("threshold"), (int, float)) else None,
            )
        )
    return profiles
