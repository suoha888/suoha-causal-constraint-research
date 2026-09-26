#!/usr/bin/env python3
"""Run the repository's unittest-based evaluation suite."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_research_case import validate_case


def evaluate_record(root, record):
    if record.get("expected") not in {"accept", "reject"} or not record.get("fixture"):
        raise ValueError("eval must declare fixture and expected accept/reject")
    path = (root / record["fixture"]).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError("fixture outside repository")
    case = json.loads(path.read_text(encoding="utf-8"))
    for change in record.get("mutations", []):
        if change.get("op") not in {"set", "remove"} or not isinstance(change.get("path"), list) or not change["path"]:
            raise ValueError("mutation requires set/remove and nonempty path array")
        parent = case
        for key in change["path"][:-1]:
            parent = parent[key]
        key = change["path"][-1]
        if change["op"] == "set":
            parent[key] = change["value"]
        else:
            del parent[key]
    result = validate_case(case)
    if result["ok"] != (record["expected"] == "accept"):
        raise ValueError(f"expected {record['expected']}, got ok={result['ok']}")
    if record["expected"] == "reject":
        expected_codes = record.get("error_codes")
        if not expected_codes or not set(expected_codes) <= {e["code"] for e in result["errors"]}:
            raise ValueError("reject must match all declared error_codes")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Run research skill evaluations")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    command = [sys.executable, "-m", "unittest", "discover", "-s", "tests"]
    if args.verbose:
        command.append("-v")
    completed = subprocess.run(command, cwd=root, check=False)
    eval_cases = 0
    eval_files = 0
    eval_errors: list[dict[str, str]] = []
    for path in sorted((root / "evals").rglob("*.jsonl")):
        eval_files += 1
        for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not raw.strip():
                continue
            try:
                record = json.loads(raw)
            except json.JSONDecodeError as exc:
                eval_errors.append({"path": str(path.relative_to(root)), "line": str(line_number), "error": str(exc)})
                continue
            if not isinstance(record, dict) or not isinstance(record.get("id"), str) or not record.get("id"):
                eval_errors.append({"path": str(path.relative_to(root)), "line": str(line_number), "error": "each eval record needs a stable id"})
                continue
            try:
                evaluate_record(root, record)
                eval_cases += 1
            except (OSError, ValueError, KeyError, IndexError, TypeError) as exc:
                eval_errors.append({"path": str(path.relative_to(root)), "line": str(line_number), "error": str(exc)})
    result = {
        "ok": completed.returncode == 0 and not eval_errors,
        "command": command,
        "eval_files": eval_files,
        "eval_cases": eval_cases,
        "eval_errors": eval_errors,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
