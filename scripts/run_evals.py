#!/usr/bin/env python3
"""Run the repository's unittest-based evaluation suite."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Run research skill evaluations")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    command = [sys.executable, "-m", "unittest", "discover", "-s", "tests"]
    if args.verbose:
        command.append("-v")
    completed = subprocess.run(command, cwd=root, check=False)
    result = {"ok": completed.returncode == 0, "command": command}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
