#!/usr/bin/env bash
# Reproduce the local development setup (kit server env, common base env, model store, PDFs).
# Run from the repository root. Needs network access once; the evaluation itself is offline.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
KIT="$ROOT/apctt-participant-kit-0.5.0-cpu"
MODELS=(all-minilm-l6-v2 ms-marco-minilm-l6-v2 deberta-v3-base-zeroshot-v2.0-c)

cd "$KIT"
shasum -a 256 -c MANIFEST.sha256 --quiet && echo "kit OK"
uv python find 3.12 >/dev/null || uv python install 3.12

# 1. Kit server environment (runs the server, tests and tools; not our module).
[ -x .venv/bin/python ] || uv venv --python 3.12 .venv
uv pip install -q --python .venv/bin/python -r requirements-dev.lock
uv pip install -q --python .venv/bin/python --no-deps -e .

# 2. Common base environment (runs our module, same packages as the event machines).
.venv/bin/python tools/make_env.py --base-dir "$ROOT/apctt-env/base"

# 3. Catalogue models into a local store with the organizer's layout.
.venv/bin/python tools/get_models.py "${MODELS[@]}" --store "$ROOT/models"

# 4. Public sample case PDFs (pass --all to fetch all 99, about 1.1 GB).
.venv/bin/python tools/get_public_cases.py "${1:---smoke}" --download --dir "$ROOT/data/pdfs"

# 5. Server configuration for our module.
.venv/bin/python "$ROOT/config/make_config.py"
