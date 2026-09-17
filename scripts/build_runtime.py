#!/usr/bin/env python3
"""Build a deterministic manifest for the public skill runtime."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


INCLUDED_SUFFIXES = {".md", ".json", ".yaml", ".yml", ".py", ".txt", ".gitignore"}
EXCLUDED_PARTS = {".git", "__pycache__", ".venv", "private-research-corpus", "dist"}


def files_for(root: Path) -> list[Path]:
    result = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if any(part in EXCLUDED_PARTS for part in relative.parts):
            continue
        if path.suffix.casefold() in INCLUDED_SUFFIXES or path.name == "LICENSE":
            result.append(path)
    return sorted(result, key=lambda value: value.relative_to(root).as_posix())


def file_record(root: Path, path: Path) -> dict[str, object]:
    content = path.read_bytes()
    return {
        "path": path.relative_to(root).as_posix(),
        "bytes": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a runtime manifest")
    parser.add_argument("--root", default=None)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()
    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parents[1]
    output = Path(args.output).resolve() if args.output else root / "dist" / "runtime-manifest.json"
    records = [file_record(root, path) for path in files_for(root)]
    manifest = {
        "manifest_version": "1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "runtime": "python-standard-library",
        "entrypoint": "SKILL.md",
        "files": records,
        "file_count": len(records),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "output": output.as_posix(), "file_count": len(records)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
