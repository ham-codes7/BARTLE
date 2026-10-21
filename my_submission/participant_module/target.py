"""The assessment target and its context, as given in the case.

A TRL is always relative to the target and to its intended application and environment
(PROBLEM_DESCRIPTION §3). This module turns those case fields into term sets used to:
  - steer retrieval towards sentences about the target itself, and
  - score how much a sentence concerns the target (the target-match criterion).
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

_STOP = {
    "the", "a", "an", "of", "and", "or", "for", "in", "on", "at", "to", "by", "with", "from", "into",
    "selected", "use", "used", "using", "based", "new", "other", "its", "their", "this", "that",
    "usa", "u.s", "united", "states", "county", "river", "creek", "sdg", "target", "targets",
    "management", "integrated", "sustainable", "water", "resource", "resources", "model", "models",
    "study", "studies", "area", "areas", "data", "report", "analysis", "analyses",
}
_ACRONYM = re.compile(r"\b[A-Z][A-Za-z0-9]*[A-Z0-9](?:[–\-/][A-Z0-9]+)*\b")


def tokens(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9][a-z0-9\-]*", text.lower()) if len(t) > 2]


@dataclass
class TargetProfile:
    description: str
    target_type: str
    application: str
    environment: str
    title: str
    target_terms: set[str] = field(default_factory=set)  # distinctive words of the target
    acronyms: set[str] = field(default_factory=set)  # e.g. HEC-RAS, PRMS
    environment_terms: set[str] = field(default_factory=set)
    application_terms: set[str] = field(default_factory=set)

    def overlap(self, sentence: str) -> float:
        """0..1: how strongly a sentence names the target (acronyms count double)."""
        words = set(tokens(sentence))
        if not self.target_terms and not self.acronyms:
            return 0.0
        hits = len(words & self.target_terms)
        acr = sum(1 for a in self.acronyms if a in sentence)
        denominator = max(1, min(4, len(self.target_terms)))
        return min(1.0, (hits + 2 * acr) / denominator)

    def environment_overlap(self, sentence: str) -> float:
        if not self.environment_terms:
            return 0.0
        words = set(tokens(sentence))
        return min(1.0, len(words & self.environment_terms) / max(1, min(3, len(self.environment_terms))))


def _distinctive(text: str) -> set[str]:
    return {t for t in tokens(text) if t not in _STOP and not t.isdigit()}


def build_target(case: Mapping[str, Any]) -> TargetProfile:
    target = case.get("assessment_target") or {}
    description = str(target.get("description") or "") if isinstance(target, Mapping) else ""
    profile = TargetProfile(
        description=description,
        target_type=str(target.get("type") or "") if isinstance(target, Mapping) else "",
        application=str(case.get("intended_application") or ""),
        environment=str(case.get("intended_environment") or ""),
        title=str(case.get("title") or ""),
    )
    profile.target_terms = _distinctive(description)
    profile.acronyms = {a for a in _ACRONYM.findall(description) if len(a) >= 3 and a not in {"USA", "SDG"}}
    profile.environment_terms = _distinctive(profile.environment)
    profile.application_terms = _distinctive(re.sub(r"\(SDG target \d+\)", "", profile.application))
    return profile
