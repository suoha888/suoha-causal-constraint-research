#!/usr/bin/env python3
"""Build a minimal runtime tree and a deterministic manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import os
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path


RUNTIME_ROOTS = (
    "SKILL.md",
    "ARCHITECTURE.md",
    "FUNCTIONAL_SPEC.md",
    "LICENSE",
    "README.md",
    "requirements.txt",
    "version.json",
    "NOTICE.md",
    "DATA_POLICY.md",
    "RESEARCH-PROVENANCE.md",
    "docs",
    "examples",
    "agents",
    "contracts",
    "kernel",
    "references",
    "schemas",
)
RUNTIME_SCRIPTS = {"validate_research_case.py", "gate_engine.py", "schema_validation.py", "semantic_integrity.py"}
EXCLUDED_PARTS = {".git", "__pycache__", ".venv", "private-research-corpus", "dist", "tests", "evals"}


def files_for(root: Path) -> list[Path]:
    result: list[Path] = []
    for entry in RUNTIME_ROOTS:
        path = root / entry
        if path.is_file():
            result.append(path)
            continue
        if not path.is_dir():
            continue
        for child in path.rglob("*"):
            if child.is_file() and not any(part in EXCLUDED_PARTS for part in child.relative_to(root).parts):
                result.append(child)
    scripts = root / "scripts"
    for name in sorted(RUNTIME_SCRIPTS):
        path = scripts / name
        if path.is_file():
            result.append(path)
    return sorted(set(result), key=lambda value: value.relative_to(root).as_posix())


def file_record(root: Path, path: Path) -> dict[str, object]:
    content = path.read_bytes()
    return {
        "path": path.relative_to(root).as_posix(),
        "bytes": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the minimal runtime tree")
    parser.add_argument("--root", default=None)
    parser.add_argument("--output", default=None)
    parser.add_argument("--runtime-dir", default=None)
    args = parser.parse_args()
    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parents[1]
    output = Path(args.output).resolve() if args.output else root / "dist" / "runtime-manifest.json"
    runtime_dir = Path(args.runtime_dir).resolve() if args.runtime_dir else root / "dist" / "runtime"
    records = [file_record(root, path) for path in files_for(root)]
    if runtime_dir == root or root.is_relative_to(runtime_dir) or runtime_dir.is_symlink() or not runtime_dir.is_relative_to(output.parent) or runtime_dir == output.parent:
        raise ValueError("runtime target must not replace source or an ancestor/symlink")
    runtime_dir.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix="runtime-stage-", dir=runtime_dir.parent))
    for record in records:
        source = root / str(record["path"])
        destination = staging / str(record["path"])
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
    # Keep old generated contents recoverable, including any unexpected files.
    backup = None
    if runtime_dir.exists():
        backup = runtime_dir.with_name(runtime_dir.name + "-backup-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f"))
        runtime_dir.rename(backup)
    try:
        staging.rename(runtime_dir)
    except OSError:
        if backup:
            backup.rename(runtime_dir)
        raise
    version = json.loads((root / "version.json").read_text(encoding="utf-8"))
    manifest = {
        "manifest_version": "2",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "runtime": "python-3.11-with-requirements",
        "release": version["release"],
        "case_schema": version["case_schema"],
        "entrypoint": "SKILL.md",
        "runtime_directory": Path(os.path.relpath(runtime_dir, output.parent)).as_posix(),
        "excluded": ["tests", "evals", "policy", "private research", "development-only scripts"],
        "files": records,
        "file_count": len(records),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    package = output.parent / "suoha-causal-constraint-research.skill"
    if package.exists():
        shutil.copy2(package, package.with_name(package.name + ".backup-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")))
    with zipfile.ZipFile(package, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for record in records:
            relative = str(record["path"])
            info = zipfile.ZipInfo("suoha-causal-constraint-research/" + relative, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, (runtime_dir / relative).read_bytes())
    print(json.dumps({"ok": True, "output": output.as_posix(), "runtime": runtime_dir.as_posix(), "package": package.as_posix(), "backup": str(backup) if backup else None, "file_count": len(records)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
