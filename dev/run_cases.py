"""Run the module directly on public cases, validate every result and record timings.

Each case runs in its own process (like the server's cold worker) with at most --threads CPU
threads, to approximate the 4-core event machine. Results go to dev/out/<run>/<case_id>.json and a
summary to dev/out/<run>/summary.json.

Usage (base environment's Python):
    apctt-env/base/bin/python dev/run_cases.py --smoke
    apctt-env/base/bin/python dev/run_cases.py --all --jobs 2 --run baseline
    apctt-env/base/bin/python dev/run_cases.py 12 40 61
"""

from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import os
import resource
import sys
import tempfile
import time
import traceback
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

DEADLINE_MS = 180_000.0


def run_one(args: tuple[str, str, int, float, dict]) -> dict:
    case_id, out_dir, threads, deadline_ms, settings = args
    for var in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
        os.environ[var] = str(threads)
    started = time.monotonic()
    record: dict = {"case_id": case_id}
    try:
        with tempfile.TemporaryDirectory() as scratch:
            scratch_path = Path(scratch)
            case = harness.worker_case(case_id, scratch_path)
            t0 = time.monotonic()
            from participant_module.adapter import AssessmentModule

            module = AssessmentModule()
            module.load(harness.module_config(settings=settings), harness.SUBMISSION / "assets")
            t1 = time.monotonic()
            context = SimpleNamespace(
                run_id="local",
                seed=42,
                time_budget_ms=int(deadline_ms),
                scratch_dir=scratch_path,
                remaining_ms=lambda: deadline_ms - (time.monotonic() - t0) * 1000.0,
            )
            result = module.assess(case, context)
            t2 = time.monotonic()
            module.reset_case()
            module.close()
            issues = harness.validate(result, case)
        Path(out_dir, f"{case_id}.json").write_text(json.dumps(result, indent=2) + "\n")
        from participant_module import pipeline

        Path(out_dir, f"{case_id}.debug.json").write_text(json.dumps(pipeline.LAST, indent=2) + "\n")
        record.update(
            status=result.get("assessment_status"),
            predicted_trl=result.get("predicted_trl"),
            reference_trl=harness.reference_trl(case_id),
            issues=issues,
            load_s=round(t1 - t0, 2),
            assess_s=round(t2 - t1, 2),
            total_s=round(time.monotonic() - started, 2),
            peak_rss_mb=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 2**20, 1),
        )
    except Exception as error:  # the harness itself failed, not the module contract
        record.update(status="harness_error", error=repr(error), trace=traceback.format_exc())
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("ids", nargs="*")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--jobs", type=int, default=1, help="cases run in parallel")
    parser.add_argument("--threads", type=int, default=4, help="CPU threads per case")
    parser.add_argument("--run", default=time.strftime("run-%Y%m%d-%H%M%S"))
    parser.add_argument("--deadline-ms", type=float, default=DEADLINE_MS)
    parser.add_argument("--set", action="append", default=[], metavar="KEY=JSON",
                        help="module setting, e.g. --set nli_k=12")
    args = parser.parse_args()

    case_ids = harness.select_cases(args.ids, args.smoke, args.all)
    if not case_ids:
        parser.error("give case IDs, --smoke or --all")
    out_dir = harness.ROOT / "dev" / "out" / args.run
    out_dir.mkdir(parents=True, exist_ok=True)
    settings = {k: json.loads(v) for k, v in (item.split("=", 1) for item in args.set)}
    jobs = [(cid, str(out_dir), args.threads, args.deadline_ms, settings) for cid in case_ids]
    ctx = mp.get_context("spawn")
    records = []
    with ctx.Pool(processes=max(1, args.jobs), maxtasksperchild=1) as pool:
        for record in pool.imap(run_one, jobs):
            records.append(record)
            issues = record.get("issues")
            print(
                f"{record['case_id']}: {record.get('status')} trl={record.get('predicted_trl')} "
                f"ref={record.get('reference_trl')} issues={len(issues) if issues is not None else '-'} "
                f"total={record.get('total_s')}s rss={record.get('peak_rss_mb')}MB"
                + (f" ERROR {record.get('error')}" if record.get("error") else ""),
                flush=True,
            )
    summary = {
        "run": args.run,
        "cases": len(records),
        "invalid": sum(1 for r in records if r.get("issues")),
        "harness_errors": sum(1 for r in records if r.get("status") == "harness_error"),
        "max_total_s": max((r.get("total_s", 0) for r in records), default=0),
        "records": records,
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(
        f"\n{summary['cases']} cases, {summary['invalid']} invalid, {summary['harness_errors']} harness errors, "
        f"max {summary['max_total_s']}s -> {out_dir}"
    )


if __name__ == "__main__":
    main()
