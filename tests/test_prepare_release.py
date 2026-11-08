"""Test release preparation through its CLI with real Git repositories."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "prepare_release.py"
GIT = shutil.which("git") or "git"
NAME = "clod-soul"


class ReleaseTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
        self.environment.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")
        self.environment["GITHUB_OUTPUT"] = str(self.root / "output")
        self.git("init", "--quiet", "-b", "main")
        self.git("config", "user.name", "Test")
        self.git("config", "user.email", "test@example.com")
        (self.root / ".gitignore").write_text("output\n", encoding="utf-8")
        self.write_versions("1.2.3")

    def git(self, *args: str) -> str:
        result = subprocess.run(  # noqa: S603 -- fixed Git executable and fixture-controlled arguments.
            [GIT, *args], cwd=self.root, env=self.environment,
            check=True, capture_output=True, text=True,
        )
        return result.stdout.strip()

    def commit(self, message: str) -> str:
        self.git("add", ".")
        self.git("commit", "--quiet", "--no-verify", "--allow-empty", "-m", message)
        return self.git("rev-parse", "HEAD")

    def write_versions(self, version: str) -> None:
        for name in (".claude-plugin/plugin.json", ".codex-plugin/plugin.json", ".claude-plugin/marketplace.json"):
            path = self.root / name
            path.parent.mkdir(exist_ok=True)
            value = (
                {"plugins": [{"name": "other", "version": "9.0.0"}, {"name": NAME, "version": version}]}
                if "marketplace" in name else {"name": NAME, "version": version, "description": "Keep this"}
            )
            path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

    def run_release(self, source: str, previous: str) -> subprocess.CompletedProcess[str]:
        (self.root / "output").unlink(missing_ok=True)
        return subprocess.run(  # noqa: S603 -- repository CLI and fixture-controlled arguments.
            [sys.executable, str(SCRIPT), "--source", source, "--previous", previous],
            cwd=self.root, env=self.environment, capture_output=True, text=True, check=False,
        )

    def assert_versions(self, expected: str) -> None:
        for name in (".claude-plugin/plugin.json", ".codex-plugin/plugin.json"):
            value = json.loads((self.root / name).read_text(encoding="utf-8"))
            self.assertEqual(value, {"name": NAME, "version": expected, "description": "Keep this"})
        value = json.loads((self.root / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
        self.assertEqual(value["plugins"], [{"name": "other", "version": "9.0.0"}, {"name": NAME, "version": expected}])

    def test_patch_bump_synchronizes_versions(self) -> None:
        previous = self.commit("base")
        source = self.commit("feature")
        result = self.run_release(source, previous)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_versions("1.2.4")
        self.assertEqual((self.root / "output").read_text(), "state=new\nversion=1.2.4\n")

    def test_manual_bump_in_earlier_push_commit_is_preserved(self) -> None:
        previous = self.commit("base")
        path = self.root / ".claude-plugin/plugin.json"
        path.write_text(path.read_text().replace('"1.2.3"', '"1.3.0"'))
        self.commit("manual release")
        source = self.commit("another commit in same push")
        result = self.run_release(source, previous)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_versions("1.3.0")

    def test_retry_reuses_release_commit(self) -> None:
        previous = self.commit("base")
        source = self.commit("feature")
        self.assertEqual(self.run_release(source, previous).returncode, 0)
        self.commit(f"Release 1.2.4\n\nSource-Commit: {source}")
        result = self.run_release(source, previous)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_versions("1.2.4")
        self.assertEqual((self.root / "output").read_text(), "state=retry\nversion=1.2.4\n")
        self.assertEqual(self.git("status", "--porcelain"), "")

    def test_superseded_push_does_not_change_files(self) -> None:
        previous = self.commit("base")
        source = self.commit("feature")
        self.commit("superseding push")
        result = self.run_release(source, previous)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.root / "output").read_text(), "state=stale\nversion=1.2.3\n")
        self.assertEqual(self.git("status", "--porcelain"), "")

    def test_decreased_or_invalid_version_is_rejected(self) -> None:
        for version in ("1.1.0", "invalid", "1.3.0rc1"):
            with self.subTest(version=version):
                self.write_versions("1.2.3")
                previous = self.commit("base")
                self.write_versions(version)
                source = self.commit("bad release")
                result = self.run_release(source, previous)
                self.assertNotEqual(result.returncode, 0)
                self.assertTrue("version decreased" in result.stderr or "major.minor.patch" in result.stderr, result.stderr)
                self.assertEqual(self.git("status", "--porcelain"), "")

    def test_invalid_revisions_are_rejected(self) -> None:
        source = self.commit("base")
        for source_arg, previous_arg in (("HEAD", source), (source, "HEAD")):
            with self.subTest(source=source_arg, previous=previous_arg):
                result = self.run_release(source_arg, previous_arg)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("full Git commit SHA", result.stderr)

    def test_invalid_metadata_fails_before_writing(self) -> None:
        for name, content, error in (
            (".codex-plugin/plugin.json", "[]", "must contain a JSON object"),
            (".claude-plugin/marketplace.json", '{"plugins": {}}', "must contain a plugins array"),
            (".claude-plugin/marketplace.json", '{"plugins": []}', "must register"),
        ):
            with self.subTest(name=name, content=content):
                self.write_versions("1.2.3")
                previous = self.commit("base")
                (self.root / name).write_text(content, encoding="utf-8")
                source = self.commit("invalid metadata")
                result = self.run_release(source, previous)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(error, result.stderr)
                self.assertEqual(self.git("status", "--porcelain"), "")

    def test_manifest_identity_fails_before_writing(self) -> None:
        for manifest in (".claude-plugin/plugin.json", ".codex-plugin/plugin.json", ".claude-plugin/marketplace.json"):
            with self.subTest(manifest=manifest):
                self.write_versions("1.2.3")
                previous = self.commit("base")
                path = self.root / manifest
                value = json.loads(path.read_text())
                if "marketplace" in manifest:
                    value["plugins"].append({"name": NAME, "version": "1.2.3"})
                else:
                    value["name"] = "wrong-plugin"
                path.write_text(json.dumps(value))
                source = self.commit("invalid identity")
                result = self.run_release(source, previous)
                assert result.returncode != 0
                assert NAME in result.stderr
                assert self.git("status", "--porcelain") == ""
