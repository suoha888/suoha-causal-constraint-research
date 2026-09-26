#!/usr/bin/env python3
"""Scan the repository public surface without storing forbidden terms in code.

The blocklist stores SHA-256 digests of normalized atoms. The scanner reports
locations and digests, never the matched text.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path
from urllib.parse import unquote, urlsplit


TEXT_SUFFIXES = {
    ".md",
    ".markdown",
    ".txt",
    ".py",
    ".json",
    ".jsonl",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".html",
    ".xml",
    ".csv",
    ".js",
    ".ts",
    ".sh",
    ".ps1",
}
URL_RE = re.compile(r"https?://[^\s<>()\"']+", re.IGNORECASE)
ATOM_RE = re.compile(r"[^\s,;:!?()[\]{}<>\"'|]+", re.UNICODE)
HASH_RE = re.compile(r"^[0-9a-f]{64}$")


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold()
    for _ in range(2):
        value = unquote(value)
    return value.strip().rstrip(".,;:!?")


def digest(value: str) -> str:
    return hashlib.sha256(normalize(value).encode("utf-8")).hexdigest()


def read_hashes(path: Path) -> set[str]:
    hashes: set[str] = set()
    if not path.exists():
        return hashes
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        value = line.strip().lower()
        if not value or value.startswith("#"):
            continue
        if not HASH_RE.match(value):
            raise ValueError(f"invalid digest at {path}:{line_number}")
        hashes.add(value)
    return hashes


def allowed_hosts(policy_path: Path) -> tuple[set[str], set[str], set[str]]:
    hosts: set[str] = set()
    schemes: set[str] = set()
    prefixes: set[str] = set()
    if not policy_path.exists():
        return hosts, schemes, prefixes
    section = None
    for raw in policy_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.endswith(":") and not line.startswith("-"):
            section = line[:-1]
            continue
        if line.startswith("- "):
            value = line[2:].strip().strip("\"'")
            if section == "allowed_hosts":
                hosts.add(value.casefold())
            elif section == "allowed_schemes":
                schemes.add(value.casefold())
            elif section == "allowed_url_prefixes":
                prefixes.add(value.rstrip("/").casefold())
    return hosts, schemes, prefixes


def iter_files(root: Path):
    ignored = {".git", "__pycache__", ".venv", "private-research-corpus", "dist"}
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in ignored for part in path.relative_to(root).parts):
            continue
        if path.suffix.casefold() in TEXT_SUFFIXES or path.name in {"LICENSE", "Makefile"}:
            yield path


def atom_candidates(text: str) -> set[str]:
    atoms: set[str] = set()
    for match in URL_RE.findall(text):
        cleaned = normalize(match)
        atoms.add(cleaned)
        parsed = urlsplit(cleaned)
        if parsed.hostname:
            atoms.add(parsed.hostname)
        if parsed.path:
            atoms.add(parsed.path)
    tokens = [normalize(token) for token in ATOM_RE.findall(text)]
    tokens = [token for token in tokens if token]
    for token in tokens:
        atoms.add(token)
    for width in range(2, 6):
        for start in range(0, max(0, len(tokens) - width + 1)):
            atoms.add(" ".join(tokens[start : start + width]))
    return atoms


def git_text(root: Path) -> list[tuple[str, str]]:
    records: list[tuple[str, str]] = []
    try:
        messages = subprocess.run(
            ["git", "-C", str(root), "log", "--all", "--format=%B%x00"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        ).stdout
    except OSError:
        return []
    if messages:
        records.append((".git/history-messages", messages))
    try:
        objects = subprocess.run(
            ["git", "-C", str(root), "rev-list", "--objects", "--all"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        ).stdout
    except OSError:
        return records
    for line in objects.splitlines():
        object_id, _, object_path = line.partition(" ")
        if not object_id:
            continue
        kind = subprocess.run(
            ["git", "-C", str(root), "cat-file", "-t", object_id],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        ).stdout.strip()
        if kind != "blob":
            continue
        raw = subprocess.run(
            ["git", "-C", str(root), "cat-file", "-p", object_id],
            check=False,
            capture_output=True,
        ).stdout
        if len(raw) > 2_000_000:
            continue
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            continue
        records.append((f".git/blob/{object_id}/{object_path or 'unknown'}", text))
    return records


def scan(root: Path, blocked: set[str], policy: Path) -> dict[str, object]:
    violations: list[dict[str, object]] = []
    hosts, schemes, prefixes = allowed_hosts(policy)
    for path in iter_files(root):
        relative = str(path.relative_to(root)).replace("\\", "/")
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for candidate in atom_candidates(relative + "\n" + text):
            candidate_hash = digest(candidate)
            if candidate_hash in blocked:
                violations.append({"type": "blocked_digest", "path": relative, "digest": candidate_hash})
                break
        for url in URL_RE.findall(text):
            cleaned = url.rstrip(".,;:!?")
            parsed = urlsplit(cleaned)
            host = (parsed.hostname or "").casefold().rstrip(".")
            scheme = parsed.scheme.casefold()
            prefix_hosts = {urlsplit(prefix).hostname for prefix in prefixes}
            prefix_match = any(cleaned.casefold().startswith(prefix) for prefix in prefixes)
            allowed_by_host = scheme in schemes and (host in hosts or host in prefix_hosts)
            if host in prefix_hosts:
                allowed_by_host = allowed_by_host and prefix_match
            if not allowed_by_host:
                violations.append(
                    {
                        "type": "disallowed_link",
                        "path": relative,
                        "scheme": scheme,
                        "host": host,
                    }
                )
    for label, text in git_text(root):
        for candidate in atom_candidates(text):
            candidate_hash = digest(candidate)
            if candidate_hash in blocked:
                violations.append({"type": "blocked_digest", "path": label, "digest": candidate_hash})
                break
    return {
        "ok": not violations,
        "files_scanned": sum(1 for _ in iter_files(root)),
        "violations": violations,
        "blocked_digest_count": len(blocked),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan the public repository surface")
    parser.add_argument("--root", default=None, help="repository root; defaults to the project root")
    parser.add_argument("--blocked-digests", default=None)
    parser.add_argument("--policy", default=None)
    args = parser.parse_args()
    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parents[1]
    blocked_path = Path(args.blocked_digests).resolve() if args.blocked_digests else root / "policy" / "blocked-digests.txt"
    policy_path = Path(args.policy).resolve() if args.policy else root / "policy" / "external-link-policy.yaml"
    try:
        blocked = read_hashes(blocked_path)
        result = scan(root, blocked, policy_path)
    except (OSError, ValueError) as exc:
        result = {"ok": False, "files_scanned": 0, "violations": [{"type": "scanner_error", "message": str(exc)}]}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
