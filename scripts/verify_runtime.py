#!/usr/bin/env python3
"""Verify the managed minimal runtime tree against its manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
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
    if not isinstance(manifest, dict) or manifest.get("manifest_version") != "2" or not isinstance(manifest.get("files"), list) or not manifest["files"] or manifest.get("file_count") != len(manifest["files"]):
        print(json.dumps({"ok": False, "error": "invalid or empty manifest"}))
        return 1
    directory = manifest.get("runtime_directory")
    if not isinstance(directory, str) or Path(directory).is_absolute() or ".." in Path(directory).parts:
        print(json.dumps({"ok": False, "error": "unsafe runtime directory"}))
        return 1
    runtime_dir = (manifest_path.parent / directory).resolve()
    if not runtime_dir.is_relative_to(manifest_path.parent) or runtime_dir == manifest_path.parent:
        print(json.dumps({"ok": False, "error": "runtime escapes manifest directory"}))
        return 1
    mismatches: list[dict[str, str]] = []
    expected: set[str] = set()
    for record in manifest.get("files", []):
        if not isinstance(record, dict):
            mismatches.append({"path": "?", "reason": "invalid record"})
            continue
        relative = record.get("path")
        if not isinstance(relative, str):
            mismatches.append({"path": "?", "reason": "manifest record has no path"})
            continue
        if Path(relative).is_absolute() or ".." in Path(relative).parts or relative in expected or not re.fullmatch(r"[0-9a-f]{64}", str(record.get("sha256", ""))):
            mismatches.append({"path": relative, "reason": "unsafe, duplicate or invalid record"})
            continue
        expected.add(relative)
        path = runtime_dir / relative
        if not path.resolve().is_relative_to(runtime_dir) or not path.is_file():
            mismatches.append({"path": relative, "reason": "missing from runtime"})
            continue
        current_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        if current_hash != record.get("sha256") or path.stat().st_size != record.get("bytes"):
            mismatches.append({"path": relative, "reason": "sha256 mismatch"})
    actual = {
        path.relative_to(runtime_dir).as_posix()
        for path in runtime_dir.rglob("*")
        if path.is_file()
    } if runtime_dir.exists() else set()
    for extra in sorted(actual - expected):
        mismatches.append({"path": extra, "reason": "unexpected runtime file"})
    if "SKILL.md" not in expected or "version.json" not in expected:
        mismatches.append({"path": "manifest", "reason": "missing entrypoint or version"})
    else:
        try:
            version = json.loads((runtime_dir / "version.json").read_text(encoding="utf-8"))
            if version.get("release") != manifest.get("release") or version.get("case_schema") != manifest.get("case_schema"):
                mismatches.append({"path": "version.json", "reason": "version mismatch"})
        except (OSError, ValueError):
            mismatches.append({"path": "version.json", "reason": "invalid version"})
    package = manifest_path.parent / "suoha-causal-constraint-research.skill"
    try:
        with zipfile.ZipFile(package) as archive:
            prefix = "suoha-causal-constraint-research/"
            if set(archive.namelist()) != {prefix + p for p in expected} or len(archive.namelist()) != len(expected):
                mismatches.append({"path": package.name, "reason": "package file set mismatch"})
            for record in manifest["files"]:
                if isinstance(record, dict) and prefix + str(record.get("path")) in archive.namelist():
                    if hashlib.sha256(archive.read(prefix + record["path"])).hexdigest() != record.get("sha256"):
                        mismatches.append({"path": record["path"], "reason": "package hash mismatch"})
    except (OSError, zipfile.BadZipFile):
        mismatches.append({"path": package.name, "reason": "missing or invalid package"})
    result = {
        "ok": not mismatches,
        "manifest": manifest_path.as_posix(),
        "checked": len(expected),
        "mismatches": mismatches,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
