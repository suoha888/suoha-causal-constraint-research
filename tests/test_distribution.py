import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import shutil

ROOT = Path(__file__).resolve().parents[1]


class DistributionTests(unittest.TestCase):
    def run_script(self, name, *args):
        return subprocess.run([sys.executable, "-B", str(ROOT / "scripts" / name), *map(str, args)], capture_output=True, text=True, encoding="utf-8")

    def test_isolated_runtime_and_package(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            manifest = directory / "manifest.json"
            runtime = directory / "runtime"
            built = self.run_script("build_runtime.py", "--output", manifest, "--runtime-dir", runtime)
            self.assertEqual(built.returncode, 0, built.stderr)
            verified = self.run_script("verify_runtime.py", "--manifest", manifest)
            self.assertEqual(verified.returncode, 0, verified.stdout)
            smoke = subprocess.run([sys.executable, "-B", str(runtime / "scripts/validate_research_case.py"), str(runtime / "examples/synthetic-case-v1.1.json")], capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(smoke.returncode, 0, smoke.stdout + smoke.stderr)
            self.assertIn('"ok": true', smoke.stdout)
            installed_path = directory / "agent/skills/suoha-causal-constraint-research"
            installed = self.run_script("install_runtime.py", "--manifest", manifest, "--destination", installed_path)
            self.assertEqual(installed.returncode, 0, installed.stdout + installed.stderr)
            self.assertEqual((installed_path / "SKILL.md").read_bytes(), (runtime / "SKILL.md").read_bytes())
            repeated = self.run_script("install_runtime.py", "--manifest", manifest, "--destination", installed_path)
            self.assertEqual(repeated.returncode, 0, repeated.stdout + repeated.stderr)
            self.assertTrue(Path(json.loads(repeated.stdout)["backup"]).is_dir())
            (runtime / "SKILL.md").write_text("corrupted", encoding="utf-8")
            self.assertNotEqual(self.run_script("verify_runtime.py", "--manifest", manifest).returncode, 0)
            refused = self.run_script("install_runtime.py", "--manifest", manifest, "--destination", installed_path)
            self.assertNotEqual(refused.returncode, 0)
            self.assertNotEqual((installed_path / "SKILL.md").read_text(encoding="utf-8"), "corrupted")

    def test_empty_or_traversing_manifest_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            manifest = Path(temporary) / "manifest.json"
            for value in ({}, {"manifest_version":"2", "files":[], "file_count":0}, {"manifest_version":"2", "files":[{"path":"../secret"}], "file_count":1, "runtime_directory":"../outside"}):
                manifest.write_text(json.dumps(value), encoding="utf-8")
                self.assertNotEqual(self.run_script("verify_runtime.py", "--manifest", manifest).returncode, 0)

    def test_failed_eval_returns_nonzero_even_when_unit_tests_pass(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for folder in ("scripts", "schemas", "examples"):
                shutil.copytree(ROOT / folder, root / folder, ignore=shutil.ignore_patterns("__pycache__"))
            (root / "tests").mkdir()
            (root / "evals").mkdir()
            (root / "evals/bad.jsonl").write_text(json.dumps({"id":"bad-expectation", "fixture":"examples/synthetic-case-v1.1.json", "expected":"reject", "error_codes":["missing"]}) + "\n", encoding="utf-8")
            result = subprocess.run([sys.executable, "-B", str(root / "scripts/run_evals.py")], cwd=root, capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertFalse(json.loads(result.stdout)["ok"])
