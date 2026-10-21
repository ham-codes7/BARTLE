"""Entry point: participant_module.adapter:AssessmentModule (apctt-worker-v2).

The server creates the class with no arguments and calls load -> assess -> reset_case -> close in a
fresh process for every case. Whatever happens inside the assessment, `assess` returns a result
that satisfies the result contract: internal errors fall back to a prior-only `completed` result,
and every result passes through `result.finalize` before it is returned.
"""

from __future__ import annotations

import sys
import traceback
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from participant_module import pipeline
from participant_module import result as contract
from participant_module.criteria import Profile, build_profiles, load_assets
from participant_module.decide import load_trl_model
from participant_module.models import Models
from participant_module.safety import Budget, fallback_result, load_prior


class AssessmentModule:
    def __init__(self) -> None:
        self._checklist_version = ""
        self._criteria: list[dict[str, str]] = []
        self._criterion_ids: list[str] = []
        self._settings: dict[str, Any] = {}
        self._asset_root = Path(".")
        self._prior: dict[str, Any] | None = None
        self._profiles: list[Profile] = []
        self._models: Models | None = None
        self._trl_model: dict[str, Any] | None = None
        self._seed = 42

    def load(self, config: Mapping[str, Any], asset_root: Path) -> None:
        checklist = config["checklist"]
        self._checklist_version = str(checklist["version"])
        self._criteria = [
            {"criterion_id": str(c["criterion_id"]), "description": str(c.get("description", ""))}
            for c in checklist["criteria"]
        ]
        self._criterion_ids = [c["criterion_id"] for c in self._criteria]
        module = config.get("module") or {}
        settings = module.get("settings") if isinstance(module, Mapping) else None
        self._settings = dict(settings) if isinstance(settings, Mapping) else {}
        self._asset_root = Path(asset_root)
        compute = config.get("compute") or {}
        seed = compute.get("seed") if isinstance(compute, Mapping) else None
        self._seed = seed if isinstance(seed, int) else 42
        self._prior = load_prior(self._asset_root)
        self._profiles = build_profiles(self._criteria, load_assets(self._asset_root))
        self._models = Models(self._asset_root, threads=4, seed=self._seed)
        self._trl_model = load_trl_model(self._asset_root)

    def assess(self, case: Mapping[str, Any], context: Any) -> dict[str, Any]:
        budget = Budget(context)
        try:
            raw = self._assess(case, budget, context)
        except Exception:
            traceback.print_exc(file=sys.stderr)
            raw = fallback_result(
                case, self._criterion_ids, self._checklist_version, self._prior,
                "the automatic assessment stopped with an internal error",
            )
        return contract.finalize(raw, case, self._criterion_ids, self._checklist_version)

    def _assess(self, case: Mapping[str, Any], budget: Budget, context: Any) -> dict[str, Any]:
        return pipeline.run(
            case, self._profiles, self._checklist_version, self._prior, self._settings, budget,
            self._models, self._trl_model,
        )

    def reset_case(self) -> None:
        """Nothing is kept between cases; each case runs in a new process."""

    def close(self) -> None:
        """No files or devices are held open."""
