"""Install a verified runtime, preserving the previous installation for rollback."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--destination", required=True)
    args = parser.parse_args()
    manifest_path = Path(args.manifest).resolve()
    check = subprocess.run([sys.executable, "-B", str(Path(__file__).with_name("verify_runtime.py")), "--manifest", str(manifest_path)], capture_output=True, text=True)
    if check.returncode:
        print(check.stdout)
        return check.returncode
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    source = (manifest_path.parent / manifest["runtime_directory"]).resolve()
    requested = Path(args.destination)
    destination = requested.resolve()
    repository = Path(__file__).resolve().parents[1]
    if requested.is_symlink() or destination.name != "suoha-causal-constraint-research" or repository.is_relative_to(destination) or destination.is_relative_to(repository) or destination == source:
        raise ValueError("Destination must be a separate skill directory, never source or an ancestor")
    destination.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".skill-stage-", dir=destination.parent))
    shutil.copytree(source, stage, dirs_exist_ok=True)
    backup = None
    if destination.exists():
        backup_root = destination.parent.parent / "skill-backups"
        backup_root.mkdir(parents=True, exist_ok=True)
        backup = backup_root / (destination.name + "-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f"))
        destination.rename(backup)
    try:
        stage.rename(destination)
    except OSError:
        if backup:
            backup.rename(destination)
        raise
    print(json.dumps({"ok":True, "release":manifest["release"], "destination":str(destination), "backup":str(backup) if backup else None}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
