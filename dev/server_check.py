"""Send request files to the local kit server and report what the organizer's server would record.

Start the server first (from the repository root):
    apctt-participant-kit-0.5.0-cpu/.venv/bin/python -m apctt_server --profile dev --config config/my.local.json
Then:
    python3 dev/server_check.py data/requests/*.json
"""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE = "http://127.0.0.1:8000"


def call(method: str, path: str, body: dict | None = None) -> tuple[int, dict]:
    data = None if body is None else json.dumps(body).encode("utf-8")
    request = urllib.request.Request(BASE + path, data=data, method=method)
    request.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read())


def run(path: Path) -> bool:
    body = json.loads(path.read_text(encoding="utf-8"))
    body["request_id"] = f"dev-{time.strftime('%Y%m%d-%H%M%S')}-{time.time_ns() % 1_000_000}"
    status, job = call("POST", "/v1/assessments", body)
    if status not in (200, 201, 202):
        print(f"{path.name}: POST {status} {json.dumps(job)[:300]}")
        return False
    assessment_id = job.get("assessment_id")
    while job.get("job_status") not in ("finished", "failed", "cancelled"):
        time.sleep(1)
        status, job = call("GET", f"/v1/assessments/{assessment_id}")
    result = job.get("result") or {}
    diagnostics = job.get("diagnostics") or {}
    ok = job.get("result_origin") == "module" and result.get("assessment_status") != "failed"
    print(
        f"{path.name}: job={job.get('job_status')} origin={job.get('result_origin')} "
        f"status={result.get('assessment_status')} trl={result.get('predicted_trl')} "
        f"timings={diagnostics.get('timings_ms')} issues={diagnostics.get('output_issues')} "
        f"warnings={diagnostics.get('warning_codes')}"
    )
    return ok


def main() -> int:
    status, ready = call("GET", "/health/ready")
    print("ready:", ready.get("reason_code"))
    status, package = call("GET", "/v1/package")
    print("package:", package.get("package_id"), package.get("verification_status"),
          package.get("verified_package_sha256"))
    results = [run(Path(p)) for p in sys.argv[1:]]
    print(f"{sum(results)}/{len(results)} returned a module result")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
