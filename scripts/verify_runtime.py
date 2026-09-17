#!/usr/bin/env python3
"""Verify a previously built runtime manifest against the current files."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify a runtime manifest")
    parser.add_argument("--root", default=None)
    parser.add_argument("--manifest", default=None)
    args = parser.parse_args()
    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parents[1]
    manifest_path = Path(args.manifest).resolve() if args.manifest else root / "dist" / "runtime-manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        return 2
    mismatches: list[dict[str, str]] = []
    for record in manifest.get("files", []):
        relative = record.get("path")
        if not isinstance(relative, str):
            mismatches.append({"path": "?", "reason": "manifest record has no path"})
            continue
        path = root / relative
        if not path.exists():
            mismatches.append({"path": relative, "reason": "missing"})
            continue
        current_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        if current_hash != record.get("sha256"):
            mismatches.append({"path": relative, "reason": "sha256 mismatch"})
    result = {
        "ok": not mismatches,
        "manifest": manifest_path.as_posix(),
        "checked": len(manifest.get("files", [])),
        "mismatches": mismatches,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
