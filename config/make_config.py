"""Write config/my.local.json: the kit server configuration that runs our module.

Paths in the generated file are resolved by the server against this directory. The model store
path is absolute because the worker runs in its own scratch directory (kit README step 6).

Usage (from the repository root):
    apctt-participant-kit-0.5.0-cpu/.venv/bin/python config/make_config.py [--deadline-ms N]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KIT = ROOT / "apctt-participant-kit-0.5.0-cpu"
OUT = ROOT / "config" / "my.local.json"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--deadline-ms", type=int, default=None, help="override limits.deadline_ms")
    parser.add_argument("--checklist", type=Path, default=None, help="checklist JSON (default: official)")
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()

    config = json.loads((KIT / "config" / "dev.json").read_text(encoding="utf-8"))
    config["data_dir"] = "../server_data"
    config["worker_tmp_dir"] = "../worker_tmp"
    checklist = args.checklist or KIT / "contracts" / "checklist.official.json"
    config["checklist_path"] = str(checklist.resolve())
    config["module"].update(
        package_id="trl-evidence-module",
        entrypoint="participant_module.adapter:AssessmentModule",
        module_root="../my_submission",
        package_root="../my_submission/participant_module",
        asset_root="../my_submission/assets",
        declared_package_sha256=None,
        example_only=False,
        settings={},
    )
    config["worker"]["python"] = "../apctt-env/base/bin/python"
    config["worker"]["extra_env"] = {"APCTT_MODEL_STORE": str((ROOT / "models").resolve())}
    if args.deadline_ms is not None:
        config["limits"]["deadline_ms"] = args.deadline_ms

    args.out.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
